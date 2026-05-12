# INSTRUCTIONS_4

- Reclassified the latest run as **runtime fail, no false completion**.
- Confirmed this was **not** the requested `-resume --stop-after 11` validation; it was another focused `01A` runtime attempt.

## Current diagnosis

`PATCH_SET_07` did its intended first job:

```json
{
  "captured_thinking_as_final_output": false,
  "browser_assistant_response_not_ready_logged": true,
  "orphaned_python_process": false
}
```

But the run still failed because the orchestrator accepted **partial JSON-like content** before the final assistant message became complete:

```
MODEL_OUTPUT_NOT_JSON
parse_error=Unterminated string starting at: line 11 column 1
```

The terminal preview began with JSON, not `Thinking`, which means the final-content gate worked against the placeholder but was still too weak: it only required a JSON candidate, not parseable JSON.

`workflow_state.json` correctly shows:

```json
{
  "outputs": {},
  "last_completed_step": null,
  "has_prompt_01A": false
}
```

So no failed partial output was persisted as completed.

---

# Revised status

```json
{
  "PATCH_SET_07": "PARTIAL_PASS",
  "static_helper_validation": "PASS",
  "thinking_placeholder_gate": "PASS",
  "runtime_01A": "FAIL",
  "current_failure_location": "partial JSON accepted before complete parseable response",
  "STATE_16": "NOT_CONFIRMED",
  "next_patch_set": "PATCH_SET_09"
}
```

Do **not** proceed to `--stop-after 11` yet.

---

# PATCH_SET_09 — Parseable JSON final gate

## Purpose

Require the assistant response to be **parseable JSON after existing repairs** before `send_prompt()` can treat it as stable/final.

This patch does **not** change:

- prompts
- schemas
- retry policy
- output persistence
- image routing
- stop-after semantics
- fail-fast behavior

---

## PATCH_09A — Add parseable-JSON readiness control

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_09A",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "60"))
BROWSER_REQUIRE_JSON_CANDIDATE = os.getenv("BROWSER_REQUIRE_JSON_CANDIDATE", "1") == "1"
```

### REPLACE WITH

```python
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "180"))
BROWSER_REQUIRE_JSON_CANDIDATE = os.getenv("BROWSER_REQUIRE_JSON_CANDIDATE", "1") == "1"
BROWSER_REQUIRE_PARSEABLE_JSON = os.getenv("BROWSER_REQUIRE_PARSEABLE_JSON", "1") == "1"
```

---

## PATCH_09B — Require parseable JSON in `assistant_response_ready(...)`

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_09B",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
def assistant_response_ready(text: str) -> bool:
    if is_transient_assistant_text(text):
        return False
    if BROWSER_REQUIRE_JSON_CANDIDATE and not has_json_candidate(text):
        return False
    return True
```

### REPLACE WITH

```python
def assistant_response_ready(text: str) -> bool:
    if is_transient_assistant_text(text):
        return False
    if BROWSER_REQUIRE_JSON_CANDIDATE and not has_json_candidate(text):
        return False
    if BROWSER_REQUIRE_PARSEABLE_JSON:
        parsed, _err, _excerpt = try_parse_response_json(text)
        if parsed is None:
            return False
    return True
```

---

## PATCH_09C — Add parseable-gate diagnostics

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_09C",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
                            "requires_json_candidate": BROWSER_REQUIRE_JSON_CANDIDATE,
```

### REPLACE WITH

```python
                            "requires_json_candidate": BROWSER_REQUIRE_JSON_CANDIDATE,
                            "requires_parseable_json": BROWSER_REQUIRE_PARSEABLE_JSON,
                            "has_json_candidate": has_json_candidate(current),
```

---

# PATCH_SET_09 validation checkpoint

```json
{
  "patch_set_id": "PATCH_SET_09",
  "expected_behavior": "Assistant placeholder text is ignored, partial JSON-like content is not accepted as final, and only parseable JSON after existing repair logic can stabilize as the browser response.",
  "expected_present": {
    "BROWSER_REQUIRE_PARSEABLE_JSON": true,
    "parsed, _err, _excerpt = try_parse_response_json(text)": true,
    "requires_parseable_json": true,
    "has_json_candidate": true
  },
  "expected_terminal_success_fields": [
    "timestamp",
    "level",
    "status",
    "trace_id",
    "span_id",
    "output_hash"
  ],
  "forbidden_changes": [
    "Do not modify prompts.md",
    "Do not change output schemas",
    "Do not change image context router behavior",
    "Do not change image step numbering",
    "Do not change JSON retry policy",
    "Do not remove fail-fast behavior"
  ]
}
```

---

# Validation commands

## 1. Clean runtime artifacts

Remove the stray bytecode artifact from the workspace:

```powershell
Remove-Item -LiteralPath "__pycache__\workflow_orchestrator.cpython-314.pyc" -ErrorAction SilentlyContinue
```

## 2. Compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

## 3. Focused helper validation

```powershell
D:\TOOLS\Python314\python.exe - <<'PY'
import workflow_orchestrator as w

assert w.assistant_response_ready("Thinking") is False
assert w.assistant_response_ready('{"reference_tag": ""') is False
assert w.assistant_response_ready('{"reference_tag": ""}') is True

bad_but_repairable = '{"sensor_size":"1/2.9"","pixel_size":"2.8µ"}'
assert w.assistant_response_ready(bad_but_repairable) is True

print("PATCH_09_PARSEABLE_GATE_HELPER_OK")
PY
```

## 4. Focused runtime test

Use a longer stabilization window. The previous `60s` window was too short for this browser/model path.

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_SELECTOR_TIMEOUT_MS="3000"
$env:BROWSER_COMPOSER_READY_TIMEOUT_MS="30000"
$env:BROWSER_SELECTOR_POLL_MS="500"
$env:BROWSER_RESPONSE_STABILIZE_SECONDS="180"
$env:BROWSER_RESPONSE_STABLE_REQUIRED="2"
$env:BROWSER_REQUIRE_JSON_CANDIDATE="1"
$env:BROWSER_REQUIRE_PARSEABLE_JSON="1"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

Acceptable outcomes:

```json
{
  "acceptable_outcomes": [
    "Browser assistant response not ready appears for Thinking",
    "Partial JSON-like content is not accepted as final",
    "Browser response parsed as JSON appears",
    "Completed step 01A appears",
    "Stopped after step 01A appears",
    "OUTPUT/SUCCESS appears",
    "last_completed_step=01A",
    "prompt_01A exists"
  ],
  "unacceptable_outcomes": [
    "actual: Thinking",
    "parse error caused by partial JSON before stabilization deadline",
    "timeout after Browser assistant response detected",
    "orphaned Python process",
    "partial completed state without prompt_01A"
  ]
}
```