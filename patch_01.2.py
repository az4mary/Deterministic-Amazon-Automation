import argparse
import difflib
import re
import shutil
from pathlib import Path

FILE_PATH = Path("workflow_orchestrator.py")

# === ONLY EDIT THESE TWO ===
FIND = """def json_log(event: str, **fields: Any) -> None:
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": TRACE_ID,
        "span_id": next_span_id(),
        "event": event,
        **fields,
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "execution.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")"""

REPLACE = """def json_log(
    level: str,
    message: str,
    stage: str,
    status: str,
    context: Optional[Dict[str, Any]] = None,
    progress_percent: Optional[int] = None,
    current_step: Optional[int] = None,
    total_steps: Optional[int] = None,
    **fields: Any,
) -> None:
    record: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "level": level,
        "message": message,
        "service": "workflow_orchestrator",
        "stage": stage,
        "status": status,
        "trace_id": TRACE_ID,
        "span_id": next_span_id(),
        "context": context or {},
    }

    if progress_percent is not None:
        record["progress_percent"] = int(progress_percent)
        record["current_step"] = current_step
        record["total_steps"] = total_steps

    record.update(fields)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "execution.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")"""
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
