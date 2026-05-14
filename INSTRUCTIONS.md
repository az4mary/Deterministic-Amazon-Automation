# INSTRUCTIONS

Since the current state is already at:

```json
{
  "last_completed_step": "12"
}
```

the next command should resume from `13` and run through `24`:

```powershell
$env:SKIP_IMAGES="0"
$env:IMAGE_REFERENCE_STRICT="1"
$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"
$env:BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS="900"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --resume --enable-image-generation
```

## Required full-run success criteria

Do not confirm until all of this is true:

```json
{
  "expected_terminal": "OUTPUT/SUCCESS",
  "expected_last_completed_step": "24",
  "expected_prompt_steps_complete": [
    "13", "15", "17", "19", "21", "23"
  ],
  "expected_generation_steps_complete": [
    "14", "16", "18", "20", "22", "24"
  ],
  "expected_generated_images": [
    "generated_image_1",
    "generated_image_2",
    "generated_image_3",
    "generated_image_4",
    "generated_image_5",
    "generated_image_6",
    "generated_image_7"
  ],
  "expected_image_files": [
    "output/generated_images/image_12.png",
    "output/generated_images/image_14.png",
    "output/generated_images/image_16.png",
    "output/generated_images/image_18.png",
    "output/generated_images/image_20.png",
    "output/generated_images/image_22.png",
    "output/generated_images/image_24.png"
  ],
  "expected_image_prompts_json_count": 7
}
```

## What happens if the full run fails?

Do **not** proceed to STATE 17.

Fix only the exact failed step, preserving the rest of the sequence.

```json
{
  "if_failure": {
    "step": "identify exact failing step",
    "action": "STOP and send report",
    "do_not": [
      "renumber validations",
      "rewrite prior patch sequence",
      "reopen PATCH_SET_02",
      "reopen PATCH_SET_03",
      "skip to bug logging"
    ]
  }
}
```

```json
{
  "required_files_after_run": [
    "output/logs/execution.jsonl",
    "output/workflow_state.json",
    "output/image_prompts.json",
    "output/generated_images directory listing"
  ]
}
```