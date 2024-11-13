#!/usr/bin/env python3
import bisect
import math
import os
from enum import IntEnum
from collections.abc import Callable

from cereal import log, car
import cereal.messaging as messaging
from openpilot.common.conversions import Conversions as CV
from openpilot.common.git import get_short_branch
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.locationd.calibrationd import MIN_SPEED_FILTER

AlertSize = log.ControlsState.AlertSize
AlertStatus = log.ControlsState.AlertStatus
VisualAlert = car.CarControl.HUDControl.VisualAlert
AudibleAlert = car.CarControl.HUDControl.AudibleAlert
EventName = car.CarEvent.EventName


# Alert priorities
class Priority(IntEnum):
  LOWEST = 0
  LOWER = 1
  LOW = 2
  MID = 3
  HIGH = 4
  HIGHEST = 5


# Event types
class ET:
  ENABLE = 'enable'
  PRE_ENABLE = 'preEnable'
  OVERRIDE_LATERAL = 'overrideLateral'
  OVERRIDE_LONGITUDINAL = 'overrideLongitudinal'
  NO_ENTRY = 'noEntry'
  WARNING = 'warning'
  USER_DISABLE = 'userDisable'
  SOFT_DISABLE = 'softDisable'
  IMMEDIATE_DISABLE = 'immediateDisable'
  PERMANENT = 'permanent'


# get event name from enum
EVENT_NAME = {v: k for k, v in EventName.schema.enumerants.items()}


class Events:
  def __init__(self):
    self.events: list[int] = []
    self.static_events: list[int] = []
    self.event_counters = dict.fromkeys(EVENTS.keys(), 0)

  @property
  def names(self) -> list[int]:
    return self.events

  def __len__(self) -> int:
    return len(self.events)

  def add(self, event_name: int, static: bool=False) -> None:
    if static:
      bisect.insort(self.static_events, event_name)
    bisect.insort(self.events, event_name)

  def clear(self) -> None:
    self.event_counters = {k: (v + 1 if k in self.events else 0) for k, v in self.event_counters.items()}
    self.events = self.static_events.copy()

  def contains(self, event_type: str) -> bool:
    return any(event_type in EVENTS.get(e, {}) for e in self.events)

  def create_alerts(self, event_types: list[str], callback_args=None):
    if callback_args is None:
      callback_args = []

    ret = []
    for e in self.events:
      types = EVENTS[e].keys()
      for et in event_types:
        if et in types:
          alert = EVENTS[e][et]
          if not isinstance(alert, Alert):
            alert = alert(*callback_args)

          if DT_CTRL * (self.event_counters[e] + 1) >= alert.creation_delay:
            alert.alert_type = f"{EVENT_NAME[e]}/{et}"
            alert.event_type = et
            ret.append(alert)
    return ret

  def add_from_msg(self, events):
    for e in events:
      bisect.insort(self.events, e.name.raw)

  def to_msg(self):
    ret = []
    for event_name in self.events:
      event = car.CarEvent.new_message()
      event.name = event_name
      for event_type in EVENTS.get(event_name, {}):
        setattr(event, event_type, True)
      ret.append(event)
    return ret


class Alert:
  def __init__(self,
               alert_text_1: str,
               alert_text_2: str,
               alert_status: log.ControlsState.AlertStatus,
               alert_size: log.ControlsState.AlertSize,
               priority: Priority,
               visual_alert: car.CarControl.HUDControl.VisualAlert,
               audible_alert: car.CarControl.HUDControl.AudibleAlert,
               duration: float,
               alert_rate: float = 0.,
               creation_delay: float = 0.):

    self.alert_text_1 = alert_text_1
    self.alert_text_2 = alert_text_2
    self.alert_status = alert_status
    self.alert_size = alert_size
    self.priority = priority
    self.visual_alert = visual_alert
    self.audible_alert = audible_alert

    self.duration = int(duration / DT_CTRL)

    self.alert_rate = alert_rate
    self.creation_delay = creation_delay

    self.alert_type = ""
    self.event_type: str | None = None

  def __str__(self) -> str:
    return f"{self.alert_text_1}/{self.alert_text_2} {self.priority} {self.visual_alert} {self.audible_alert}"

  def __gt__(self, alert2) -> bool:
    if not isinstance(alert2, Alert):
      return False
    return self.priority > alert2.priority


class NoEntryAlert(Alert):
  def __init__(self, alert_text_2: str,
               alert_text_1: str = "القائد الآلي غير متاح",
               visual_alert: car.CarControl.HUDControl.VisualAlert=VisualAlert.none):
    super().__init__(alert_text_1, alert_text_2, AlertStatus.normal,
                     AlertSize.mid, Priority.LOW, visual_alert,
                     AudibleAlert.refuse, 3.)


class SoftDisableAlert(Alert):
  def __init__(self, alert_text_2: str):
    super().__init__("تولي التحكم فوراً", alert_text_2,
                     AlertStatus.userPrompt, AlertSize.full,
                     Priority.MID, VisualAlert.steerRequired,
                     AudibleAlert.warningSoft, 2.)


# نسخة أقل حدة من SoftDisable، حيث يكون الشرط ناتجًا عن المستخدم
class UserSoftDisableAlert(SoftDisableAlert):
  def __init__(self, alert_text_2: str):
    super().__init__(alert_text_2)
    self.alert_text_1 = "القائد الآلي سيتوقف"


