# INSTRUCTIONS

- Confirmed the full workflow **mechanically completed** through step `24`.
- Confirmed the new issue is **runtime pacing / model-overlap**, not step execution failure.

SEARCH VALIDATION RESULT:

- The run completed with `exit_status=0`, `last_completed_step=24`, all seven `generated_image_N` entries present, `image_prompts_json_count=7`, and all generated image files present: `image_12.png`, `image_14.png`, `image_16.png`, `image_18.png`, `image_20.png`, `image_22.png`, and `image_24.png`.
- The same result file records the observed defect: the script sends the next prompt while the current image is still visibly generating, leading to simultaneous image generations and degraded output quality.
- `workflow_state.json` confirms successful persistence through the image workflow, including generated image outputs and final step progression, but this does not invalidate the quality/pacing defect.
- The script already has `TEXT_STEP_WAIT_SECONDS` and `IMAGE_STEP_WAIT_SECONDS`, but their current defaults are `0`, so the built-in `apply_step_wait(...)` function effectively provides no model cool-down unless manually overridden.

VALIDATED DECISION:

```json
{
  "STATE_16": "FULL_RUN_MECHANICAL_PASS_BUT_NOT_CONFIRMED",
  "reason": "Execution completed, but automated browser workflow can overlap active model generations and degrade images.",
  "STATE_17_ALLOWED": false,
  "next_patch": "PATCH_10K",
  "patch_scope": "step pacing / model cooldown only",
  "do_not_change": [
    "image context routing",
    "prompt docs",
    "browser image capture",
    "adapter handoff",
    "step numbering",
    "output schemas"
  ]
}
```

OUTPUT:

# Current status

The script now proves:

```json
{
  "full_execution_through_24": "PASS",
  "all_7_image_prompt_records": "PASS",
  "all_7_generated_image_records": "PASS",
  "all_7_image_files": "PASS",
  "terminal_OUTPUT_SUCCESS": "PASS",
  "image_quality_pacing": "FAIL / NEEDS_HARDENING"
}
```

For an unmonitored browser/model workflow, **zero wait between text and image jobs is too aggressive**, especially after generated-image capture from a `canvas`. The script can capture/persist an image while the UI/model is still settling, then immediately submit another prompt. That creates exactly the behavior you observed: multiple visible generations, degraded output, and pressure on context/model stability.

So the next fix is not another selector patch. It is a **pacing patch**.

---

# PATCH_10K — Enforce model cooldown between steps

## Purpose

Prevent overlapping model operations by enforcing:

```json
{
  "text_step_wait_seconds": 300,
  "image_generation_step_wait_seconds": 600
}
```

That matches your operating rule:

- **5 minutes after each text generation**
- **10 minutes after each image generation**

This patch uses the existing `apply_step_wait(...)` hook and changes only the wait behavior.

---

## PATCH_10K1 — Change default step wait values

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10K1",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
TEXT_STEP_WAIT_SECONDS = int(os.getenv("TEXT_STEP_WAIT_SECONDS", "0"))
IMAGE_STEP_WAIT_SECONDS = int(os.getenv("IMAGE_STEP_WAIT_SECONDS", "0"))
```

### REPLACE WITH

```python
TEXT_STEP_WAIT_SECONDS = int(os.getenv("TEXT_STEP_WAIT_SECONDS", "300"))
IMAGE_STEP_WAIT_SECONDS = int(os.getenv("IMAGE_STEP_WAIT_SECONDS", "600"))
```

---

## PATCH_10K2 — Add explicit cooldown logging

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10K2",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
def apply_step_wait(step_kind: str) -> None:
    global SYNTHETIC_DURATION_MS

    if step_kind == "text":
        time.sleep(TEXT_STEP_WAIT_SECONDS)
        SYNTHETIC_DURATION_MS += TEXT_STEP_WAIT_SECONDS * 1000
    elif step_kind == "image_generate":
        time.sleep(IMAGE_STEP_WAIT_SECONDS)
        SYNTHETIC_DURATION_MS += IMAGE_STEP_WAIT_SECONDS * 1000
```

### REPLACE WITH

