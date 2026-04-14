from datetime import datetime
import json
import re
from pathlib import Path

file_path = Path("workflow_orchestrator.py")
content = file_path.read_text()

FIND = r"""def json_log(event: str, **fields: Any) -> None:
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

# DRY RUN
matches = re.findall(FIND, content, re.MULTILINE)
print(f"Matches found: {len(matches)}")

if matches:
    updated = re.sub(FIND, REPLACE, content, flags=re.MULTILINE)
    file_path.write_text(updated)
    print("Patch applied.")
else:
    print("No match found. Aborting.")
