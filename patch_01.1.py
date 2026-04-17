import argparse
import difflib
import re
import shutil
from pathlib import Path

FILE_PATH = Path("prompts.md")

# === ONLY EDIT THESE TWO ===
FIND = """"**Use the following PRODUCT DATA as seen in actual product label/box:**
**Product Name:** DASHCAM C1
**Brand:** ROAV by ANKER 
**Color:** Black
**Model:** R2110

**Features and Specifications:** found on actual product label/package
- Built-In Wi-Fi With App Support
- ANKER 2-Port USB Car Charger
- Exmor IMX 323 Advanced SONY Sensor
- FHD 1080P Crystal-Clear Definition
- SD Free 32GB Card
- SONY Exmor IMX323 sensor has Nighthawk Vision™ to clearly capture speeding license plates — especially at night.
- 145° wide-angle view simultaneously records up to 4 lanes of traffic.
- Gravity sensor monitors and instantly starts recording when sudden stops or collisions occur.
- Connect to DashCam's Wi-Fi to seamlessly review, download, and share videos via the Roav app.
- Chipset: Novatek NT96658 
- Wi-Fi: Built-in 
- Sensor: SONY Exmor IMX323 (1/2.9", 2.8µ pixel) 
- Motion Sensor: G-Sensor 
- Video: 1080P 30FPS (1920×1080) 
- Night Vision: WDR Superior Night Vision 
- Operating Temperatures: 14°F to 149°F 
- Screen: Illuminated 2.4" 
- Screen Lens: F1.8 with 6 high-quality glass elements and 145° viewing angle 
- Battery: 470mAh Li-polymer battery capable of operating in high and low temperatures.
- Download the Roav Dashcam app from the App Store or Google Play.

**Box Contents:**
- DashCam C1
- Anker 2-Port USB car charger
- Micro-USB charging cable
- 32GB card
- Owner's Manual"""

REPLACE = """"**Use the following PRODUCT DATA as provided in the current input bundle:**
- Product metadata
- Packaging text
- Specification sheets
- URLs
- Documents
- Chat text
- Product label images
- Product box images

Extract only what is present in the provided sources.
Do not assume a category or invent missing data."""
# ===========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    content = FILE_PATH.read_text(encoding="utf-8")

    pattern = re.compile(re.escape(FIND), re.MULTILINE)
    matches = list(pattern.finditer(content))

    print(f"Matches found: {len(matches)}")

    if len(matches) == 0:
        print("❌ Abort: no matches found")
        return

    updated = pattern.sub(REPLACE, content)  # replaces ALL exact matches

    diff = difflib.unified_diff(
        content.splitlines(True),
        updated.splitlines(True),
        fromfile=str(FILE_PATH),
        tofile=str(FILE_PATH) + " (patched)",
    )
    print("".join(diff))

    if not args.apply:
        print("Dry run only. No changes made.")
        return

    FILE_PATH.write_text(updated, encoding="utf-8")
    print(f"✅ Patch applied.")

if __name__ == "__main__":
    main()
