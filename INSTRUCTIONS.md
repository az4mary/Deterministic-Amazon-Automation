**Github cloned into Local** **-** D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch
**Github:** https://github.com/az4mary/Deterministic-Amazon-Automation.git 
**Branch:** codex_branch
**File:** workflow_orchestrator.py

ACTION:

- Perform actual Dry-run locally.
- Implement `PATCH_SET_02` in manageable segment based on your capability.
- Commit per PATCH and not per PATCH_SET to remote github codex_branch
- Find `PATCH_SET_02` below.
- Send `PATCH_SET_02` COMPLETION REPORT

**DRY-RUN EXPECTATION:**

```json
{
  "patch_id": "PATCH_XXA",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

VALIDATED DECISION:

- `PATCH_SET_02` will solve PROMPT 11–24 by adding one centralized routing layer:
    - image prompt steps `11,13,15,17,19,21,23` receive slim `IMAGE_CONTEXT_JSON`
    - image generation steps `12,14,16,18,20,22,24` use only the prior `image_generation_prompt`, slim strategy context, and separately attached reference images
- No manual one-off patching per image prompt.
- No full `workflow_state.json` sent to image prompt/generation steps after this patch.

OUTPUT:

## PATCH_SET_02 — Centralized image context router

### PATCH_02A — Add image step constants and task metadata

**FIND**

```python
TEXT_STEP_WAIT_SECONDS = int(os.getenv("TEXT_STEP_WAIT_SECONDS", "0"))
IMAGE_STEP_WAIT_SECONDS = int(os.getenv("IMAGE_STEP_WAIT_SECONDS", "0"))
```

**REPLACE WITH**

```python
TEXT_STEP_WAIT_SECONDS = int(os.getenv("TEXT_STEP_WAIT_SECONDS", "0"))
IMAGE_STEP_WAIT_SECONDS = int(os.getenv("IMAGE_STEP_WAIT_SECONDS", "0"))

IMAGE_PROMPT_STEP_IDS = {"11", "13", "15", "17", "19", "21", "23"}
IMAGE_GENERATION_STEP_IDS = {"12", "14", "16", "18", "20", "22", "24"}

IMAGE_TASKS: Dict[str, Dict[str, Any]] = {
    "11": {
        "image_number": 1,
        "image_type": "Hero Product Image",
        "buyer_question": "What is this product?",
        "focus": "product identity, visual accuracy, included accessories, Amazon hero image compliance",
    },
    "13": {
        "image_number": 2,
        "image_type": "Core Benefit Image",
        "buyer_question": "Why do I need it?",
        "focus": "top customer-facing benefits and product value",
    },
    "15": {
        "image_number": 3,
        "image_type": "Problem Solution Image",
        "buyer_question": "What problem does this product solve?",
        "focus": "problem-to-solution mapping using verified features only",
    },
    "17": {
        "image_number": 4,
        "image_type": "Lifestyle Use Image",
        "buyer_question": "When would I use it?",
        "focus": "realistic use cases and safe lifestyle context",
    },
    "19": {
        "image_number": 5,
        "image_type": "Technology Feature Image",
        "buyer_question": "What technology makes it better?",
        "focus": "verified technical capabilities only",
    },
    "21": {
        "image_number": 6,
        "image_type": "Ease of Use / Installation Image",
        "buyer_question": "How easy is it to install or use?",
        "focus": "setup steps, included setup accessories, user workflow",
    },
    "23": {
        "image_number": 7,
        "image_type": "Specifications Infographic",
        "buyer_question": "What specifications matter?",
        "focus": "most relevant verified specifications for purchase decision",
    },
}
```

---

### PATCH_02B — Add slim image context helper functions

**FIND**

```python
def build_text_input(state: Dict[str, Any], prompt_text: str) -> str:
    compact_state = json.dumps(state, ensure_ascii=False, indent=2)
    return (
        f"WORKFLOW_STATE_JSON:\n{compact_state}\n\n"
        f"INSTRUCTIONS:\n{prompt_text}\n\n"
        f"OUTPUT RULES:\nReturn only valid JSON."
    )
