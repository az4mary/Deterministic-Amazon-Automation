import argparse
import difflib
import re
import shutil
from pathlib import Path

FILE_PATH = Path("workflow_orchestrator.py")

# === ONLY EDIT THESE TWO ===
FIND = """HERE"""

REPLACE = """HERE"""
# ===========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    content = FILE_PATH.read_text(encoding="utf-8")

    pattern = re.compile(re.escape(FIND), re.MULTILINE)
    matches = list(pattern.finditer(content))

    print(f"Matches found: {len(matches)}")

    if len(matches) != 1:
        print("❌ Abort: match must be exactly 1")
        return

    updated = pattern.sub(REPLACE, content, count=1)

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
