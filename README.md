Table of Contents
=======================

* [Join our Discord](#-join-our-discord)
* [Read Before Installing](#-read-before-installing)
* [Prohibited Safety Modifications](#-prohibited-safety-modifications)
* [Installation](#-installation)
* [Highlight Features](#-highlight-features)
* [Driving Enhancements](#-driving-enhancements)
* [Branch Definitions](#-branch-definitions)
* [Recommended Branches](#-recommended-branches)
* [How-To's](#-How-Tos)
* [Donate](#-donate)
* [Pull Requests](#-Pull-Requests)
* [Special Thanks](#-special-thanks)
* [Licensing](#licensing)

---

<details><summary><h3>💭 Join our Discord</h3></summary>

 Join the official sunnypilot Discord server to stay up to date with all the latest features and be a part of shaping the future of sunnypilot!
* https://discord.gg/wRW3meAgtx
 
    ![Discord Shield](https://discordapp.com/api/guilds/880416502577266699/widget.png?style=shield)
 
</details>

<details><summary><h3>🚨 Read Before Installing</h3></summary>
 
It is recommended to read this entire page before proceeding. This will ensure that you fully understand each added feature on sunnypilot and you are selecting the right branch for your car (and device) to have the best driving experience.

sunnypilot is recommended to be used for **most** models of the following car manufacturers:
* Hyundai/Kia/Genesis (**HKG**)
* Honda
* Toyota
* Subaru
* Chrysler/Jeep/RAM (**FCA**)
* General Motors (**GM**)

This is a fork of [comma.ai's openpilot](https://github.com/commaai/openpilot). By installing this software, you accept all responsibility for anything that might occur while you use it. All contributors to sunnypilot are not liable. ❗<ins>**Use at your own risk.**</ins>❗
</details>

<details><summary><h3>⛔ Prohibited Safety Modifications</h3></summary>
 
All [official sunnypilot branches](https://github.com/sunnyhaibin/sunnypilot/branches) from sunnypilot's official GitHub repository strictly adhere to [comma.ai's safety policy](https://github.com/commaai/openpilot/blob/master/docs/SAFETY.md). Any changes to this policy will result in your fork and/or device being banned from both comma.ai and sunnypilot channels.

The following changes are a **VIOLATION** and **ARE NOT** included in any sunnypilot branches:
* Driver Monitoring:
  * ❌ "Nerfing" or reducing monitoring bounds.
* Panda safety:
  * ❌ No preventing disengaging of <ins>**LONGITUDINAL CONTROL**</ins> (acceleration/brake) on brake pedal press (never included in MADS).
  * ❌ No auto re-engaging of <ins>**LONGITUDINAL CONTROL**</ins> (acceleration/brake) on brake pedal release (never included in MADS).
  * ❌ No disengaging on ACC MAIN in OFF state.

</details>


<details><summary><h3>⚒ Installation</h3></summary>

 <details><summary>comma.ai URL (Easy)</summary> 

  ### comma three
  ---
  
   Please refer to [Recommended Branches](#-recommended-branches) to find your preferred/supported branch, this guide will assume you want to install the latest release:

   1. Factory reset/uninstall previous software if you already installed another fork.
   2. Select `Custom Software` when given the option.
   3. Input the following URL: ```installer.comma.ai/sunnyhaibin/test-c3``` (note: `https://` is not recrequired on the comma three)
   4. Complete the rest of the installation.
   5. Pop into the `#installation-help` channel on Discord for any more assistance.

 ### comma two
  ---

  Please refer to [Recommended Branches](#-recommended-branches) to find your preferred/supported branch, this will assume you want to install the latest release:

  1. Factory reset/uninstall previous software if you already installed another fork.
  2. Select `Custom Software` when given the option.
  3. Input the following URL: ```https://installer.comma.ai/sunnyhaibin/0.8.12-4-prod```
  4. Complete the rest of the installation.
  5. Pop into the `#installation-help` channel on Discord for any more assistance.


  </details>
   
 <details>
 <summary>SSH (More Versatile)</summary>
 </br>
 
 Prerequisites: [How to SSH](https://github.com/commaai/openpilot/wiki/SSH)
 
If you are looking to install sunnyhaibin's fork via SSH, run the following command in an SSH terminal after connecting to your device:

  
 ### comma three:
 ---
* [`test-c3`](https://github.com/sunnyhaibin/openpilot/tree/test-c3):
    ```
    cd /data; rm -rf ./openpilot; git clone -b test-c3 --depth 1 --single-branch --recurse-submodules --shallow-submodules https://github.com/sunnyhaibin/openpilot.git openpilot; cd openpilot; sudo reboot
    ```
### comma two:
---
* [`0.8.12-prod-personal-hkg`](https://github.com/sunnyhaibin/openpilot/tree/0.8.12-prod-personal-hkg):
    ```
    cd /data; rm -rf ./openpilot; git clone -b 0.8.12-prod-personal-hkg --depth 1 --single-branch --recurse-submodules --shallow-submodules https://github.com/sunnyhaibin/openpilot.git openpilot; cd openpilot; reboot
    ```
After running the command to install the desired branch, your comma device should reboot.
  </details>  
 
 </details>  


<details><summary><h3>🚗 Highlight Features</h3></summary>
 
### Quality of life Enhancements
- [**Modified Assistive Driving Safety (MADS)**](#modified-assistive-driving-safety-mads) - sunnypilot Automatic Lane Centering (ALC) and Adaptive Cruise Control (ACC) / Smart Cruise Control (SCC) can be engaged independently of each other
  * This feature is enabled by default and can be disabled in the "sunnypilot" menu
- [**Dynamic Lane Profile (DLP)**](#dynamic-lane-profile-dlp) - Dynamically switch lane profile base on lane recognition confidence (depreciated after `test-c3-20220907`)
- [**Enhanced Speed Control**](#enhanced-speed-control) - Utilizes data from vision or OpenStreetMap to achieve dynamic speed control without user's intervention
  * Vision-based Turn Speed Control (VTSC)
  * Map-Data-based Turn Speed Control (MTSC)
  * Speed Limit control (SLC)
  * HKG only: Highway Driving Assist (HDA) status integration - on applicable HKG cars only
- [**Gap Adjust Cruise (GAC)**](#gap-adjust-cruise) - Enable the `GAP`/`INTERVAL`/`DISTANCE` button on the steering wheel or on screen button to adjust the cruise gap between the car and the lead car
 - [**Quiet Drive 🤫**](#-quiet-drive) - Toggle to mute all notification sounds (excluding driver safety warnings)
 - [**Auto Lane Change Timer**](#Auto-Lane-Change-Timer) - Set a timer to delay the auto lane change operation when the blinker is used. No nudge on the steering wheel is required to auto lane change if a timer is set
 - [**Force Car Recognition (FCR)**](#Force-Car-Recognition-) - Use a selector to force your car to be recognized by sunnypilot
 - [**Fix sunnypilot No Offroad**](#Fix-sunnypilot-No-Offroad) - Enforce sunnypilot to go offroad and turns off after shutting down the car. This feature fixes non-official devices running sunnypilot without comma power
 - [**Enable ACC+MADS with RES+/SET-**](#Enable-ACC+MADS-with-RES+/SET-) - Engage both ACC and MADS with a single press of RES+ or SET- button
 - [**Enable Offline Maps Download**](#Enable-Offline-Maps-Download) - OpenStreetMap database can now be downloaded locally for offline use. Currently offering US South, US West, US Northeast, US Florida, Taiwan, and South Africa
 - [**Various Live Tuning**](#Various0-Live-Tuning) - Ability to fine turn your driving experience without having to wait for the official commit
   * Enforce Torque Lateral Control - Use latest torque controller for all vehicles.
   * Torque Lateral Control Live Tune - Ability to adjust the torque contoller's `FRICTION` and `LAT_ACCEL_FACTOR` values to suit your vehicle.
   * Torque Lateral Controller Self-Tune - Enable self turning for the Torque controller.

### Visual Enhancements
* **M.A.D.S Status Icon** - Dedicated icon to display M.A.D.S. engagement status
  * Green🟢: M.A.D.S. engaged
  * White⚪: M.A.D.S. suspended or disengaged
* **Lane Color** - Various lane colors to display real-time Lane Model and M.A.D.S. engagement status
  * 0.8.14 and later:
    * Blue🔵: Laneful mode, M.A.D.S. engaged
    * Green🟢: Laneless mode, M.A.D.S. engaged
    * Yellow🟡: Experimetal e2e, M.A.D.S. engaged
  * Before and not 0.8.14:
    * Green🟢: Laneful mode, M.A.D.S. engaged
    * Red🔴: Laneless mode, M.A.D.S. engaged
  * White⚪: M.A.D.S. suspended or disengaged
  * Black⚫: M.A.D.S. engaged, steering is being manually override by user
* **Developer (Dev) UI** - Display various real-time metrics on screen while driving
  * 1. Enable "Show debug UI elements" in the "sunnypilot' menu
  * 2. Click on the "MAX" box on the top left of the sunnypilot display to toggle different metrics display
* **Stand Still Timer** - Display time spent at a stop with M.A.D.S engaged (i.e., at a stop lights, stop signs, traffic congestions)
* **Braking Status** - Current car speed text turns red when the car is braking by the driver or ACC/SCC

### Operational Enhancements
* **Fast Boot** - sunnypilot will fast boot by creating a Prebuilt file
* **Disable Onroad Uploads** - Disable uploads completely when onroad. Necessary to avoid high data usage when connected to Wi-Fi hotspot
* **Brightness Control (Global)** - Manually adjusts the global brightness of the screen
* **Driving Screen Off Timer** - Turns off the device screen or reduces brightness to protect the screen after car starts
* **Driving Screen Off Brightness (%)** - When using the Driving Screen Off feature, the brightness is reduced according to the automatic brightness ratio
* **Max Time Offroad** - Device is automatically turned off after a set time when the engine is turned off (off-road) after driving (on-road)

 </details>


<details><summary><h3>🚗 Driving Enhancements</h3></summary>
 
### Modified Assistive Driving Safety (MADS)
The goal of Modified Assistive Driving Safety (MADS) is to enhance the user driving experience with modified behaviors of driving assist engagements. This feature complies with comma.ai's safety rules as accurately as possible with the following changes:
* sunnypilot Automatic Lane Centering and ACC/SCC can be engaged independently of each other
* Dedicated button to toggle sunnypilot ALC:
  * `CRUISE (MAIN)` button: All supported cars on sunnypilot
    * `LFA` button: Newer HKG cars with `LFA` button
    * `LKAS` button: Honda, Toyota, Global Subaru
* `SET-` button enables ACC/SCC
* `CANCEL` button only disables ACC/SCC
* `CRUISE (MAIN)` must be `ON` to use MADS and ACC/SCC
* `CRUISE (MAIN)` button disables sunnypilot completely when `OFF` **(strictly enforced in panda safety code)**
* NEW❗ **Disengage Lateral ALC on Brake Press Mode** toggle:
  1. `ON`: `BRAKE pedal` press will pause sunnypilot Automatic Lane Centering; `BRAKE pedal` release will resume sunnypilot Automatic Lane Centering; `BRAKE pedal` release will NOT resume ACC/SCC without an explicit entry **(strictly enforced in panda safety code)**
  2. `OFF`: `BRAKE pedal` press will NOT pause sunnypilot Automatic Lane Centering; `BRAKE pedal` release will NOT resume ACC/SCC without an explicit entry **(strictly enforced in panda safety code)**
* `TURN SIGNALS` (`Left` or `Right`) will pause sunnypilot Automatic Lane Centering if the vehicle speed is below the threshold for sunnypilot Automatic Lane Change
* Event audible alerts are more relaxed to match manufacturer's stock behavior
* Critical events trigger disengagement of Automatic Lane Centering completely. The disengagement is enforced in sunnypilot and panda safety

### Dynamic Lane Profile (DLP)
Dynamic Lane Profile (DLP) aims to provide the best driving experience at staying within a lane confidently. Dynamic Lane Profile allows sunnypilot to dynamically switch between lane profiles based on lane recognition confidence level on road.

There are 3 modes to select on the onroad camera screen:
* **Auto Lane**: sunnypilot dynamically chooses between `Laneline` or `Laneless` model
* **Laneline**: sunnypilot uses Laneline model only.
* **Laneless**: sunnypilot uses Laneless model only.

To use Dynamic Lane Profile, do the following:
```
1. sunnypilot Settings -> SP - Controls -> Enable Dynamic Lane Profile -> ON toggle
2. Reboot.
3. Before driving, on the onroad camera screen, toggle between the 3 modes by pressing on the button.
4. Drive. 
```

### Enhanced Speed Control
This fork now allows supported cars to dynamically adjust the longitudinal plan based on the fetched map data. Big thanks to the Move Fast team for the amazing implementation!

**Supported cars:**
* sunnypilot Longitudinal Control capable
* Stock Longitudinal Control
  * Hyundai/Kia/Genesis (non CAN-FD)
  * Honda Bosch
  * Volkswagen MQB

Certain features are only available with an active data connection, via:
* [comma Prime](https://comma.ai/prime) - Intuitive service provided directly by comma, or;
* Personal Hotspot - From your mobile device, or a dedicated hotspot from a cellular carrier.

**Features:**
* Vision-based Turn Speed Control (VTSC) - Use vision path predictions to estimate the appropriate speed to drive through turns ahead - i.e., slowing down for curves
* Map-Data-based Turn Speed Control (MTSC) - Use curvature information from map data to define speed limits to take turns ahead - i.e., slowing down for curves
  * **Note: Requires data connection**
* Speed Limit Control (SLC) - Use speed limit signs information from map data and car interface to automatically adapt cruise speed to road limits
  * HKG only: Highway Driving Assist (HDA) status integration - on applicable HKG cars only
  * **Note: Requires data connection**
    * Speed Limit Offset - When Speed Limit Control is enabled, set speed limit slightly higher than the actual speed limit for a more natural drive
      * **Note: Requires data connection**
* Hands on Wheel Monitoring - Monitors and alerts the driver when their hands have not been on the steering wheel for an extended time

### Custom Stock Longitudinal Control
While using stock Adaptive/Smart Cruise Control, Custom Stock Longitudinal Control in sunnypilot allows sunnypilot to manipulate and take over the set speed on the car's dashboard.

**Supported Cars:**
* Hyundai/Kia/Genesis
  * CAN platform
  * CAN-FD platform with 0x1CF broadcasted in CAN traffic
* Honda Bosch
* Volkswagen MQB

**Instruction**

**📗 How to use Custom Longitudinal Control on sunnypilot **

When using Speed Limit, Vision, or Map based Turn control, you will be setting the "MAX" ACC speed on the sunnypilot display instead of the one in the dashboard. The car will then set the ACC setting in the dashboard to the targeted speed, but will never exceed the max speed set on the sunnypilot display. A quick press of the RES+ or SET- buttons will change this speed by 5 MPH or KM/H on the sunnypilot display, while a long deliberate press (about a 1/2 second press) changes it by 1 MPH or KM/H. DO NOT hold the RES+ or SET- buttons for longer that a 1 second. Either make quick or long deliberate presses only.

**‼ Where to look when setting ACC speed ‼**

Do not look at the dashboard when setting your ACC max speed. Instead, only look at the one on the sunnypilot display, "MAX". The reason you need to look at the sunnypilot display is because sunnypilot will be changing the one in the dashboard. It will be adjusting it as needed, never raising it above the one set on the sunnypilot display. ONLY look at the MAX speed on the sunnypilot display when setting the ACC speed instead of the dashboard!

(Courtesy instructions from John, author of jvePilot)

### Gap Adjust Cruise
This fork now allows supported openpilot longitudinal cars to adjust the cruise gap between the car and the lead car.

**Supported cars:**
* sunnypilot Longitudinal Control capable

🚨**PROCEED WITH EXTREME CAUTION AND BE READY TO MANUALLY TAKE OVER AT ALL TIMES**

There are 4 modes to select on the steering wheel and/or the onroad camera screen:
* **Far Gap**: Furthest distance - 1.8 second profile
* **Normal Gap**: Stock sunnypilot distance - 1.45 second profile
* **Aggro Gap**: Aggressive distance - 1.2 second profile
* 🚨**Maniac Gap**🚨: Extremely aggressive distance - 1.0 second profile

**Availability**

|      Car Make       | Far Gap | Normal Gap | Aggro Gap | Maniac Gap |
|:-------------------:|:-------:|:----------:|:---------:|:----------:|
|       Honda         |    ✅    |     ✅      |     ✅     |     ⚠      |
| Hyundai/Kia/Genesis |    ✅    |     ✅      |     ✅     |     ⚠      |
|       Toyota        |    ✅    |     ✅      |     ✅     |     ❌      |

</details>


<details><summary><h3>⚒ Branch Definitions</h3></summary>
 
|     Tag      | Definition                                 | Description                                                                                                                     |
|:------------:|--------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
|    `prod`    | Production branches                        | Include features that are tested by users and ready to use. ✅                                                                   |
|  `staging`   | Staging branches                           | Include new features that are not tested by users. No stability guaranteed. 🚨                                                  |
|  `feature`   | Feature branches                           | Represent new features being added to the system. No stability guaranteed. 🚨                                                   |
|    `test`    | Test branches                              | For experimenting with concepts that might not get used in the project. No stability guaranteed. 🚨                             |
|  `develop`   | Development branches                       | All features are gathered in respective versions. Reviewed features will be committed to `develop`. No stability guaranteed. 🚨 |
|    `full`    | Full Feature branches                      | All features inclusive within the branch.                                                                                       |
|  `personal`  | sunnyhaibin's personal branches            | On top of Full Feature.                                                                                                         |
|    `hkg`     | Hyundai/Kia/Genesis(HKG)-specific branches | Only for HKG cars.                                                                                                              |
|   `honda`    | Honda-specific branches                    | Only for Honda cars.                                                                                                            |
|   `toyota`   | Toyota-specific branches                   | Only for Toyota cars.                                                                                                           |
|   `subaru`   | Subaru-specific branches                   | Only for Subaru cars.                                                                                                           |
| `volkswagen` | Volkswagen-specific branches               | Only for Volkswagen cars.                                                                                                       |

Example:
* [`0.8.12-prod-full-honda`](https://github.com/sunnyhaibin/openpilot/tree/0.8.12-prod-full-hkg): 0.8.12-based, Production, Full Feature, Honda branch
* [`0.8.12-prod-personal-hkg`](https://github.com/sunnyhaibin/openpilot/tree/0.8.12-prod-personal-hkg): 0.8.12-based, Production, sunnyhaibin's personal Full Feature, Hyundai/Kia/Genesis branch

</details>

<details><summary><h3>✅ Recommended Branches</h3></summary>
 
| Branch                                                                            | Definition                                                                                          | Compatible Device | Changelogs                                                                                                      |
|:----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------|
| `0.8.12-prod-full-<car>`                                                          | • Latest production/stable branch<br/>• Based on comma.ai's openpilot 0.8.12                        | comma two         | [`0.8.14-prod-<car>` Changelogs](https://github.com/sunnyhaibin/sunnypilot/branches/all?query=0.8.12-prod-full) |
| [`0.8.14-prod-c3`](https://github.com/sunnyhaibin/sunnypilot/tree/0.8.14-prod-c3) | • Latest production/stable branch<br/>• Based on comma.ai's openpilot 0.8.14                        | comma three       | [`0.8.14-prod-c3` Changelogs](https://github.com/sunnyhaibin/sunnypilot/blob/0.8.14-prod-c3/CHANGELOGS.md)      |
| [`test-c3`](https://github.com/sunnyhaibin/sunnypilot/tree/test-c3)               | • Latest test branch with experimental features<br/>• Based on comma.ai's openpilot latest upstream | comma three       | [`test-c3` Changelogs](https://github.com/sunnyhaibin/sunnypilot/blob/test-c3/CHANGELOGS.md)                    |


</details>


<details>
 <summary><h3>📗 How To's</h3></summary>
 
How-To instructions can be found in [HOW-TOS.md](https://github.com/sunnyhaibin/openpilot/blob/(!)README/HOW-TOS.md).
</details>

<details><summary><h3>💰 Donate</h3></summary>
If you find any of the features useful, feel free to donate to support for future feature development.

Thank you for your continuous love and support! Enjoy 🥰

**PayPal:**

<a href="https://paypal.me/sunnyhaibin0850" target="_blank">
<img src="https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif" alt="PayPal this" title="PayPal - The safer, easier way to pay online!" border="0" />
</a>
<br></br>

**PayPal QR Code:**

![sunnyhaibin0850_qrcode_paypal.me.png](sunnyhaibin0850_qrcode_paypal.me.png)
</details>


<details><summary><h3>🎆 Pull Requests</h3></summary>
We welcome both pull requests and issues on GitHub. Bug fixes are encouraged.

Pull requests should be against the most current `prod-full` branch.
</details>


<details><summary><h3>🏆 Special Thanks</h3></summary>
 
* [spektor56](https://github.com/spektor56/openpilot)
* [rav4kumar](https://github.com/rav4kumar/openpilot)
* [mob9221](https://github.com/mob9221/opendbc)
* [briantran33](https://github.com/briantran33/openpilot)
* [Aragon7777](https://github.com/aragon7777/openpilot)
* [sshane](https://github.com/sshane/openpilot-installer-generator)
* [jung](https://github.com/chanhojung/openpilot)
* [dri94](https://github.com/dri94/openpilot)
* [JamesKGithub](https://github.com/JamesKGithub/FrogPilot)
* [twilsonco](https://github.com/twilsonco/openpilot)
* [martinl](https://github.com/martinl/openpilot)
* [multikyd](https://github.com/openpilotkr)
* [Move Fast GmbH](https://github.com/move-fast/openpilot)
* [dragonpilot](https://github.com/dragonpilot-community/dragonpilot)
* [neokii](https://github.com/neokii/openpilot)
* [Aragon7777](https://github.com/aragon7777)
* [AlexandreSato](https://github.com/AlexandreSato/openpilot)

</details>

Licensing
------

openpilot is released under the MIT license. Some parts of the software are released under other licenses as specified.

Any user of this software shall indemnify and hold harmless comma.ai, Inc. and its directors, officers, employees, agents, stockholders, affiliates, subcontractors and customers from and against all allegations, claims, actions, suits, demands, damages, liabilities, obligations, losses, settlements, judgments, costs and expenses (including without limitation attorneys’ fees and costs) which arise out of, relate to or result from any use of this software by user.

**THIS IS ALPHA QUALITY SOFTWARE FOR RESEARCH PURPOSES ONLY. THIS IS NOT A PRODUCT.
YOU ARE RESPONSIBLE FOR COMPLYING WITH LOCAL LAWS AND REGULATIONS.
NO WARRANTY EXPRESSED OR IMPLIED.**

---

<img src="https://d1qb2nb5cznatu.cloudfront.net/startups/i/1061157-bc7e9bf3b246ece7322e6ffe653f6af8-medium_jpg.jpg?buster=1458363130" width="75"></img> <img src="https://cdn-images-1.medium.com/max/1600/1*C87EjxGeMPrkTuVRVWVg4w.png" width="225"></img>

[![openpilot tests](https://github.com/commaai/openpilot/workflows/openpilot%20tests/badge.svg?event=push)](https://github.com/commaai/openpilot/actions)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/commaai/openpilot.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/commaai/openpilot/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/commaai/openpilot.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/commaai/openpilot/context:python)
[![Language grade: C/C++](https://img.shields.io/lgtm/grade/cpp/g/commaai/openpilot.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/commaai/openpilot/context:cpp)
[![codecov](https://codecov.io/gh/commaai/openpilot/branch/master/graph/badge.svg)](https://codecov.io/gh/commaai/openpilot)
