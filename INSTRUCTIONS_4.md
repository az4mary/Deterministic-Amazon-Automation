# INSTRUCTIONS_4

## Current runtime patch status

```json
{
  "PATCH_SET_04": "PASS",
  "PATCH_SET_05": "PASS",
  "PATCH_SET_06": "PASS",
  "PATCH_SET_07": "PASS",
  "PATCH_SET_08": "PASS",
  "PATCH_SET_09": "PASS",
  "01A_runtime": "PASS",
  "STATE_16": "READY_FOR_STOP_AFTER_11_VALIDATION"
}
```

## Next validation

Run the `--resume --stop-after 11` validation from the successful `01A` state:

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_SELECTOR_TIMEOUT_MS="3000"
$env:BROWSER_COMPOSER_READY_TIMEOUT_MS="30000"
$env:BROWSER_SELECTOR_POLL_MS="500"
$env:BROWSER_RESPONSE_STABILIZE_SECONDS="180"
$env:BROWSER_RESPONSE_STABLE_REQUIRED="2"
$env:BROWSER_REQUIRE_JSON_CANDIDATE="1"
$env:BROWSER_REQUIRE_PARSEABLE_JSON="1"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --resume --stop-after 11
```

Expected success criteria:

```json
{
  "expected": [
    "resume starts after 01A",
    "01B completes",
    "steps 02 through 10 complete",
    "step 11 completes",
    "step 11 uses IMAGE_CONTEXT_JSON",
    "last_completed_step=11",
    "image_strategy_1 exists",
    "terminal OUTPUT/SUCCESS appears",
    "no orphaned Python process"
  ]
}
```