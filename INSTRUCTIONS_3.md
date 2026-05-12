# INSTRUCTIONS_3

- Confirmed `PATCH_05D` is complete, committed, pushed, and clean.
- Confirmed the updated script now includes:
    - bounded response stabilization controls,
    - safer latest-assistant-text preservation,
    - doubled terminal quote repair inside `repair_common_json_glitches(...)`.

## Decision

`PATCH_05D = CONFIRMED`

Proceed to the focused `--stop-after 01A` runtime test.

Do **not** proceed to full `--stop-after 11` yet. First validate that `01A` now either:

1. completes successfully, or
2. fails fast with structured `MODEL_OUTPUT_NOT_JSON`, rather than hanging after assistant response detection.

## Current PATCH_SET_05 status

```json
{
  "PATCH_05A": "PASS",
  "PATCH_05B": "PASS",
  "PATCH_05C": "PASS",
  "PATCH_05D": "PASS",
  "PATCH_SET_05": "AWAITING_RUNTIME_01A_VALIDATION"
}
```

## Run this next

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_RESPONSE_STABILIZE_SECONDS="20"
$env:BROWSER_RESPONSE_STABLE_REQUIRED="2"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

## Expected acceptable outcomes

```json
{
  "acceptable_outcomes": [
    "01A completes and state.last_completed_step becomes 01A",
    "01A fails fast with structured MODEL_OUTPUT_NOT_JSON",
    "execution.jsonl includes Browser response received",
    "execution.jsonl includes either Browser response parsed as JSON or Browser response JSON parse failed",
    "no hang after Browser assistant response detected"
  ],
  "unacceptable_outcomes": [
    "timeout after Browser assistant response detected",
    "no Browser response received log",
    "orphaned Python process",
    "partial state mutation without terminal event"
  ]
}
```