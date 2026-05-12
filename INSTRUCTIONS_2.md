# INSTRUCTIONS_2

ACTION:

- Reclassified the failure: `PATCH_SET_04` successfully localized the browser path, but `01A` runtime did **not** complete.
- Confirmed `workflow_state.json.outputs` is still empty, so no workflow step was persisted as completed.

## Diagnosis

Your diagnostics show the browser path is working up to assistant response detection:

```
Step started: 01A
Browser text execution started
Browser page ready
Browser payload built
Browser JSON attempt started
Browser prompt send started
Browser input box resolved
Browser prompt submission attempted
Browser assistant response wait started
Browser assistant response detected
```

The last phase reached was:

```
Browser assistant response detected
```

The phases not reached were:

```
Browser assistant response stabilized
Browser response received
Browser response parsed as JSON
Stopped after step 01A
OUTPUT/SUCCESS
```

So the current failure is **not** browser connection, login, selector discovery, prompt submission, or assistant-response creation. It is localized to **assistant response stabilization/capture**.

The second finding is also important: the browser did receive a 3,093-character assistant response, but the response was malformed JSON around:

```json
"sensor_size":"1/2.9""
```

That means after response capture is fixed, the next likely failure is JSON parsing unless we harden repair for doubled terminal quote characters.

---

# Revised status

```json
{
  "PATCH_SET_04": "PARTIAL_PASS",
  "stop_after_semantics": "LIKELY_FIXED",
  "runtime_01A": "FAIL",
  "failure_location": "assistant response stabilization/capture",
  "secondary_issue": "malformed JSON from model response",
  "STATE_16": "NOT_CONFIRMED",
  "next_patch_set": "PATCH_SET_05"
}
```

---

# PATCH_SET_05 — Browser response capture + JSON quote repair

## Purpose

Fix the two issues surfaced by `PATCH_SET_04`:

1. Prevent `send_prompt()` from waiting too long after an assistant response already exists.
2. Repair common malformed JSON caused by doubled terminal quote characters such as:

```json
"sensor_size":"1/2.9""
```

This patch does **not** add retry policy, self-healing, or workflow behavior changes.

---

## PATCH_05A — Add response stabilization controls

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_05A",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
```

### REPLACE WITH

```python
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "20"))
```

---

## PATCH_05B — Use bounded stabilization window after assistant response detection

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_05B",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        # Wait for streaming to settle to avoid capturing partial (invalid) JSON.
        stable_required = 3
        stable_count = 0
        last_text = ""
        deadline = time.time() + (self.action_timeout_ms / 1000.0)
```

### REPLACE WITH

```python
        # Wait for streaming to settle to avoid capturing partial (invalid) JSON.
        # This window starts only after an assistant response has been detected.
        # It must be shorter than the full browser action timeout so malformed JSON
        # can be captured, parsed, repaired, or retried instead of hanging at capture.
        stable_required = BROWSER_RESPONSE_STABLE_REQUIRED
        stable_count = 0
        last_text = ""
        deadline = time.time() + BROWSER_RESPONSE_STABILIZE_SECONDS
```

---

## PATCH_05C — Preserve latest non-empty assistant text before fallback return

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_05C",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
            current = assistant.inner_text(timeout=self.action_timeout_ms).strip()
            if current and current == last_text:
```

### REPLACE WITH

```python
            current = assistant.inner_text(timeout=self.action_timeout_ms).strip()
            if current:
                last_text = current
            if current and current == last_text:
```

### Important note

This exact patch may expose a logic issue because setting `last_text = current` immediately before comparing `current == last_text` makes the comparison always true. If your dry-run tool flags this as problematic, use the safer replacement below instead.

### SAFER REPLACEMENT

Use this replacement instead of the one above if applying manually:

```python
            current = assistant.inner_text(timeout=self.action_timeout_ms).strip()
            if current and current == last_text:
```

Replace the whole stabilization comparison block with:

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

If using the safer replacement, do **not** keep the old `else:` block beneath it.

---

## PATCH_05D — Repair doubled terminal quote in JSON strings

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_05D",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
def repair_common_json_glitches(json_text: str) -> str:
    # Fix the common inch-mark issue that breaks JSON strings, e.g.:
    # "sensor": "SONY Exmor IMX323 (1/2.9", 2.8µ pixel)"
    # becomes:
    # "sensor": "SONY Exmor IMX323 (1/2.9 inches, 2.8µ pixel)"
    json_text = re.sub(r'(\d)"\s*,\s*(\d)', r"\1 inches, \2", json_text)
    return json_text
```

### REPLACE WITH

```python
def repair_common_json_glitches(json_text: str) -> str:
    # Fix the common inch-mark issue that breaks JSON strings, e.g.:
    # "sensor": "SONY Exmor IMX323 (1/2.9", 2.8µ pixel)"
    # becomes:
    # "sensor": "SONY Exmor IMX323 (1/2.9 inches, 2.8µ pixel)"
    json_text = re.sub(r'(\d)"\s*,\s*(\d)', r"\1 inches, \2", json_text)

    # Fix doubled terminal quote characters inside JSON string values, e.g.:
    # "sensor_size":"1/2.9""
    # becomes a valid JSON string containing the inch quote:
    # "sensor_size":"1/2.9\""
    json_text = re.sub(r'(?<=\d)""(?=\s*[,}\]])', r'\\""', json_text)

    return json_text
```

---

# PATCH_SET_05 validation checkpoint

```json
{
  "patch_set_id": "PATCH_SET_05",
  "expected_behavior": "Assistant responses are captured after a bounded stabilization window, malformed doubled terminal quote JSON is repaired, and 01A either completes or fails with a parse/runtime error rather than hanging after assistant response detection.",
  "expected_present": {
    "BROWSER_RESPONSE_STABLE_REQUIRED": true,
    "BROWSER_RESPONSE_STABILIZE_SECONDS": true,
    "assistant_response_stabilization_deadline": true,
    "doubled terminal quote repair": true
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
    "Do not add retry or recovery policy beyond existing JSON retry loop",
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

## 2. Focused JSON repair test

```powershell
D:\TOOLS\Python314\python.exe - <<'PY'
import workflow_orchestrator as w

bad = '{"sensor_size":"1/2.9"","pixel_size":"2.8µ"}'
parsed, err, excerpt = w.try_parse_response_json(bad)

assert parsed is not None, err
assert parsed["sensor_size"] == '1/2.9"'
assert parsed["pixel_size"] == "2.8µ"

print("PATCH_05_JSON_REPAIR_OK")
print(parsed)
PY
```

## 3. Focused runtime test for `01A`

Use shorter stabilization and no JSON retries first:

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_RESPONSE_STABILIZE_SECONDS="20"
$env:BROWSER_RESPONSE_STABLE_REQUIRED="2"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

Expected result:

```json
{
  "expected": [
    "Step 01A runs",
    "assistant response is captured",
    "Browser response received appears",
    "Then either 01A completes or MODEL_OUTPUT_NOT_JSON fails fast",
    "No hang after Browser assistant response detected"
  ]
}
```

## 4. If 01A completes

Then run:

```powershell
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 11
```

Only run this after `--stop-after 01A` is clean.

---