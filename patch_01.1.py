from __future__ import annotations

import argparse
import difflib
import re
import shutil
from pathlib import Path


TARGET_FILE = Path("workflow_orchestrator.py")

FIND = """import time"""

REPLACE = """import time
from datetime import datetime, timezone"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to disk")
    args = parser.parse_args()

    if not TARGET_FILE.exists():
        raise FileNotFoundError(f"Target file not found: {TARGET_FILE}")

    original = TARGET_FILE.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(FIND), flags=re.MULTILINE)

    matches = list(pattern.finditer(original))
    print(f"Matches found: {len(matches)}")

    if len(matches) == 0:
        print("No match found. Aborting.")
        return 1

    if len(matches) > 1:
        print("Multiple matches found. Aborting to avoid accidental mass edit.")
        return 1

    updated = pattern.sub(REPLACE, original, count=1)

    if original == updated:
        print("Matched text found, but replacement produced no change.")
        return 1

    diff = difflib.unified_diff(
        original.splitlines(True),
        updated.splitlines(True),
        fromfile=str(TARGET_FILE),
        tofile=f"{TARGET_FILE} (patched)",
    )
    print("".join(diff))

    if not args.apply:
        print("Dry run only. No files were changed.")
        return 0

    backup = TARGET_FILE.with_suffix(TARGET_FILE.suffix + ".bak")
    shutil.copy2(TARGET_FILE, backup)
    TARGET_FILE.write_text(updated, encoding="utf-8")
    print(f"Patch applied. Backup saved to: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
