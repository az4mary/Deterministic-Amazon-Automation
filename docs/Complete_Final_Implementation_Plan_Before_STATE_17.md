This is the controlling plan from this point forward.

## 0. Non-negotiable interpretation

`PATCH_SET_02` and `PATCH_SET_03` **already fixed the original image-context defect**.

Do **not** reopen or repatch them unless validation proves their implemented behavior changed.

The remaining work before `STATE 17` is **not** “fix image context routing again.” The remaining work is to validate and, if needed, patch the **actual even-step image-generation adapter handoff**.

---

## 1. Source of truth

This plan is governed by `Current_Implementation_Plan.md`.

The plan defines one centralized image-context router:

```json
{
  "image_prompt_steps": ["11", "13", "15", "17", "19", "21", "23"],
  "image_generation_steps": ["12", "14", "16", "18", "20", "22", "24"],
  "json_payload": "slim IMAGE_CONTEXT_JSON only",
  "full_workflow_state": "persisted source of truth only, not sent to image steps",
  "reference_images": "attached separately through image model/browser workflow where supported"
}
```

That is explicitly stated in the implementation plan.

---

## 2. Already completed and locked

### PATCH_SET_02 — Script: centralized image context router

**Status:** `COMPLETE / LOCKED`

The current script contains:

```python
IMAGE_PROMPT_STEP_IDS = {"11", "13", "15", "17", "19", "21", "23"}
IMAGE_GENERATION_STEP_IDS = {"12", "14", "16", "18", "20", "22", "24"}
```

The current script routes image prompt text steps through `build_model_context_for_step(...)`, which returns `context_type: IMAGE_CONTEXT_JSON` for image prompt steps instead of sending the full workflow state.

**Locked behavior:**

```json
{
  "normal_text_steps_01A_to_10": "WORKFLOW_STATE_JSON",
  "image_prompt_steps_11_13_15_17_19_21_23": "IMAGE_CONTEXT_JSON",
  "workflow_state_json": "persisted full source of truth",
  "full_workflow_state_sent_to_image_prompt_steps": false
}
```

### PATCH_SET_03 — Prompt docs: image-context wording

**Status:** `COMPLETE / LOCKED`

The current `prompts.md` says PROMPT 11 and PROMPT 12 use only `IMAGE_CONTEXT_JSON`, do not assume access to full `workflow_state.json`, and preserve `reference_tag` from `IMAGE_CONTEXT_JSON`.

The PATCH_SET_03 validation reported:

- `IMAGE_CONTEXT_JSON` wording: `14 / 14`
- reference image separation wording: `14 / 14`
- old workflow-state dependency wording: `0`
- `package_contents` present in PROMPT 11 and PROMPT 12

**Locked behavior:**

```json
{
  "PROMPT_11_to_24_wording": "IMAGE_CONTEXT_JSON",
  "old_workflow_state_dependency_wording": "removed",
  "package_contents_in_PROMPT_11_and_12": true,
  "output_schemas_changed": false
}
```

---

## 3. Step 11 rule — do not drift

### STEP 11 = Hero Image Prompt Generation

STEP 11 is **not** actual image generation.

STEP 11 generates:

```json
{
  "image_strategy": {
    "image_number": 1,
    "image_type": "Hero Product Image",
    "buyer_question": "What is this product?",
    "layout_description": "",
    "headline_text": "N/A",
    "supporting_text": "N/A",
    "visual_design_direction": "",
    "image_generation_prompt": ""
  }
}
```

PROMPT 11’s job is to create the **prompt for image generation**, not to render the image.

### STEP 11 input boundary

STEP 11 receives:

```json
{
  "context_type": "IMAGE_CONTEXT_JSON",
  "image_context": {
    "product_identity": {},
    "included_accessories": [],
    "package_contents": [],
    "visual_grounding": {},
    "style_guidance": {},
    "visual_attribute_subset": {},
    "feature_subset": [],
    "image_task": {},
    "amazon_rules": {}
  }
}
```

