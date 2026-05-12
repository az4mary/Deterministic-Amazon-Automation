# INSTRUCTIONS_3

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