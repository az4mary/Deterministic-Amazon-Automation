# INSTRUCTIONS

CONFIRMATION REQUIRED: Before each 16 STEPS.

YES

- Preserve `PATCH_SET_11` as confirmed.
- Clean only generated validation/runtime artifacts.
- Proceed next with `PATCH_SET_12 — Flow browser image backend`.

`PATCH_SET_11` is now the stable base: `PATCH_11H` applied, committed, pushed, H-validations passed, clean `--stop-after 23` passed, and all seven prompt records now contain the spatial prompt contract fields.

---

# PATCH_12J — Reuse ChatGPT browser/CDP session for Flow adapter

Proceed with PATCH_12J.

There is no PATCH_12K yet. The next controlled action is to apply and validate PATCH_12J, because PATCH_SET_12 is currently blocked by the Playwright/CDP session ownership issue.

## Execute now

Apply:

```json
{
  "patch_id": "PATCH_12J",
  "purpose": "Reuse the active ChatGPT browser/CDP Playwright session inside FlowBrowserImageGenerationAdapter instead of starting a second sync Playwright session.",
  "target_file": "workflow_orchestrator.py",
  "scope": [
    "FlowBrowserImageGenerationAdapter.__init__",
    "FlowBrowserImageGenerationAdapter._page",
    "get_image_execution_adapter"
  ]
}
```

Then run:

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Then:

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "shared_browser_adapter: Optional[BrowserPromptExecutionAdapter] = None",
    "self.shared_browser_adapter = shared_browser_adapter",
    "Flow adapter reused shared browser session",
    "flow_reuse_shared_browser_session",
    "shared_browser_adapter=shared_browser_adapter",
]

for marker in required:
    assert marker in text, marker

