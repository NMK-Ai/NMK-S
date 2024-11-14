#!/usr/bin/env python3
import json
import os
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

from openpilot.common.basedir import BASEDIR
from openpilot.selfdrive.ui.tests.test_translations import UNFINISHED_TRANSLATION_TAG
from openpilot.selfdrive.ui.update_translations import LANGUAGES_FILE, TRANSLATIONS_DIR

TRANSLATION_TAG = "<translation"
BADGE_HEIGHT = 40

def create_local_badge(language: str, percent_finished: int, unfinished_count: int, output_path: str):
    try:
        # تحديد لون الشارة بناءً على نسبة الإنجاز
        color = "green" if percent_finished == 100 else "orange" if percent_finished > 90 else "red"

        # إعداد نص الشارة
        badge_text = f"{language}: {percent_finished}% complete ({unfinished_count} unfinished)"

        # رسم الشارة باستخدام matplotlib
        plt.figure(figsize=(6, 1))
        plt.text(0.5, 0.5, badge_text, fontsize=12, ha='center', va='center', color='white', bbox=dict(facecolor=color, edgecolor='black'))
        plt.axis('off')

        # حفظ الشارة كملف SVG
        plt.savefig(output_path, format='svg')
        plt.close()
        print(f"Badge for {language} created successfully at {output_path}")
    except Exception as e:
        print(f"Error creating badge for {language}: {e}")

if __name__ == "__main__":
    try:
        with open(LANGUAGES_FILE) as f:
            translation_files = json.load(f)
    except FileNotFoundError:
        print(f"Error: languages.json not found at {LANGUAGES_FILE}")
        exit(1)

    for name, file in translation_files.items():
        try:
            file_path = os.path.join(TRANSLATIONS_DIR, f"{file}.ts")
            with open(file_path) as tr_f:
                tr_file = tr_f.read()

            total_translations = 0
            unfinished_translations = 0
            for line in tr_file.splitlines():
                if TRANSLATION_TAG in line:
                    total_translations += 1
                if UNFINISHED_TRANSLATION_TAG in line:
                    unfinished_translations += 1

            # حساب نسبة الإنجاز
            if total_translations == 0:
                print(f"No translations found in {file_path}")
                continue

            percent_finished = int(100 - (unfinished_translations / total_translations * 100))

            # تحديد مسار حفظ الشارة
            output_path = os.path.join(BASEDIR, f"badge_{name}.svg")

            # إنشاء الشارة محليًا
            create_local_badge(name, percent_finished, unfinished_translations, output_path)

        except Exception as e:
            print(f"Error processing {name}: {e}")
