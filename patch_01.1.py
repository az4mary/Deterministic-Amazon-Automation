import argparse
import difflib
import re
import shutil
from pathlib import Path

FILE_PATH = Path("prompts.md")

# === ONLY EDIT THESE TWO ===
FIND = """"{
 "reference_tag": "",
 "product_category": "",
 "product_profile": {
   "brand": "",
   "product_name": "",
   "model": "",
   "color": ""
 },

 "core_features": [],

 "attributes": {
   "attribute_name": "value"
 },

 "package_contents": [],

 "product_summary": ""
}"""

REPLACE = """"{
 "reference_tag": "",
 "product_category": "",
 "product_profile": {
   "brand": "",
   "product_name": "",
   "model": "",
   "color": ""
 },

 "core_features": [],

 "attributes": {
   "attribute_name": "value"
 },

 "additional_attributes": {
   "attribute_name": "value"
 },

 "package_contents": [],

 "product_summary": ""
}"""
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