```python
def apply_step_wait(step_kind: str) -> None:
    global SYNTHETIC_DURATION_MS

    wait_seconds = 0

    if step_kind == "text":
        wait_seconds = TEXT_STEP_WAIT_SECONDS
    elif step_kind == "image_generate":
        wait_seconds = IMAGE_STEP_WAIT_SECONDS

    if wait_seconds <= 0:
        return

    json_log(
        level="INFO",
        message="Model cooldown wait started",
        stage="PROCESSING",
        status="IN_PROGRESS",
        context={
            "operation": "model_cooldown_wait",
            "step_kind": step_kind,
            "wait_seconds": wait_seconds,
        },
    )

    time.sleep(wait_seconds)
    SYNTHETIC_DURATION_MS += wait_seconds * 1000

    json_log(
        level="INFO",
        message="Model cooldown wait completed",
        stage="PROCESSING",
        status="IN_PROGRESS",
        context={
            "operation": "model_cooldown_complete",
            "step_kind": step_kind,
            "wait_seconds": wait_seconds,
        },
    )
```

---

# PATCH_10K validation

## K-Validation 1 — compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```
PASS / no output
```

## K-Validation 2 — static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    'TEXT_STEP_WAIT_SECONDS = int(os.getenv("TEXT_STEP_WAIT_SECONDS", "300"))',
    'IMAGE_STEP_WAIT_SECONDS = int(os.getenv("IMAGE_STEP_WAIT_SECONDS", "600"))',
    "Model cooldown wait started",
    "Model cooldown wait completed",
    "model_cooldown_wait",
    "model_cooldown_complete",
]

for marker in required:
    assert marker in text, marker

print("PATCH_10K_MODEL_COOLDOWN_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_10K_MODEL_COOLDOWN_STATIC_OK
```

## K-Validation 3 — fast functional wait test

This does **not** wait 5/10 minutes. It overrides waits to 60/120 second to prove the hook works.

```powershell
$env:TEXT_STEP_WAIT_SECONDS="60"
$env:IMAGE_STEP_WAIT_SECONDS="120"

@'
import workflow_orchestrator as w

start = w.SYNTHETIC_DURATION_MS
w.apply_step_wait("text")
after_text = w.SYNTHETIC_DURATION_MS
w.apply_step_wait("image_generate")
after_image = w.SYNTHETIC_DURATION_MS

assert after_text - start == 60000, (start, after_text)
assert after_image - after_text == 120000, (after_text, after_image)

print("PATCH_10K_MODEL_COOLDOWN_FUNCTIONAL_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_10K_MODEL_COOLDOWN_FUNCTIONAL_OK
```

---

CONFIRMATION REQUIRED:
YES

# STATE full-run validation after PATCH_10K

Because the existing full run completed **without enforced cooldown**, it should not be used as the final quality pass.

Run a clean full execution after `PATCH_10K`:

```powershell
$env:SKIP_IMAGES="0"
$env:IMAGE_REFERENCE_STRICT="1"
$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"
$env:BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS="900"
$env:BROWSER_FORCE_ROOT_NEW_CHAT="1"
$env:BROWSER_NEW_CHAT_READY_TIMEOUT_MS="30000"

# Optional explicit values; these are now defaults after PATCH_10K.
$env:TEXT_STEP_WAIT_SECONDS="300"
$env:IMAGE_STEP_WAIT_SECONDS="600"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --enable-image-generation
```

Expected success criteria:

```json
{
  "expected_terminal": "OUTPUT/SUCCESS",
  "expected_last_completed_step": "24",
  "expected_image_prompts_json_count": 7,
  "expected_generated_images_present": [
    "generated_image_1",
    "generated_image_2",
    "generated_image_3",
    "generated_image_4",
    "generated_image_5",
    "generated_image_6",
    "generated_image_7"
  ],
  "expected_generated_files_present": [
    "output/generated_images/image_12.png",
    "output/generated_images/image_14.png",
    "output/generated_images/image_16.png",
    "output/generated_images/image_18.png",
    "output/generated_images/image_20.png",
    "output/generated_images/image_22.png",
    "output/generated_images/image_24.png"
  ],
  "expected_log_evidence": [
    "Model cooldown wait started",
    "Model cooldown wait completed",
    "Workflow completed successfully"
  ],
  "expected_quality_condition": [
    "No visible simultaneous image generations",
    "No prompt submitted while prior image generation is still visibly active"
  ]
}
```