### STEP 11 raw reference-image attachment

**Do not require raw binary image attachment at STEP 11.**

The raw image analysis already happens in `01B`. STEP 11 uses the derived `visual_grounding` from `01B`.

If future wording says “reference images are attached separately” in PROMPT 11, the operational interpretation is:

```json
{
  "STEP_11": {
    "raw_binary_image_attachment_required": false,
    "uses_visual_grounding_from_01B": true,
    "may_receive_source_image_paths_in_IMAGE_CONTEXT_JSON": true,
    "must_not_receive_full_workflow_state": true
  }
}
```

Do **not** patch STEP 11 to attach raw images unless we explicitly define a V2 behavior change.

---

## 4. Step 12 rule — actual unresolved boundary

### STEP 12 = Hero Image Generation

STEP 12 is the first actual image-generation step.

The implementation plan says even image steps must not receive workflow state. They should receive only:

```json
{
  "reference_tag": "",
  "image_task": {},
  "image_generation_prompt": "",
  "visual_grounding": {},
  "included_accessories": [],
  "style_lock": {},
  "source_images": []
}
```

and reference images should be attached separately through the image model/browser workflow where supported.

### Current implementation gap

The current `run_step()` already builds `generation_context`, but then extracts only the text prompt:

```python
generation_context = build_image_generation_context(state, step.step_id)
prompt = generation_context["image_generation_prompt"]
result = call_image_generation(prompt)
```

The current adapter boundary is still:

```python
def call_image_generation(prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
    return get_execution_adapter().execute_image(prompt, size=size)
```

So the remaining issue is:

```json
{
  "issue": "generation_context exists but is not handed to the image execution adapter",
  "not_issue": "image prompt context routing",
  "not_issue_2": "PROMPT 11-24 docs wording"
}
```

---

## 5. Correct current status before STATE 17

```json
{
  "STATE_16": "TEXT_AND_IMAGE_PROMPT_EXECUTION_PASS",
  "validated": [
    "01A product extraction",
    "01B visual grounding with reference images",
    "02-10 listing text steps",
    "11 hero image prompt generation",
    "IMAGE_CONTEXT_JSON routing for STEP 11",
    "image_prompts.json output",
    "resume semantics",
    "stop-after semantics",
    "browser text execution stabilization"
  ],
  "not_yet_validated": [
    "12 actual image generation",
    "reference-image handoff to image generation adapter",
    "generated_image_1 state output",
    "generated image file persistence"
  ],
  "STATE_17_allowed": false
}
```

---

## 6. Required next patch before STATE 17

# PATCH_SET_10 — Image generation adapter context handoff

## Purpose

Pass the already-built `generation_context` into the image-generation adapter for even image steps.

This patch must **not** touch:

```json
[
  "PATCH_SET_02 image prompt routing",
  "PATCH_SET_03 prompt docs wording",
  "STEP 11 behavior",
  "PROMPT 11 behavior",
  "normal text steps 01A-10",
  "output schemas unless strictly required for generated_image metadata"
]
```

## PATCH_SET_10 required behavior

For STEP 12, the adapter boundary must receive:

```json
{
  "prompt": "image_generation_prompt",
  "generation_context": {
    "reference_tag": "",
    "image_task": {
      "image_number": 1,
      "image_type": "Hero Product Image",
      "buyer_question": "What is this product?"
    },
    "image_generation_prompt": "",
    "included_accessories": [],
    "visual_grounding": {},
    "style_lock": {},
    "source_images": []
  }
}
```

The adapter must not receive full `workflow_state.json`.

## PATCH_SET_10 target changes

### 10A — Extend adapter interface

Change:

```python
def execute_image(self, prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
```

to accept an optional context:

```python
def execute_image(
    self,
    prompt: str,
    size: str = "1024x1536",
    generation_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
```

Apply consistently to:

```json
[
  "PromptExecutionAdapter",
  "OpenAIPromptExecutionAdapter",
  "BrowserPromptExecutionAdapter",
  "call_image_generation"
]
```

### 10B — Pass context from `run_step()`

Change even image-generation execution from:

```python
result = call_image_generation(prompt)
```

to:

```python
result = call_image_generation(prompt, generation_context=generation_context)
```

### 10C — Make reference-image behavior explicit

Minimum acceptable V1 behavior:

```json
{
  "source_images_present": "logged and available at adapter boundary",
  "backend_supports_reference_images": "explicitly logged or enforced",
  "silent_drop_of_source_images": false
}
```

If the selected backend cannot attach reference images, it must not pretend it did.

Acceptable choices:

```json
{
  "strict_mode": "fail if source_images exist but backend cannot attach them",
  "non_strict_mode": "log warning that source_images were available but not attached"
}
```

For this project, I recommend **strict mode** for actual image-generation validation.

---

## 7. Required validation before STATE 17

### Validation A — compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

### Validation B — dry-run STEP 12 contract test

Mock:

```json
[
  "call_image_generation",
  "save_image",
  "save_json_atomic",
  "apply_step_wait"
]
```

Expected:

```json
{
  "step": "12",
  "uses_build_image_generation_context": true,
  "image_number": 1,
  "uses_image_strategy_1_prompt": true,
  "passes_generation_context_to_call_image_generation": true,
  "source_images_available_at_adapter_boundary": true,
  "does_not_pass_full_workflow_state_to_image_adapter": true,
  "generated_image_1_written_to_state": true
}
```

### Validation C — actual STEP 12 runtime

Only after the dry-run passes:

```powershell
$env:OPENAI_API_KEY="..."
$env:SKIP_IMAGES="0"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --resume --enable-image-generation --stop-after 12
```

Expected:

```json
{
  "expected": [
    "resume starts at 12",
    "step 12 executes",
    "generation_context is built",
    "source_images are available at image adapter boundary",
    "generated_image_1 exists in workflow_state.json",
    "generated image file exists under output/generated_images/",
    "last_completed_step=12",
    "OUTPUT/SUCCESS"
  ]
}
```

### Validation D — do not run full sequence yet

Do **not** run `--enable-image-generation` through step 24 until step 12 passes alone.

---

## 8. STATE 17 entry rule

`STATE 17` may begin only after this exact condition is true:

```json
{
  "PATCH_SET_02": "CONFIRMED",
  "PATCH_SET_03": "CONFIRMED",
  "PATCH_SET_04_to_09_runtime_stabilization": "CONFIRMED",
  "STATE_16_text_and_image_prompt_execution": "PASS",
  "PATCH_SET_10_image_generation_adapter_context_handoff": "PASS",
  "STEP_12_actual_image_generation": "PASS"
}
```

Until then:

```json
{
  "STATE_17": "BLOCKED",
  "reason": "actual image generation execution boundary not validated"
}
```

---

## 9. Forbidden future drift

Do not say any of the following again unless a new file proves it:

```json
[
  "PATCH_SET_02 did not fix image context routing",
  "PATCH_SET_03 did not fix prompt wording",
  "STEP 11 must attach raw reference images",
  "STATE 16 is full execution pass before STEP 12 image generation runs",
  "Image generation has been validated because image_prompts.json exists",
  "Prompt generation and image generation are the same execution concern",
  "The next action is STATE 17 before STEP 12 validation"
]
```

---

## 10. One-line stone version

```json
{
  "before_STATE_17": "PATCH_SET_02 and PATCH_SET_03 are locked; STEP 11 uses slim IMAGE_CONTEXT_JSON and does not require raw image attachment; STEP 12 is the first actual image-generation step and must pass generation_context/source_images into the image adapter, then be validated with --resume --enable-image-generation --stop-after 12 before STATE 17 can begin."
}
```