class ImmediateDisableAlert(Alert):
  def __init__(self, alert_text_2: str):
    super().__init__("تولي التحكم فوراً", alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.HIGHEST, VisualAlert.steerRequired,
                     AudibleAlert.warningImmediate, 4.)
    

class EngagementAlert(Alert):
  def __init__(self, audible_alert: car.CarControl.HUDControl.AudibleAlert):
    super().__init__("", "",
                     AlertStatus.normal, AlertSize.none,
                     Priority.MID, VisualAlert.none,
                     audible_alert, .2),


class NormalPermanentAlert(Alert):
  def __init__(self, alert_text_1: str, alert_text_2: str = "", duration: float = 0.2, priority: Priority = Priority.LOWER, creation_delay: float = 0.):
    super().__init__(alert_text_1, alert_text_2,
                     AlertStatus.normal, AlertSize.mid if len(alert_text_2) else AlertSize.small,
                     priority, VisualAlert.none, AudibleAlert.none, duration, creation_delay=creation_delay),


class StartupAlert(Alert):
  def __init__(self, alert_text_1: str, alert_text_2: str = "دائماً حافظ على يديك على المقود وعينيك على الطريق", alert_status=AlertStatus.normal):
    super().__init__(alert_text_1, alert_text_2,
                     alert_status, AlertSize.mid,
                     Priority.LOWER, VisualAlert.none, AudibleAlert.none, 5.)
                     

# ********** helper functions **********
def get_display_speed(speed_ms: float, metric: bool) -> str:
  speed = int(round(speed_ms * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)))
  unit = 'km/h' if metric else 'mph'
  return f"{speed} {unit}"


# ********** alert callback functions **********

AlertCallbackType = Callable[[car.CarParams, car.CarState, messaging.SubMaster, bool, int], Alert]


