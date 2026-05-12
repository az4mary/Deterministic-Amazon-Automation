# INSTRUCTIONS_3

`PATCH_SET_06` did its job: selector resolution no longer hangs. The new failure is a final-content gate problem—`send_prompt()` accepts the transient “Thinking” placeholder as the assistant response before the real JSON appears.

- Reclassified `PATCH_SET_06` as **PASS for selector-resolution objective**.
- Confirmed the current blocker has moved forward: the browser no longer hangs at composer detection, and the run now reaches prompt submission, assistant detection, response capture, parse failure, and terminal `OUTPUT/FAILED`.

## Current diagnosis

`PATCH_SET_06` fixed the immediate blocker:

```
Browser prompt send started
Browser input selector matched
Browser input box resolved
Browser prompt submission attempted
Browser assistant response wait started
Browser assistant response detected
Browser assistant response stabilized
Browser response received
Browser response JSON parse failed
OUTPUT/FAILED
```

That is a valid fast structured failure path, not a hang.

The newly surfaced issue is different:

```
MODEL_OUTPUT_NOT_JSON
actual: Thinking
```

The orchestrator captured the transient ChatGPT “Thinking” placeholder as if it were the final assistant response. After the model thinking phase ended, the real assistant response appeared in the browser and was around `2924` characters, but the orchestrator had already failed fast on the placeholder.

`workflow_state.json` correctly shows no completed step and no `prompt_01A`, so the failed run did not falsely persist a completed workflow step.

---

# Revised status

```json
{
  "PATCH_SET_06": "PASS",
  "selector_resolution": "PASS",
  "runtime_01A": "FAIL_FAST",
  "current_failure_location": "assistant final-content gating",
  "root_issue": "transient Thinking placeholder accepted before final JSON response",
  "STATE_16": "NOT_CONFIRMED",
  "next_patch_set": "PATCH_SET_07"
}
```

---

# PATCH_SET_07 — Assistant final-content gate

## Purpose

Prevent `send_prompt()` from accepting transient assistant placeholder text such as:

```
Thinking
```

as the final model output.

This patch does **not** change prompts, schemas, retry policy, output persistence, image routing, or fail-fast behavior.

---

## PATCH_07A — Add final-content gate controls

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_07A",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
BROWSER_SELECTOR_TIMEOUT_MS = int(os.getenv("BROWSER_SELECTOR_TIMEOUT_MS", "5000"))
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "20"))
```

### REPLACE WITH

```python
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
BROWSER_SELECTOR_TIMEOUT_MS = int(os.getenv("BROWSER_SELECTOR_TIMEOUT_MS", "5000"))
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "60"))
BROWSER_REQUIRE_JSON_CANDIDATE = os.getenv("BROWSER_REQUIRE_JSON_CANDIDATE", "1") == "1"
```

---

## PATCH_07B — Add assistant response readiness helpers

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_07B",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
def repair_unescaped_quotes(json_text: str) -> str:
```

### REPLACE WITH

```python
def is_transient_assistant_text(text: str) -> bool:
    stripped = (text or "").strip()
    lowered = stripped.lower().strip(".… ")

    if not stripped:
        return True

    if stripped.lstrip().startswith("{") or stripped.lstrip().startswith("["):
        return False

    transient_values = {
        "thinking",
        "thinking...",
        "thinking…",
    }

    return lowered in transient_values

def has_json_candidate(text: str) -> bool:
    normalized = normalize_json_text(text or "")
    return "{" in normalized and "}" in normalized

def assistant_response_ready(text: str) -> bool:
    if is_transient_assistant_text(text):
        return False
    if BROWSER_REQUIRE_JSON_CANDIDATE and not has_json_candidate(text):
        return False
    return True

def repair_unescaped_quotes(json_text: str) -> str:
```

---

## PATCH_07C — Ignore transient assistant placeholder during stabilization

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_07C",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
            current = assistant.inner_text(timeout=self.action_timeout_ms).strip()
            if current:
                if current == last_text:
                    stable_count += 1
                    if stable_count >= stable_required:
                        json_log(
                            level="DEBUG",
                            message="Browser assistant response stabilized",
                            stage="PROCESSING",
                            status="IN_PROGRESS",
                            context={
                                "operation": "assistant_response_stabilized",
                                "response_chars": len(current),
                                "stable_count": stable_count,
                            },
                        )
                        return current
                else:
                    stable_count = 0
                    last_text = current
            page.wait_for_timeout(500)
```

### REPLACE WITH

```python
            current = assistant.inner_text(timeout=self.action_timeout_ms).strip()
            if current:
                if not assistant_response_ready(current):
                    last_text = current
                    stable_count = 0
                    json_log(
                        level="DEBUG",
                        message="Browser assistant response not ready",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "assistant_response_not_ready",
                            "response_chars": len(current),
                            "response_excerpt": current[:120],
                            "requires_json_candidate": BROWSER_REQUIRE_JSON_CANDIDATE,
                        },
                    )
                    page.wait_for_timeout(500)
                    continue

                if current == last_text:
                    stable_count += 1
                    if stable_count >= stable_required:
                        json_log(
                            level="DEBUG",
                            message="Browser assistant response stabilized",
                            stage="PROCESSING",
                            status="IN_PROGRESS",
                            context={
                                "operation": "assistant_response_stabilized",
                                "response_chars": len(current),
                                "stable_count": stable_count,
                            },
                        )
                        return current
                else:
                    stable_count = 0
                    last_text = current
            page.wait_for_timeout(500)
```

---

# PATCH_SET_07 validation checkpoint

```json
{
  "patch_set_id": "PATCH_SET_07",
  "expected_behavior": "Assistant placeholder text such as Thinking is ignored during stabilization; final JSON-like content is required before response capture succeeds.",
  "expected_present": {
    "BROWSER_REQUIRE_JSON_CANDIDATE": true,
    "is_transient_assistant_text": true,
    "has_json_candidate": true,
    "assistant_response_ready": true,
    "Browser assistant response not ready": true
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

## 1. Compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

## 2. Focused helper test

```powershell
D:\TOOLS\Python314\python.exe - <<'PY'
import workflow_orchestrator as w

assert w.is_transient_assistant_text("Thinking") is True
assert w.assistant_response_ready("Thinking") is False
assert w.has_json_candidate('{"reference_tag": ""}') is True
assert w.assistant_response_ready('{"reference_tag": ""}') is True

print("PATCH_07_HELPER_TEST_OK")
PY
```

## 3. Focused runtime test

Use this first:

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_SELECTOR_TIMEOUT_MS="3000"
$env:BROWSER_RESPONSE_STABILIZE_SECONDS="60"
$env:BROWSER_RESPONSE_STABLE_REQUIRED="2"
$env:BROWSER_REQUIRE_JSON_CANDIDATE="1"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

Acceptable outcomes:

```json
{
  "acceptable_outcomes": [
    "Browser assistant response not ready appears for Thinking",
    "Browser response received contains final response, not Thinking",
    "Then either 01A completes or fails fast with MODEL_OUTPUT_NOT_JSON on the final assistant response",
    "No timeout after Browser response detected",
    "No orphaned Python process"
  ],
  "unacceptable_outcomes": [
    "actual: Thinking",
    "timeout after Browser assistant response detected",
    "orphaned Python process",
    "partial completed state without prompt_01A"
  ]
}
```

## Decision

Apply `PATCH_SET_07` next. This is the correct runtime-control fix before attempting `--stop-after 11`.