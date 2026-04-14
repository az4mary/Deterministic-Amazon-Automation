from datetime import datetime
import json
import re
from pathlib import Path

file_path = Path("workflow_orchestrator.py")
content = file_path.read_text()

FIND = r"""import time"""

REPLACE = """import time
from datetime import datetime, timezone"""

# DRY RUN
matches = re.findall(FIND, content, re.MULTILINE)
print(f"Matches found: {len(matches)}")

if matches:
    updated = re.sub(FIND, REPLACE, content, flags=re.MULTILINE)
    file_path.write_text(updated)
    print("Patch applied.")
else:
    print("No match found. Aborting.")