def soft_disable_alert(alert_text_2: str) -> AlertCallbackType:
  def func(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
    if soft_disable_time < int(0.5 / DT_CTRL):
      return ImmediateDisableAlert(alert_text_2)
    return SoftDisableAlert(alert_text_2)
  return func

def user_soft_disable_alert(alert_text_2: str) -> AlertCallbackType:
  def func(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
    if soft_disable_time < int(0.5 / DT_CTRL):
      return ImmediateDisableAlert(alert_text_2)
    return UserSoftDisableAlert(alert_text_2)
  return func

def startup_master_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  branch = get_short_branch()  # Ensure get_short_branch is cached to avoid lags on startup
  if "REPLAY" in os.environ:
    branch = "replay"

  return StartupAlert("تحذير: هذا الفرع غير مُختبر", branch, alert_status=AlertStatus.userPrompt)

def below_engage_speed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return NoEntryAlert(f"قد فوق {get_display_speed(CP.minEnableSpeed, metric)} لتفعيل القائد الآلي")


def below_steer_speed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return Alert(
    f"التوجيه غير متاح تحت {get_display_speed(CP.minSteerSpeed, metric)}",
    "",
    AlertStatus.userPrompt, AlertSize.small,
    Priority.LOW, VisualAlert.steerRequired, AudibleAlert.prompt, 0.4)


def calibration_incomplete_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  first_word = 'إعادة المعايرة' if sm['liveCalibration'].calStatus == log.LiveCalibrationData.Status.recalibrating else 'المعايرة'
  return Alert(
    f"{first_word} جارية: {sm['liveCalibration'].calPerc:.0f}%",
    f"قد فوق {get_display_speed(MIN_SPEED_FILTER, metric)}",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2)


def torque_nn_load_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  model_name = CP.lateralTuning.torque.nnModelName
  if model_name in ("", "mock"):
    return Alert(
      "لم يتم تحميل وحدة التحكم الجانبية NN",
      '⚙️ -> "sunnypilot" لمزيد من التفاصيل',
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 6.0)
  else:
    fuzzy = CP.lateralTuning.torque.nnModelFuzzyMatch
    alert_text_2 = '⚙️ -> "sunnypilot" لمزيد من التفاصيل [التطابق غير دقيق]' if fuzzy else ""
    alert_status = AlertStatus.userPrompt if fuzzy else AlertStatus.normal
    alert_size = AlertSize.mid if fuzzy else AlertSize.small
    audible_alert = AudibleAlert.prompt if fuzzy else AudibleAlert.none
    return Alert(
      "تم تحميل وحدة التحكم الجانبية NN",
      alert_text_2,
      alert_status, alert_size,
      Priority.LOW, VisualAlert.none, audible_alert, 6.0)

# *** تنبيهات التصحيح ***

def out_of_space_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  full_perc = round(100. - sm['deviceState'].freeSpacePercent)
  return NormalPermanentAlert("نفدت مساحة التخزين", f"{full_perc}% ممتلئة")


def posenet_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  mdl = sm['modelV2'].velocity.x[0] if len(sm['modelV2'].velocity.x) else math.nan
  err = CS.vEgo - mdl
  msg = f"خطأ في السرعة: {err:.1f} م/ث"
  return NoEntryAlert(msg, alert_text_1="سرعة Posenet غير صالحة")


def process_not_running_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  not_running = [p.name for p in sm['managerState'].processes if not p.running and p.shouldBeRunning]
  msg = ', '.join(not_running)
  return NoEntryAlert(msg, alert_text_1="العملية لا تعمل")


def comm_issue_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  bs = [s for s in sm.data.keys() if not sm.all_checks([s, ])]
  msg = ', '.join(bs[:4])  # لا يمكن وضع الكثير في سطر واحد
  return NoEntryAlert(msg, alert_text_1="مشكلة في الاتصال بين العمليات")


def camera_malfunction_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  all_cams = ('roadCameraState', 'driverCameraState', 'wideRoadCameraState')
  bad_cams = [s.replace('State', '') for s in all_cams if s in sm.data.keys() and not sm.all_checks([s, ])]
  return NormalPermanentAlert("عطل في الكاميرا", ', '.join(bad_cams))


def calibration_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  rpy = sm['liveCalibration'].rpyCalib
  yaw = math.degrees(rpy[2] if len(rpy) == 3 else math.nan)
  pitch = math.degrees(rpy[1] if len(rpy) == 3 else math.nan)
  angles = f"أعد تركيب الجهاز (الزاوية: {pitch:.1f}°, الانحراف: {yaw:.1f}°)"
  return NormalPermanentAlert("المعايرة غير صالحة", angles)


def overheat_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  cpu = max(sm['deviceState'].cpuTempC, default=0.)
  gpu = max(sm['deviceState'].gpuTempC, default=0.)
  temp = max((cpu, gpu, sm['deviceState'].memoryTempC))
  return NormalPermanentAlert("النظام محموم", f"{temp:.0f} °م")


def low_memory_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return NormalPermanentAlert("ذاكرة منخفضة", f"{sm['deviceState'].memoryUsagePercent}% مستخدمة")


def high_cpu_usage_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  x = max(sm['deviceState'].cpuUsagePercent, default=0.)
  return NormalPermanentAlert("استخدام عالي لوحدة المعالجة المركزية", f"{x}% مستخدم")


def modeld_lagging_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return NormalPermanentAlert("تأخر نموذج القيادة", f"{sm['modelV2'].frameDropPerc:.1f}% من الإطارات مفقودة")

def wrong_car_mode_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  text = "قم بتفعيل نظام التحكم التكيفي لتفعيل القائد الآلي"
  if CP.carName == "honda":
    text = "قم بتفعيل المفتاح الرئيسي لتفعيل القائد الآلي"
  return NoEntryAlert(text)


def joystick_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  axes = sm['testJoystick'].axes
  gb, steer = list(axes)[:2] if len(axes) else (0., 0.)
  vals = f"الغاز: {round(gb * 100.)}%, التوجيه: {round(steer * 100.)}%"
  return NormalPermanentAlert("وضع عصا التحكم", vals)

def speed_limit_adjust_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  speedLimit = sm['longitudinalPlanSP'].speedLimit
  speed = round(speedLimit * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH))
  message = f'تعديل السرعة إلى {speed} {"كم/س" if metric else "ميل/س"}'
  return Alert(
    message,
    "",
    AlertStatus.normal, AlertSize.small,
    Priority.LOW, VisualAlert.none, AudibleAlert.none, 4.)


EVENTS: dict[int, dict[str, Alert | AlertCallbackType]] = {
  # ********** أحداث بدون تنبيهات **********

  EventName.stockFcw: {},
  EventName.actuatorsApiUnavailable: {},

  # ********** أحداث تحتوي فقط على تنبيهات تظهر في جميع الحالات **********

  EventName.joystickDebug: {
    ET.WARNING: joystick_alert,
    ET.PERMANENT: NormalPermanentAlert("وضع عصا التحكم"),
  },

  EventName.controlsInitializing: {
    ET.NO_ENTRY: NoEntryAlert("النظام قيد التهيئة"),
  },

  EventName.startup: {
    ET.PERMANENT: StartupAlert("كن مستعدًا لتولي التحكم في أي وقت")
  },

  EventName.startupMaster: {
    ET.PERMANENT: startup_master_alert,
  },

  # السيارة معروفة، ولكن تم تعيينها كـ dashcam فقط
  EventName.startupNoControl: {
    ET.PERMANENT: StartupAlert("وضع Dashcam"),
    ET.NO_ENTRY: NoEntryAlert("وضع Dashcam"),
  },

  # السيارة غير معروفة
  EventName.startupNoCar: {
    ET.PERMANENT: StartupAlert("وضع Dashcam للسيارات غير المدعومة"),
  },

  EventName.startupNoFw: {
    ET.PERMANENT: StartupAlert("السيارة غير معروفة",
                               "تحقق من توصيلات الطاقة",
                               alert_status=AlertStatus.userPrompt),
  },

  EventName.dashcamMode: {
    ET.PERMANENT: NormalPermanentAlert("وضع Dashcam",
                                       priority=Priority.LOWEST),
  },

  EventName.invalidLkasSetting: {
    ET.PERMANENT: NormalPermanentAlert("نظام LKAS الافتراضي مفعّل",
                                       "أوقف تشغيل نظام LKAS الافتراضي لتفعيل القائد الآلي"),
  },

  EventName.cruiseMismatch: {
    #ET.PERMANENT: ImmediateDisableAlert("فشل القائد الآلي في إلغاء تثبيت السرعة"),
  },

  # القائد الآلي لا يتعرف على السيارة. هذا يحول القائد الآلي إلى وضع القراءة فقط.
  # يمكن حل هذه المشكلة بإضافة بصمتك.
  # راجع https://github.com/commaai/openpilot/wiki/Fingerprinting لمزيد من المعلومات
  EventName.carUnrecognized: {
    ET.PERMANENT: NormalPermanentAlert("وضع Dashcam",
                                       '⚙️ -> "المركبة" لاختيار سيارتك',
                                       priority=Priority.LOWEST),
  },

EventName.stockAeb: {
    ET.PERMANENT: Alert(
      "استخدم المكابح!",
      "نظام الكبح الطارئ الافتراضي (AEB): خطر التصادم",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 2.),
    ET.NO_ENTRY: NoEntryAlert("نظام الكبح الطارئ الافتراضي (AEB): خطر التصادم"),
  },

  EventName.fcw: {
    ET.PERMANENT: Alert(
      "استخدم المكابح!",
      "خطر التصادم",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.warningSoft, 2.),
  },

  EventName.ldw: {
    ET.PERMANENT: Alert(
      "تم الكشف عن انحراف عن المسار",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.ldw, AudibleAlert.prompt, 3.),
  },

  # ********** أحداث تحتوي فقط على تنبيهات تظهر أثناء التفعيل **********

  EventName.steerTempUnavailableSilent: {
    ET.WARNING: Alert(
      "التوجيه غير متاح مؤقتاً",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.prompt, 1.8),
  },

  EventName.preDriverDistracted: {
    ET.PERMANENT: Alert(
      "انتبه للطريق",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.promptDriverDistracted: {
    ET.PERMANENT: Alert(
      "انتبه للطريق",
      "السائق مشتت",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.driverDistracted: {
    ET.PERMANENT: Alert(
      "تعطيل القائد الآلي فوراً",
      "السائق مشتت",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.warningImmediate, .1),
  },

  EventName.preDriverUnresponsive: {
    ET.PERMANENT: Alert(
      "المس عجلة القيادة: لم يتم الكشف عن وجه",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .1, alert_rate=0.75),
  },

  EventName.promptDriverUnresponsive: {
    ET.PERMANENT: Alert(
      "المس عجلة القيادة",
      "السائق غير مستجيب",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.driverUnresponsive: {
    ET.PERMANENT: Alert(
      "تعطيل القائد الآلي فوراً",
      "السائق غير مستجيب",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.warningImmediate, .1),
  },

  EventName.preKeepHandsOnWheel: {
    ET.WARNING: Alert(
      "لم يتم الكشف عن أيدي على عجلة القيادة",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.none, .1, alert_rate=0.75),
  },

  EventName.promptKeepHandsOnWheel: {
    ET.WARNING: Alert(
      "الأيدي غير موجودة على عجلة القيادة",
      "ضع يديك على عجلة القيادة",
      AlertStatus.critical, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.keepHandsOnWheel: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("السائق لم يضع يديه على عجلة القيادة"),
  },

  EventName.manualRestart: {
    ET.WARNING: Alert(
      "تولي التحكم",
      "استأنف القيادة يدوياً",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.resumeRequired: {
    ET.WARNING: Alert(
      "اضغط على استئناف للخروج من التوقف التام",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.belowSteerSpeed: {
    ET.WARNING: below_steer_speed_alert,
  },

  EventName.preLaneChangeLeft: {
    ET.WARNING: Alert(
      "وجه السيارة إلى اليسار لبدء تغيير المسار بمجرد أن يكون آمناً",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1, alert_rate=0.75),
  },

  EventName.preLaneChangeRight: {
    ET.WARNING: Alert(
      "وجه السيارة إلى اليمين لبدء تغيير المسار بمجرد أن يكون آمناً",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1, alert_rate=0.75),
  },

  EventName.laneChangeBlocked: {
    ET.WARNING: Alert(
      "تم الكشف عن سيارة في النقطة العمياء",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, .1),
  },

  EventName.laneChangeRoadEdge: {
    ET.WARNING: Alert(
      "تغيير المسار غير متاح: حافة الطريق",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, .1),
  },

  EventName.laneChange: {
    ET.WARNING: Alert(
      "تغيير المسار",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.manualSteeringRequired: {
    ET.WARNING: Alert(
      "توجيه المسار التلقائي متوقف",
      "التوجيه اليدوي مطلوب",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.disengage, 1.),
  },

  EventName.manualLongitudinalRequired: {
    ET.WARNING: Alert(
      "نظام التحكم الذكي/التكيفي في السرعة متوقف",
      "التحكم اليدوي في الغاز/الفرامل مطلوب",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1.),
  },

  EventName.cruiseEngageBlocked: {
    ET.WARNING: Alert(
      "القائد الآلي غير متاح",
      "تم الضغط على الدواسة أثناء تفعيل التحكم في السرعة",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.brakePressed, AudibleAlert.refuse, 3.),
  },

EventName.steerSaturated: {
    ET.WARNING: Alert(
      "تولي التحكم",
      "الانعطاف يتجاوز حد التوجيه",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 2.),
  },

  # Thrown when the fan is driven at >50% but is not rotating
  EventName.fanMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("عطل في المروحة", "مشكلة في الأجهزة على الأرجح"),
  },

  # Camera is not outputting frames
  EventName.cameraMalfunction: {
    ET.PERMANENT: camera_malfunction_alert,
    ET.SOFT_DISABLE: soft_disable_alert("عطل في الكاميرا"),
    ET.NO_ENTRY: NoEntryAlert("عطل في الكاميرا: أعد تشغيل جهازك"),
  },
  # Camera framerate too low
  EventName.cameraFrameRate: {
    ET.PERMANENT: NormalPermanentAlert("معدل إطارات الكاميرا منخفض", "أعد تشغيل جهازك"),
    ET.SOFT_DISABLE: soft_disable_alert("معدل إطارات الكاميرا منخفض"),
    ET.NO_ENTRY: NoEntryAlert("معدل إطارات الكاميرا منخفض: أعد تشغيل جهازك"),
  },

  # Unused

  EventName.locationdTemporaryError: {
    ET.NO_ENTRY: NoEntryAlert("خطأ مؤقت في locationd"),
    ET.SOFT_DISABLE: soft_disable_alert("خطأ مؤقت في locationd"),
  },

  EventName.locationdPermanentError: {
    ET.NO_ENTRY: NoEntryAlert("خطأ دائم في locationd"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خطأ دائم في locationd"),
    ET.PERMANENT: NormalPermanentAlert("خطأ دائم في locationd"),
  },

  # openpilot tries to learn certain parameters about your car by observing
  # how the car behaves to steering inputs from both human and openpilot driving.
  # This includes:
  # - steer ratio: gear ratio of the steering rack. Steering angle divided by tire angle
  # - tire stiffness: how much grip your tires have
  # - angle offset: most steering angle sensors are offset and measure a non zero angle when driving straight
  # This alert is thrown when any of these values exceed a sanity check. This can be caused by
  # bad alignment or bad sensor data. If this happens consistently consider creating an issue on GitHub
  EventName.paramsdTemporaryError: {
    ET.NO_ENTRY: NoEntryAlert("خطأ مؤقت في paramsd"),
    ET.SOFT_DISABLE: soft_disable_alert("خطأ مؤقت في paramsd"),
  },

  EventName.paramsdPermanentError: {
    ET.NO_ENTRY: NoEntryAlert("خطأ دائم في paramsd"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خطأ دائم في paramsd"),
    ET.PERMANENT: NormalPermanentAlert("خطأ دائم في paramsd"),
  },

  EventName.speedLimitActive: {
    ET.WARNING: Alert(
      "تم تغيير السرعة المحددة لتتوافق مع حد السرعة المعلن",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 3.),
  },

  EventName.speedLimitValueChange: {
    ET.WARNING: speed_limit_adjust_alert,
  },

  EventName.e2eLongStart: {
    ET.PERMANENT: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.MID, VisualAlert.none, AudibleAlert.promptStarting, 1.5),
  },

  EventName.speedLimitPreActive: {
    ET.WARNING: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.MID, VisualAlert.none, AudibleAlert.promptSingleLow, .45),
  },

  EventName.speedLimitConfirmed: {
    ET.WARNING: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.MID, VisualAlert.none, AudibleAlert.promptSingleHigh, .45),
  },

  # ********** أحداث تؤثر على انتقال حالات التحكم **********

  EventName.pcmEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.engage),
  },

  EventName.buttonEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.engage),
  },

  EventName.silentButtonEnable: {
    ET.ENABLE: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.MID, VisualAlert.none, AudibleAlert.none, .2, 0., 0.),
  },

  EventName.pcmDisable: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
  },

  EventName.buttonCancel: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("تم الضغط على إلغاء"),
  },

  EventName.brakeHold: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("تفعيل الفرامل"),
  },

  EventName.silentBrakeHold: {
    ET.USER_DISABLE: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.MID, VisualAlert.none, AudibleAlert.none, .2, 0., 0.),
    ET.NO_ENTRY: NoEntryAlert("تفعيل الفرامل"),
  },

  EventName.parkBrake: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("تفعيل فرامل الانتظار"),
  },

  EventName.pedalPressed: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("تم الضغط على الدواسة",
                              visual_alert=VisualAlert.brakePressed),
  },

  EventName.silentPedalPressed: {
    ET.USER_DISABLE: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.MID, VisualAlert.none, AudibleAlert.none, .2),
    ET.NO_ENTRY: NoEntryAlert("تم الضغط على الدواسة أثناء المحاولة",
                              visual_alert=VisualAlert.brakePressed),
  },

  EventName.preEnableStandstill: {
    ET.PRE_ENABLE: Alert(
      "حرر الفرامل للتفعيل",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1, creation_delay=1.),
  },

EventName.gasPressedOverride: {
    ET.OVERRIDE_LONGITUDINAL: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.steerOverride: {
    ET.OVERRIDE_LATERAL: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.wrongCarMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: wrong_car_mode_alert,
  },

  EventName.resumeBlocked: {
    ET.NO_ENTRY: NoEntryAlert("اضغط على تعيين للتفعيل"),
  },

  EventName.wrongCruiseMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("نظام التحكم التكيفي معطل"),
  },

  EventName.steerTempUnavailable: {
    ET.SOFT_DISABLE: soft_disable_alert("التوجيه غير متاح مؤقتاً"),
    ET.NO_ENTRY: NoEntryAlert("التوجيه غير متاح مؤقتاً"),
  },

  EventName.steerTimeLimit: {
    ET.SOFT_DISABLE: soft_disable_alert("حد وقت التوجيه للمركبة"),
    ET.NO_ENTRY: NoEntryAlert("حد وقت التوجيه للمركبة"),
  },

  EventName.outOfSpace: {
    ET.PERMANENT: out_of_space_alert,
    ET.NO_ENTRY: NoEntryAlert("نفدت مساحة التخزين"),
  },

  EventName.belowEngageSpeed: {
    ET.NO_ENTRY: below_engage_speed_alert,
  },

  EventName.sensorDataInvalid: {
    ET.PERMANENT: Alert(
      "بيانات المستشعر غير صالحة",
      "مشكلة محتملة في الأجهزة",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, .2, creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("بيانات المستشعر غير صالحة"),
    ET.SOFT_DISABLE: soft_disable_alert("بيانات المستشعر غير صالحة"),
  },

  EventName.noGps: {
    ET.PERMANENT: Alert(
      "استقبال GPS ضعيف",
      "تأكد من أن الجهاز لديه رؤية واضحة للسماء",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, .2, creation_delay=600.)
  },

  EventName.soundsUnavailable: {
    ET.PERMANENT: NormalPermanentAlert("لم يتم العثور على مكبر الصوت", "أعد تشغيل جهازك"),
    ET.NO_ENTRY: NoEntryAlert("لم يتم العثور على مكبر الصوت"),
  },

  EventName.tooDistracted: {
    ET.NO_ENTRY: NoEntryAlert("مستوى التشتت مرتفع جداً"),
  },

  EventName.overheat: {
    ET.PERMANENT: overheat_alert,
    ET.SOFT_DISABLE: soft_disable_alert("النظام محموم"),
    ET.NO_ENTRY: NoEntryAlert("النظام محموم"),
  },

  EventName.wrongGear: {
    ET.SOFT_DISABLE: user_soft_disable_alert("الترس ليس في الوضع D"),
    ET.NO_ENTRY: NoEntryAlert("الترس ليس في الوضع D"),
  },

  EventName.silentWrongGear: {
    ET.SOFT_DISABLE: Alert(
      "الترس ليس في الوضع D",
      "القائد الآلي غير متاح",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 2., 3.),
    ET.NO_ENTRY: Alert(
      "الترس ليس في الوضع D",
      "القائد الآلي غير متاح",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 0., 2., 3.),
  },

  # This alert is thrown when the calibration angles are outside of the acceptable range.
  # For example if the device is pointed too much to the left or the right.
  # Usually this can only be solved by removing the mount from the windshield completely,
  # and attaching while making sure the device is pointed straight forward and is level.
  # See https://comma.ai/setup for more information
  EventName.calibrationInvalid: {
    ET.PERMANENT: calibration_invalid_alert,
    ET.SOFT_DISABLE: soft_disable_alert("المعايرة غير صالحة: أعد تركيب الجهاز وأعد المعايرة"),
    ET.NO_ENTRY: NoEntryAlert("المعايرة غير صالحة: أعد تركيب الجهاز وأعد المعايرة"),
  },

  EventName.calibrationIncomplete: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: soft_disable_alert("المعايرة غير مكتملة"),
    ET.NO_ENTRY: NoEntryAlert("المعايرة جارية"),
  },

  EventName.calibrationRecalibrating: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: soft_disable_alert("تم اكتشاف إعادة تركيب الجهاز: إعادة المعايرة"),
    ET.NO_ENTRY: NoEntryAlert("تم اكتشاف إعادة تركيب الجهاز: إعادة المعايرة"),
  },

  EventName.doorOpen: {
    ET.SOFT_DISABLE: user_soft_disable_alert("الباب مفتوح"),
    ET.NO_ENTRY: NoEntryAlert("الباب مفتوح"),
  },

  EventName.seatbeltNotLatched: {
    ET.SOFT_DISABLE: user_soft_disable_alert("حزام الأمان غير مربوط"),
    ET.NO_ENTRY: NoEntryAlert("حزام الأمان غير مربوط"),
  },

  EventName.espDisabled: {
    ET.SOFT_DISABLE: soft_disable_alert("نظام التحكم الإلكتروني بالثبات معطل"),
    ET.NO_ENTRY: NoEntryAlert("نظام التحكم الإلكتروني بالثبات معطل"),
  },

  EventName.lowBattery: {
    ET.SOFT_DISABLE: soft_disable_alert("البطارية منخفضة"),
    ET.NO_ENTRY: NoEntryAlert("البطارية منخفضة"),
  },

  # Different openpilot services communicate between each other at a certain
  # interval. If communication does not follow the regular schedule this alert
  # is thrown. This can mean a service crashed, did not broadcast a message for
  # ten times the regular interval, or the average interval is more than 10% too high.
  EventName.commIssue: {
    ET.SOFT_DISABLE: soft_disable_alert("مشكلة في الاتصال بين العمليات"),
    ET.NO_ENTRY: comm_issue_alert,
  },
  EventName.commIssueAvgFreq: {
    ET.SOFT_DISABLE: soft_disable_alert("معدل الاتصال بين العمليات منخفض"),
    ET.NO_ENTRY: NoEntryAlert("معدل الاتصال بين العمليات منخفض"),
  },

  EventName.controlsdLagging: {
    ET.SOFT_DISABLE: soft_disable_alert("تأخر في التحكم"),
    ET.NO_ENTRY: NoEntryAlert("تأخر في عملية التحكم: أعد تشغيل جهازك"),
  },

  # Thrown when manager detects a service exited unexpectedly while driving
  EventName.processNotRunning: {
    ET.NO_ENTRY: process_not_running_alert,
    ET.SOFT_DISABLE: soft_disable_alert("العملية لا تعمل"),
  },

  EventName.radarFault: {
    ET.SOFT_DISABLE: soft_disable_alert("خطأ في الرادار: أعد تشغيل السيارة"),
    ET.NO_ENTRY: NoEntryAlert("خطأ في الرادار: أعد تشغيل السيارة"),
  },

  # Every frame from the camera should be processed by the model. If modeld
  # is not processing frames fast enough they have to be dropped. This alert is
  # thrown when over 20% of frames are dropped.
  EventName.modeldLagging: {
    ET.SOFT_DISABLE: soft_disable_alert("تأخر نموذج القيادة"),
    ET.NO_ENTRY: NoEntryAlert("تأخر نموذج القيادة"),
    ET.PERMANENT: modeld_lagging_alert,
  },

  # Besides predicting the path, lane lines and lead car data the model also
  # predicts the current velocity and rotation speed of the car. If the model is
  # very uncertain about the current velocity while the car is moving, this
  # usually means the model has trouble understanding the scene. This is used
  # as a heuristic to warn the driver.
  EventName.posenetInvalid: {
    ET.SOFT_DISABLE: soft_disable_alert("سرعة Posenet غير صالحة"),
    ET.NO_ENTRY: posenet_invalid_alert,
  },

  # When the localizer detects an acceleration of more than 40 m/s^2 (~4G) we
  # alert the driver the device might have fallen from the windshield.
  EventName.deviceFalling: {
    ET.SOFT_DISABLE: soft_disable_alert("سقوط الجهاز من الحامل"),
    ET.NO_ENTRY: NoEntryAlert("سقوط الجهاز من الحامل"),
  },

  EventName.lowMemory: {
    ET.SOFT_DISABLE: soft_disable_alert("ذاكرة منخفضة: أعد تشغيل جهازك"),
    ET.PERMANENT: low_memory_alert,
    ET.NO_ENTRY: NoEntryAlert("ذاكرة منخفضة: أعد تشغيل جهازك"),
  },

  EventName.highCpuUsage: {
    #ET.SOFT_DISABLE: soft_disable_alert("خلل في النظام: أعد تشغيل جهازك"),
    #ET.PERMANENT: NormalPermanentAlert("خلل في النظام", "أعد تشغيل جهازك"),
    ET.NO_ENTRY: high_cpu_usage_alert,
  },

  EventName.accFaulted: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خلل في نظام التحكم: أعد تشغيل السيارة"),
    ET.PERMANENT: NormalPermanentAlert("خلل في نظام التحكم: أعد تشغيل السيارة للتفعيل"),
    ET.NO_ENTRY: NoEntryAlert("خلل في نظام التحكم: أعد تشغيل السيارة"),
  },

  EventName.espActive: {
    ET.SOFT_DISABLE: soft_disable_alert("نظام التحكم الإلكتروني بالثبات نشط"),
    ET.NO_ENTRY: NoEntryAlert("نظام التحكم الإلكتروني بالثبات نشط"),
  },

  EventName.controlsMismatch: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("عدم تطابق في التحكم"),
    ET.NO_ENTRY: NoEntryAlert("عدم تطابق في التحكم"),
  },

  EventName.controlsMismatchLong: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("عدم تطابق في التحكم\nطولي"),
    ET.NO_ENTRY: NoEntryAlert("عدم تطابق في التحكم\nطولي"),
  },

  EventName.roadCameraError: {
    ET.PERMANENT: NormalPermanentAlert("خطأ في كاميرا الطريق CRC",
                                       duration=1.,
                                       creation_delay=30.),
  },

  EventName.wideRoadCameraError: {
    ET.PERMANENT: NormalPermanentAlert("خطأ في كاميرا الطريق العريضة CRC",
                                       duration=1.,
                                       creation_delay=30.),
  },

  EventName.driverCameraError: {
    ET.PERMANENT: NormalPermanentAlert("خطأ في كاميرا السائق CRC",
                                       duration=1.,
                                       creation_delay=30.),
  },

  # Sometimes the USB stack on the device can get into a bad state
  # causing the connection to the panda to be lost
  EventName.usbError: {
    ET.SOFT_DISABLE: soft_disable_alert("خطأ في USB: أعد تشغيل جهازك"),
    ET.PERMANENT: NormalPermanentAlert("خطأ في USB: أعد تشغيل جهازك", ""),
    ET.NO_ENTRY: NoEntryAlert("خطأ في USB: أعد تشغيل جهازك"),
  },