```

**REPLACE WITH**

```python
def pick_visual_attributes(product_data: Dict[str, Any]) -> Dict[str, Any]:
    attributes = product_data.get("attributes", {})
    additional = product_data.get("additional_attributes", {})
    if not isinstance(attributes, dict):
        attributes = {}
    if not isinstance(additional, dict):
        additional = {}

    visual_keywords = {
        "color",
        "material",
        "materials",
        "screen",
        "display",
        "lens",
        "viewing",
        "angle",
        "size",
        "dimensions",
        "shape",
        "mount",
        "bracket",
        "accessory",
        "accessories",
        "included",
        "app",
        "wifi",
        "wi-fi",
        "sensor",
        "night",
        "resolution",
        "frame",
        "coverage",
        "installation",
        "setup",
    }

    selected: Dict[str, Any] = {}
    for source in (attributes, additional):
        for key, value in source.items():
            key_text = str(key).lower()
            if any(token in key_text for token in visual_keywords):
                selected[key] = value
    return selected

def get_extraction_output(state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    outputs = state.get("outputs", {})
    if isinstance(outputs, dict) and isinstance(outputs.get(step_id), dict):
        return outputs[step_id]
    promoted_key = "prompt_01A" if step_id == "01A" else "prompt_01B"
    promoted = state.get(promoted_key)
    if isinstance(promoted, dict):
        return promoted
    return {}

def build_image_prompt_context(state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    product_data = get_extraction_output(state, "01A")
    visual_data = get_extraction_output(state, "01B")
    image_task = IMAGE_TASKS.get(step_id)
    if image_task is None:
        fail(
            "IMAGE_CONTEXT_STEP_INVALID",
            f"No image task metadata exists for step {step_id}.",
            field="step_id",
            expected="one of IMAGE_PROMPT_STEP_IDS",
            actual=step_id,
        )

    product_profile = product_data.get("product_profile", {})
    if not isinstance(product_profile, dict):
        product_profile = {}

    context: Dict[str, Any] = {
        "reference_tag": state.get("reference_tag", ""),
        "image_task": image_task,
        "product_identity": {
            "product_category": product_data.get("product_category", ""),
            "brand": product_profile.get("brand", ""),
            "product_name": product_profile.get("product_name", ""),
            "model": product_profile.get("model", ""),
            "color": product_profile.get("color", ""),
        },
        "included_accessories": product_data.get("package_contents", []),
        "visual_grounding": {
            "visual_identity": visual_data.get("visual_identity", {}),
            "object_layout_map": visual_data.get("object_layout_map", {}),
            "product_geometry": visual_data.get("product_geometry", {}),
            "image_views": visual_data.get("image_views", {}),
        },
        "style_guidance": {
            "lighting_profile": visual_data.get("lighting_profile", {}),
            "camera_profile": visual_data.get("camera_profile", {}),
            "image_style_lock": state.get("image_style_lock", {}),
        },
        "visual_attribute_subset": pick_visual_attributes(product_data),
        "feature_subset": product_data.get("core_features", []),
        "source_images": state.get("source_payload", {}).get("source_images", []),
    }

    if step_id == "11":
        context["amazon_rules"] = {
            "background": "pure white RGB 255,255,255",
            "allowed_objects": "product and included accessories only",
            "text_graphics": "none",
            "frame_fill": "approximately 85%",
            "visibility": "entire product visible",
            "format": "1080x1920 vertical 9:16",
        }
    else:
        context["amazon_rules"] = {
            "product_visibility": "product must be clearly visible and accurately represented",
            "text_graphics": "allowed only for verified features and secondary-image explanation",
            "feature_accuracy": "graphics must represent real product features only",
            "accessory_limit": "do not show accessories not included with the product",
            "format": "1080x1920 vertical 9:16",
        }

    return context

def build_image_generation_context(state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    previous_strategy_key = f"image_strategy_{int(step_id) - 1}"
    strategy = state.get(previous_strategy_key) or state.get("image_strategy")
    if not isinstance(strategy, dict):
        fail(
            "MISSING_IMAGE_STRATEGY",
            f"No image strategy found for image generation step {step_id}",
            field="image_strategy",
            expected=previous_strategy_key,
            actual=type(strategy).__name__,
        )

    product_data = get_extraction_output(state, "01A")
    visual_data = get_extraction_output(state, "01B")

    return {
        "reference_tag": state.get("reference_tag", ""),
        "image_task": {
            "image_number": int(step_id) // 2,
            "image_type": strategy.get("image_type", ""),
            "buyer_question": strategy.get("buyer_question", ""),
        },
        "image_generation_prompt": strategy.get("image_generation_prompt", ""),
        "included_accessories": product_data.get("package_contents", []),
        "visual_grounding": {
            "visual_identity": visual_data.get("visual_identity", {}),
            "object_layout_map": visual_data.get("object_layout_map", {}),
            "product_geometry": visual_data.get("product_geometry", {}),
            "image_views": visual_data.get("image_views", {}),
        },
        "style_lock": state.get("image_style_lock", deterministic_style_lock()),
        "source_images": state.get("source_payload", {}).get("source_images", []),
    }

def build_model_context_for_step(state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    if step_id in IMAGE_PROMPT_STEP_IDS:
        return {
            "context_type": "IMAGE_CONTEXT_JSON",
            "image_context": build_image_prompt_context(state, step_id),
        }
    return state

def build_text_input(state: Dict[str, Any], prompt_text: str) -> str:
    context_label = "IMAGE_CONTEXT_JSON" if state.get("context_type") == "IMAGE_CONTEXT_JSON" else "WORKFLOW_STATE_JSON"
    compact_state = json.dumps(state, ensure_ascii=False, indent=2)
    return (
        f"{context_label}:\n{compact_state}\n\n"
        f"INSTRUCTIONS:\n{prompt_text}\n\n"
        f"OUTPUT RULES:\nReturn only valid JSON."
    )
```

---

### PATCH_02C — Route image prompt steps through slim context

**FIND**

```python
        prompt_text = read_prompt_file(step.step_id)
        schema = build_schema()
        output = call_text_step(step.step_id, prompt_text, schema, state)
        update_state_with_prompt(state, step.step_id, output, step.output_key)
```

**REPLACE WITH**

```python
        prompt_text = read_prompt_file(step.step_id)
        schema = build_schema()
        model_context = build_model_context_for_step(state, step.step_id)
        output = call_text_step(step.step_id, prompt_text, schema, model_context)
        update_state_with_prompt(state, step.step_id, output, step.output_key)
```

---

### PATCH_02D — Use image generation context inside image generation steps

**FIND**

```python
        # Use the immediately preceding image strategy prompt stored in state.
        prev_strategy_key = f"image_strategy_{int(step.step_id) - 1}"
        strategy = state.get(prev_strategy_key) or state.get("image_strategy")
        if not strategy:
            fail("MISSING_IMAGE_STRATEGY", f"No image strategy found for image generation step {step.step_id}")
        prompt = strategy["image_generation_prompt"]

        result = call_image_generation(prompt)
```

**REPLACE WITH**

```python
        generation_context = build_image_generation_context(state, step.step_id)
        prompt = generation_context["image_generation_prompt"]
        strategy = {
            "image_type": generation_context["image_task"]["image_type"],
            "buyer_question": generation_context["image_task"]["buyer_question"],
            "image_generation_prompt": prompt,
        }

        result = call_image_generation(prompt)
```

---

### PATCH_02E — Validation commands

Run:

```powershell
python -m py_compile workflow_orchestrator.py
python workflow_orchestrator.py --stop-after 11
```

Expected result:

```json
{
  "py_compile": "PASS",
  "stop_after_11": "PASS",
  "expected_behavior": [
    "Steps 01A through 10 use WORKFLOW_STATE_JSON",
    "Step 11 uses IMAGE_CONTEXT_JSON",
    "workflow_state.json remains full persisted source of truth",
    "image_prompts.json remains generated from persisted image_strategy outputs"
  ]
}
```

CONFIRMATION REQUIRED:

YES

## PATCH_SET_ VALIDATION CHECKPOINT

Expected validation summary:

```json
{
  "patch_set_id": "",
  "expected_behavior": "",
  "expected_present": {
    "": ,
    "": ,
    "": 
  },
  "expected_terminal_success_fields": [
    "",
    "",
    "",
    "",
    ""
  ],
  "forbidden_changes": [
    "",
    "",
    "",
    "",
    "",
    ""
  ]
}
```

CONFIRMATION REQUIRED:

YES — confirm `PATCH_SET_02` completion to proceed to `PATCH_SET_03`.