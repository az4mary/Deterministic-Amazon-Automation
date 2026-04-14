from datetime import datetime
import json
import re
from pathlib import Path

file_path = Path("workflow_orchestrator.py")
content = file_path.read_text()

FIND = r"""def fail(code: str, message: str) -> None:
    json_log("fail_fast", error_code=code, message=message)
    raise SystemExit(f"{code}: {message}")"""

REPLACE = """def fail(code: str, message: str, field: str = "", expected: str = "", actual: str = "", stage: str = "VALIDATION") -> None:
    json_log(
        level="ERROR",
        message=message,
        stage=stage,
        status="FAILED",
        context={
            "error_code": code,
            "field": field,
            "expected": expected,
            "actual": actual,
        },
    )
    raise SystemExit(json.dumps({
        "error_code": code,
        "field": field,
        "expected": expected,
        "actual": actual,
        "trace_id": TRACE_ID
    }))"""

# DRY RUN
matches = re.findall(FIND, content, re.MULTILINE)
print(f"Matches found: {len(matches)}")

if matches:
    updated = re.sub(FIND, REPLACE, content, flags=re.MULTILINE)
    file_path.write_text(updated)
    print("Patch applied.")
else:
    print("No match found. Aborting.")