print("PATCH_12J_SHARED_BROWSER_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Then:

```powershell
@'
import workflow_orchestrator as w

w.IMAGE_EXECUTION_ADAPTER = None
w.TEXT_EXECUTION_ADAPTER = w.BrowserPromptExecutionAdapter(
    w.BROWSER_CDP_URL,
    w.BROWSER_CHAT_URL,
    w.BROWSER_ACTION_TIMEOUT_MS,
)

adapter = w.get_image_execution_adapter()

assert isinstance(adapter, w.FlowBrowserImageGenerationAdapter), type(adapter)
assert adapter.shared_browser_adapter is w.TEXT_EXECUTION_ADAPTER
assert adapter.cdp_url == w.BROWSER_CDP_URL
assert adapter.flow_url == w.FLOW_URL

print("PATCH_12J_SHARED_BROWSER_ROUTING_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

## Then resume Validation 5

```powershell
$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"

$env:IMAGE_EXECUTION_BACKEND="flow_browser"
$env:FLOW_URL="https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28"
$env:FLOW_IMAGE_MODEL="Nano Banana 2"
$env:FLOW_MODEL_STRICT="1"
$env:FLOW_IMAGE_TIMEOUT_SECONDS="1200"
$env:FLOW_REFERENCE_STRICT="1"
$env:FLOW_ASPECT_RATIO="9:16"
$env:FLOW_OUTPUT_COUNT="1"

$env:TEXT_STEP_WAIT_SECONDS="300"
$env:IMAGE_STEP_WAIT_SECONDS="600"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --resume --enable-image-generation --stop-after 12
```

Expected result:

```json
{
  "PATCH_12J": "PASS",
  "Validation_5": "PASS",
  "last_completed_step": "12",
  "generated_image_1.generation_backend": "flow_browser",
  "generated_image_1.generation_model": "Nano Banana 2"
}
```

Send the updated files/logs after that.

# 1. Cleanup before PATCH_SET_12

## Purpose

Remove stale prompt/image/output artifacts so Flow validation cannot accidentally pass by reading old ChatGPT-generated or old prompt-validation files.

This cleanup does **not** touch source files.

## Safe cleanup command

Run from repo root:

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$archive = "output\_archive\pre_PATCH_SET_12_$stamp"

New-Item -ItemType Directory -Force $archive | Out-Null

Copy-Item output\workflow_state.json $archive -Force -ErrorAction SilentlyContinue
Copy-Item output\image_prompts.json $archive -Force -ErrorAction SilentlyContinue
Copy-Item output\image_content.json $archive -Force -ErrorAction SilentlyContinue
Copy-Item output\logs\execution.jsonl $archive -Force -ErrorAction SilentlyContinue

if (Test-Path output\generated_images) {
    Copy-Item output\generated_images "$archive\generated_images" -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-Item output\workflow_state.json -Force -ErrorAction SilentlyContinue
Remove-Item output\image_prompts.json -Force -ErrorAction SilentlyContinue
Remove-Item output\image_content.json -Force -ErrorAction SilentlyContinue
Remove-Item output\logs\execution.jsonl -Force -ErrorAction SilentlyContinue
Remove-Item output\generated_images\*.png -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force output\logs | Out-Null
New-Item -ItemType Directory -Force output\generated_images | Out-Null

git status --short
```

## Do not delete

```json
[
  "workflow_orchestrator.py",
  "docs/prompts.md",
  "data/raw_product_input.md",
  "data/images/",
  "docs/",
  "output/_archive/"
]
```

Expected after cleanup:

```json
{
  "source_files_preserved": true,
  "old_workflow_state_removed": true,
  "old_image_prompts_removed": true,
  "old_image_content_removed": true,
  "old_execution_log_removed": true,
  "old_generated_pngs_removed": true,
  "archive_created": true
}
```

---

# Next patch set

```json
{
  "patch_set_id": "PATCH_SET_12",
  "name": "Flow browser image backend",
  "purpose": "Route actual image-generation steps to Google Flow while keeping ChatGPT browser/CDP for text and image-prompt JSON generation.",
  "state": "STATE_16",
  "depends_on": [
    "PATCH_SET_10 browser/CDP stabilization",
    "PATCH_10K cooldown pacing",
    "PATCH_SET_11 spatial image prompt contract"
  ]
}
```

## Scope

Only these steps move to Flow:

```json
{
  "actual_image_generation_steps": ["12", "14", "16", "18", "20", "22", "24"]
}
```

These remain on ChatGPT browser/CDP:

```json
{
  "text_steps": ["01A", "01B", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
  "image_prompt_steps": ["11", "13", "15", "17", "19", "21", "23"]
}
```

## Do not touch

```json
[
  "docs/prompts.md PATCH_SET_11 contract",
  "schema_image_prompt spatial_scene_brief",
  "build_image_prompt_context",
  "build_image_generation_context",
  "cooldown defaults",
  "ChatGPT text/browser prompt execution",
  "step numbering",
  "image prompt JSON schema",
  "output image numbering"
]
```

---

# Required runtime model

```json
{
  "browser": "already launched",
  "auth": "already authenticated",
  "connection": "Chrome remote debugging / CDP",
  "text_backend": "ChatGPT browser",
  "image_prompt_backend": "ChatGPT browser",
  "image_generation_backend": "Google Flow browser",
  "flow_url": "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28"
}
```

## Required environment variables

```powershell
$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"

$env:IMAGE_EXECUTION_BACKEND="flow_browser"
$env:FLOW_URL="https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28"
$env:FLOW_IMAGE_MODEL="Nano Banana 2"
$env:FLOW_MODEL_STRICT="1"
$env:FLOW_IMAGE_TIMEOUT_SECONDS="1200"
$env:FLOW_REFERENCE_STRICT="1"
$env:FLOW_ASPECT_RATIO="9:16"
$env:FLOW_OUTPUT_COUNT="1"

$env:TEXT_STEP_WAIT_SECONDS="300"
$env:IMAGE_STEP_WAIT_SECONDS="600"
```

---

# PATCH_SET_12 breakdown

## 2. PATCH_12A — Add Flow backend configuration

Add constants:

```python
IMAGE_EXECUTION_BACKEND = os.getenv("IMAGE_EXECUTION_BACKEND", "chatgpt_browser").lower()
FLOW_URL = os.getenv("FLOW_URL", "https://labs.google/fx/tools/flow")
FLOW_IMAGE_MODEL = os.getenv("FLOW_IMAGE_MODEL", "Nano Banana 2")
FLOW_MODEL_STRICT = os.getenv("FLOW_MODEL_STRICT", "1") == "1"
FLOW_IMAGE_TIMEOUT_SECONDS = float(os.getenv("FLOW_IMAGE_TIMEOUT_SECONDS", "1200"))
FLOW_REFERENCE_STRICT = os.getenv("FLOW_REFERENCE_STRICT", "1") == "1"
FLOW_ASPECT_RATIO = os.getenv("FLOW_ASPECT_RATIO", "9:16")
FLOW_OUTPUT_COUNT = int(os.getenv("FLOW_OUTPUT_COUNT", "1"))
```

Expected validation markers:

```json
{
  "required": [
    "IMAGE_EXECUTION_BACKEND",
    "FLOW_URL",
    "FLOW_IMAGE_TIMEOUT_SECONDS",
    "FLOW_REFERENCE_STRICT",
    "FLOW_ASPECT_RATIO",
    "FLOW_OUTPUT_COUNT"
  ]
}
```

---

## 3. PATCH_12B — Split text adapter from image adapter

Current behavior: `call_image_generation(...)` uses the same execution adapter path.

Required behavior:

```python
def get_text_execution_adapter() -> PromptExecutionAdapter:
    ...

def get_image_execution_adapter() -> PromptExecutionAdapter:
    ...
```

Routing rule:

```json
{
  "if IMAGE_EXECUTION_BACKEND == flow_browser": "use FlowBrowserImageGenerationAdapter for image_generate steps",
  "else": "use current browser/OpenAI image adapter path"
}
```

`call_image_generation(...)` becomes:

```python
return get_image_execution_adapter().execute_image(
    prompt,
    size=size,
    generation_context=generation_context,
)
```

---

## 4. PATCH_12C — Add `FlowBrowserImageGenerationAdapter`

New class:

```python
class FlowBrowserImageGenerationAdapter(PromptExecutionAdapter):
    ...
```

Responsibilities:

```json
[
  "connect to existing Chrome over CDP",
  "find existing Flow tab or open Flow URL",
  "bring Flow page to front",
  "verify Flow UI is reachable",
  "submit image prompt",
  "attach reference images",
  "wait for generated output",
  "capture/download generated image",
  "return image_base64 + source_images_used + generation_backend"
]
```

This adapter should raise `NotImplementedError` for `execute_text(...)` because Flow must not handle text/JSON steps.

---

## 5. PATCH_12D — Flow page discovery / readiness

Add helper methods:

```python
def _page(self):
    ...

def _flow_ready(self, page) -> bool:
    ...

def _wait_for_flow_ready(self, page) -> None:
    ...
```

Page selection rule:

```json
{
  "prefer_existing_tab_containing": "labs.google/fx/tools/flow",
  "fallback": "open new page and navigate to FLOW_URL",
  "fail_if": "Flow page unavailable or Google auth/access blocks UI"
}
```

Expected failure codes:

```json
[
  "FLOW_PAGE_UNAVAILABLE",
  "FLOW_AUTH_REQUIRED",
  "FLOW_READY_TIMEOUT"
]
```

---

## 6. PATCH_12E — Reference-image upload / ingredient handoff

Use:

```python
generation_context["source_images"]
```

Strict rule:

```json
{
  "FLOW_REFERENCE_STRICT": true,
  "missing_source_images": "fail",
  "empty_source_images": "fail"
}
```

Implementation path:

```json
{
  "v1_strategy": "upload references every generation step",
  "reason": "more deterministic than relying on Flow asset-library @ references"
}
```

Add helper:

```python
def _attach_reference_images(self, page, source_images: List[str]) -> None:
    ...
```

Expected logs:

```json
[
  "Flow reference image attachment started",
  "Flow reference images attached"
]
```

---

## 7. PATCH_12F — Flow prompt submission

Before entering the prompt and clicking generate, `FlowBrowserImageGenerationAdapter` should run:

```python

```

Use the already generated `image_generation_prompt`.

Add helper:

```python
def _submit_flow_prompt(self, page, prompt: str) -> None:
    ...
```

Required behavior:

```json
{
  "target_model":"Nano Banana 2",
  "strict":"FLOW_MODEL_STRICT",
  "if_model_visible":"select Nano Banana 2",
  "if_model_not_visible_and_strict":"fail with FLOW_MODEL_NOT_AVAILABLE",
  "if_model_not_visible_and_not_strict":"log warning and continue with current Flow model"
}
```

Expected logs:

```json
[
"Flow model selection started",
"Flow model selected",
"Flow model selection skipped",
"Flow model not available"
]
```

Expected failure code:

```json
{
  "code":"FLOW_MODEL_NOT_AVAILABLE",
  "field":"FLOW_IMAGE_MODEL",
  "expected":"Nano Banana 2 visible/selectable in Flow model menu"
}
```

### 

---

## 8. PATCH_12G — Flow generated-image capture

Preferred capture order:

```json
[
  "download generated image if Flow exposes a download button",
  "extract data/blob image if accessible",
  "screenshot generated image tile/canvas as fallback"
]
```

Add helper:

```python
def _capture_flow_generated_image_base64(self, page) -> str:
    ...
```

Expected logs:

```json
[
  "Flow image generation wait started",
  "Flow generated image captured from download",
  "Flow generated image captured from image tile",
  "Flow generated image captured from canvas/screenshot"
]
```

Expected failure codes:

```json
[
  "FLOW_IMAGE_GENERATION_TIMEOUT",
  "FLOW_GENERATED_IMAGE_CAPTURE_FAILED"
]
```

---

## 9. PATCH_12H — Persist backend metadata

Generated image records should include:

```json
{
  "generation_backend":"flow_browser",
  "generation_model":"Nano Banana 2"
}
```

Do not remove existing fields:

```json
[
"image_number",
"image_type",
"saved_path",
"source_images_used",
"image_generation_prompt"
]
```

## 

---

## 10. PATCH_12I — Validation utilities and diagnostics

Add or require static validation that confirms:

```json
{
  "required_markers": [
    "FlowBrowserImageGenerationAdapter",
    "FLOW_IMAGE_MODEL",
	  "FLOW_MODEL_STRICT",
	  "Flow model selection started",
	  "FLOW_MODEL_NOT_AVAILABLE",
	  "generation_model"
    "IMAGE_EXECUTION_BACKEND",
    "get_image_execution_adapter",
    "FLOW_URL",
    "FLOW_REFERENCE_STRICT",
    "generation_backend"
  ],
  "forbidden_changes": [
    "renumbered image steps",
    "removed spatial_scene_brief",
    "changed prompt docs",
    "changed cooldown defaults",
    "routed image_prompt steps to Flow"
  ]
}
```

---

# PATCH_SET_12 validation sequence

## 11. Validation 1 — compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```
PASS / no output
```

---

## 12. Validation 2 — static marker validation

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "IMAGE_EXECUTION_BACKEND",
    "FLOW_URL",
    "FLOW_IMAGE_TIMEOUT_SECONDS",
    "FLOW_REFERENCE_STRICT",
    "FlowBrowserImageGenerationAdapter",
    "get_image_execution_adapter",
    "generation_backend",
]

for marker in required:
    assert marker in text, marker

for forbidden in [
    "IMAGE_PROMPT_STEP_IDS = {\"12\"",
    "spatial_scene_brief\" not in",
]:
    assert forbidden not in text, forbidden

print("PATCH_SET_12_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_SET_12_STATIC_OK
```

---

## 13. Validation 3 — adapter routing dry-run

No browser call. Mock Flow adapter.

Expected proof:

```json
{
  "step": "12",
  "image_generation_prompt": "comes from image_strategy_1",
  "generation_context": "passed to image adapter",
  "source_images": "present",
  "adapter": "FlowBrowserImageGenerationAdapter",
  "generation_backend": "flow_browser"
}
```

Expected terminal marker:

```
PATCH_SET_12_ROUTING_DRY_RUN_OK
```

---

## 14. Validation 4 — Flow UI smoke check

Browser/CDP only. No image generation required.

```powershell
$env:IMAGE_EXECUTION_BACKEND="flow_browser"
$env:FLOW_URL="https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"

D:\TOOLS\Python314\python.exe -c "import workflow_orchestrator as w; print('FLOW_SMOKE_IMPORT_OK')"
```

Then run the adapter’s page readiness check if exposed.

Expected:

```json
{
  "flow_page_reachable": true,
  "auth_ready": true,
  "project_or_prompt_ui_visible": true
}
```

---

## 15. Validation 5 — STEP 12 Flow actual generation smoke test

Clean output first, then run through step `12`.

```powershell
Remove-Item output\workflow_state.json -Force -ErrorAction SilentlyContinue
Remove-Item output\image_prompts.json -Force -ErrorAction SilentlyContinue
Remove-Item output\image_content.json -Force -ErrorAction SilentlyContinue
Remove-Item output\logs\execution.jsonl -Force -ErrorAction SilentlyContinue
Remove-Item output\generated_images\*.png -Force -ErrorAction SilentlyContinue

$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"
$env:IMAGE_EXECUTION_BACKEND="flow_browser"
$env:FLOW_URL="https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28"
$env:FLOW_IMAGE_TIMEOUT_SECONDS="1200"
$env:FLOW_REFERENCE_STRICT="1"
$env:FLOW_ASPECT_RATIO="9:16"
$env:FLOW_OUTPUT_COUNT="1"
$env:TEXT_STEP_WAIT_SECONDS="300"
$env:IMAGE_STEP_WAIT_SECONDS="600"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --enable-image-generation --stop-after 12
```

Expected:

```json
{
  "expected_terminal": "OUTPUT/SUCCESS",
  "expected_last_completed_step": "12",
  "expected_generated_image": "generated_image_1",
  "expected_file": "output/generated_images/image_12.png",
  "expected_backend": "flow_browser",
  "expected_model": "Nano Banana 2",
  "expected_source_images_used": "non-empty"
}
```

---

## 16. Validation 6 — full Flow run

Only after STEP `12` Flow smoke passes.

```powershell
Remove-Item output\workflow_state.json -Force -ErrorAction SilentlyContinue
Remove-Item output\image_prompts.json -Force -ErrorAction SilentlyContinue
Remove-Item output\image_content.json -Force -ErrorAction SilentlyContinue
Remove-Item output\logs\execution.jsonl -Force -ErrorAction SilentlyContinue
Remove-Item output\generated_images\*.png -Force -ErrorAction SilentlyContinue

$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"
$env:IMAGE_EXECUTION_BACKEND="flow_browser"
$env:FLOW_URL="https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28"
$env:FLOW_IMAGE_TIMEOUT_SECONDS="1200"
$env:FLOW_REFERENCE_STRICT="1"
$env:FLOW_ASPECT_RATIO="9:16"
$env:FLOW_OUTPUT_COUNT="1"
$env:TEXT_STEP_WAIT_SECONDS="300"
$env:IMAGE_STEP_WAIT_SECONDS="600"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --enable-image-generation
```

Expected final checkpoint:

```json
{
  "expected_terminal": "OUTPUT/SUCCESS",
  "expected_last_completed_step": "24",
  "expected_image_prompts_json_count": 7,
  "expected_image_content_json_count": 7,
  "expected_generated_images": [
    "generated_image_1",
    "generated_image_2",
    "generated_image_3",
    "generated_image_4",
    "generated_image_5",
    "generated_image_6",
    "generated_image_7"
  ],
  "expected_generated_files": [
    "image_12.png",
    "image_14.png",
    "image_16.png",
    "image_18.png",
    "image_20.png",
    "image_22.png",
    "image_24.png"
  ],
  "expected_generation_backend_for_all_images": "flow_browser",
  "expected_generation_model_for_all_images": "Nano Banana 2",
  "expected_cooldown_logs": [
    "Model cooldown wait started",
    "Model cooldown wait completed"
  ]
}
```

---

# Known risk for PATCH_SET_12

```json
{
  "primary_risk": "Flow UI selectors are unknown and may require live DOM inspection.",
  "expected_failure_type": "selector/readiness failure, not architecture failure",
  "rule_if_failure": "patch only the exact failing Flow selector/helper and preserve the patch sequence"
}
```

Likely fragile points:

```json
[
  "Flow project creation/opening",
  "prompt input selector",
  "reference image upload/ingredient selector",
  "aspect ratio selector",
  "generate button selector",
  "generated image tile selector",
  "download button selector"
]
```

---