# يمكن أن يتم إطلاق هذا التنبيه للأسباب التالية:
  # - لم يتم استقبال أي بيانات CAN على الإطلاق
  # - تم استقبال بيانات CAN، ولكن بعض الرسائل لم يتم استقبالها بالتردد الصحيح
  # إذا لم تكن تقوم بكتابة منفذ سيارة جديد، فعادةً ما يكون السبب هو الأسلاك الخاطئة
  EventName.canError: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خطأ في CAN"),
    ET.PERMANENT: Alert(
      "خطأ في CAN: تحقق من التوصيلات",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1., creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("خطأ في CAN: تحقق من التوصيلات"),
  },

  EventName.canBusMissing: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("تم فصل ناقل CAN"),
    ET.PERMANENT: Alert(
      "تم فصل ناقل CAN: كابل معطل على الأرجح",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1., creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("تم فصل ناقل CAN: تحقق من التوصيلات"),
  },

  EventName.steerUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خلل في LKAS: أعد تشغيل السيارة"),
    ET.PERMANENT: NormalPermanentAlert("خلل في LKAS: أعد تشغيل السيارة للتفعيل"),
    ET.NO_ENTRY: NoEntryAlert("خلل في LKAS: أعد تشغيل السيارة"),
  },

  EventName.reverseGear: {
    ET.PERMANENT: Alert(
      "الترس العكسي",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2, creation_delay=0.5),
    ET.USER_DISABLE: ImmediateDisableAlert("الترس العكسي"),
    ET.NO_ENTRY: NoEntryAlert("الترس العكسي"),
  },

  EventName.spReverseGear: {
    ET.PERMANENT: Alert(
      "الترس العكسي",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2, creation_delay=0.5),
    ET.NO_ENTRY: NoEntryAlert("الترس العكسي"),
  },

  # في السيارات التي تستخدم نظام ACC الافتراضي، يمكن للسيارة أن تقرر إلغاء ACC لأسباب مختلفة.
  # عندما يحدث هذا، لا يمكننا التحكم في السيارة بعد الآن، لذا يجب تحذير المستخدم فوراً.
  EventName.cruiseDisabled: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("تم إيقاف التحكم في السرعة"),
  },

  # لتخطيط المسار، يتم استخدام التحكم التنبؤي النموذجي (MPC).
  # هذا هو خوارزمية تحسين غير مضمونة لإيجاد حل قابل للتطبيق.
  # إذا لم يتم العثور على حل أو كان الحل ذو تكلفة عالية جداً، يتم إطلاق هذا التنبيه.
  EventName.plannerErrorDEPRECATED: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خطأ في حل المخطط"),
    ET.NO_ENTRY: NoEntryAlert("خطأ في حل المخطط"),
  },

  # عندما يفتح المرحل في صندوق التوصيلات، يتم فصل ناقل CAN بين كاميرا LKAS وبقية السيارة.
  # عندما يتم استقبال رسائل من كاميرا LKAS على جانب السيارة، فهذا يعني عادةً أن المرحل لم يفتح بشكل صحيح
  # ويتم إطلاق هذا التنبيه.
  EventName.relayMalfunction: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("خلل في مرحل التوصيلات"),
    ET.PERMANENT: NormalPermanentAlert("خلل في مرحل التوصيلات", "تحقق من الأجهزة"),
    ET.NO_ENTRY: NoEntryAlert("خلل في مرحل التوصيلات"),
  },

  EventName.speedTooLow: {
    ET.IMMEDIATE_DISABLE: Alert(
      "تم إلغاء القائد الآلي",
      "السرعة منخفضة جداً",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.disengage, 3.),
  },

  # عندما تكون السيارة تسير بسرعة أكبر من معظم السيارات في بيانات التدريب، يمكن أن تكون مخرجات النموذج غير متوقعة.
  EventName.speedTooHigh: {
    ET.WARNING: Alert(
      "السرعة عالية جداً",
      "النموذج غير مؤكد عند هذه السرعة",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 4.),
    ET.NO_ENTRY: NoEntryAlert("تباطأ للتفعيل"),
  },

  EventName.lowSpeedLockout: {
    ET.PERMANENT: NormalPermanentAlert("خلل في التحكم: أعد تشغيل السيارة للتفعيل"),
    ET.NO_ENTRY: NoEntryAlert("خلل في التحكم: أعد تشغيل السيارة"),
  },

  EventName.lkasDisabled: {
    ET.PERMANENT: NormalPermanentAlert("تم تعطيل LKAS: قم بتفعيل LKAS للتفعيل"),
    ET.NO_ENTRY: NoEntryAlert("تم تعطيل LKAS"),
  },

  EventName.vehicleSensorsInvalid: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("أجهزة استشعار السيارة غير صالحة"),
    ET.PERMANENT: NormalPermanentAlert("أجهزة استشعار السيارة قيد المعايرة", "قد لتتم المعايرة"),
    ET.NO_ENTRY: NoEntryAlert("أجهزة استشعار السيارة قيد المعايرة"),
  },

  EventName.torqueNNLoad: {
    ET.PERMANENT: torque_nn_load_alert,
  },

  EventName.hyundaiRadarTracksAvailable: {
    ET.PERMANENT: NormalPermanentAlert("مسارات الرادار متاحة. أعد تشغيل السيارة للتهيئة")
  }
}


if __name__ == '__main__':
  # print all alerts by type and priority
  from cereal.services import SERVICE_LIST
  from collections import defaultdict

  event_names = {v: k for k, v in EventName.schema.enumerants.items()}
  alerts_by_type: dict[str, dict[Priority, list[str]]] = defaultdict(lambda: defaultdict(list))

  CP = car.CarParams.new_message()
  CS = car.CarState.new_message()
  sm = messaging.SubMaster(list(SERVICE_LIST.keys()))

  for i, alerts in EVENTS.items():
    for et, alert in alerts.items():
      if callable(alert):
        alert = alert(CP, CS, sm, False, 1)
      alerts_by_type[et][alert.priority].append(event_names[i])

  all_alerts: dict[str, list[tuple[Priority, list[str]]]] = {}
  for et, priority_alerts in alerts_by_type.items():
    all_alerts[et] = sorted(priority_alerts.items(), key=lambda x: x[0], reverse=True)

  for status, evs in sorted(all_alerts.items(), key=lambda x: x[0]):
    print(f"**** {status} ****")
    for p, alert_list in evs:
      print(f"  {repr(p)}:")
      print("   ", ', '.join(alert_list), "\n")