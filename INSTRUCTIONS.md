# CHAT

STATE 10:

ACTION:

- Reviewed attached current `prompts.md`.
- Generated `PATCH_SET_03 — Image prompt wording cleanup`.
- Enforced controlled patching: prompt-doc edits only, no Python script edits.
- Preserved output schemas, buyer questions, image roles, and Amazon image rules.
- Aligned PROMPT 11–24 with the completed `PATCH_SET_02` `IMAGE_CONTEXT_JSON` router. The current file still instructs image prompts to use `workflow_state.json`, so this patch is required.

SEARCH VALIDATION RESULT:

- OpenAI’s current image-generation documentation confirms reference images can be provided separately as image inputs, including multiple reference images, which supports the rule that reference product images should not be embedded inside `IMAGE_CONTEXT_JSON`. ([OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation))
- OpenAI’s docs also show image generation driven by prompts, reinforcing the separation between the compact text prompt/context and separately supplied image inputs. ([OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation))

VALIDATED DECISION:

- Proceed with `PATCH_SET_03`.
- Use range-scoped replacements only inside `# PROMPT 11` through `# PROMPT 24`.
- Do not modify PROMPT 1A–10.
- Do not change JSON output schemas.

OUTPUT:

## PATCH_SET_03 — Image prompt wording cleanup

### Scope rule for every patch below

Apply only within this range:

```
START: # PROMPT 11
END: end of file
```

Do **not** apply these replacements to PROMPT 1A–10.

---

## PATCH_03A — Replace full workflow-state input instruction

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03A",
  "expected_match_count": 14,
  "expected_replacement_count": 14,
  "halt_if_match_count_is_not": 14
}
```

### FIND

```
Use the structured dataset contained in workflow_state.json.
```

### REPLACE WITH

```
Use only the IMAGE_CONTEXT_JSON supplied by the orchestrator for this step.
Reference product images are attached separately through the browser/model workflow and are not embedded inside IMAGE_CONTEXT_JSON.
Do not use or assume access to the full workflow_state.json.
```

---

## PATCH_03B — Replace reference_tag source wording

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03B",
  "expected_match_count": 14,
  "expected_replacement_count": 14,
  "halt_if_match_count_is_not": 14
}
```

### FIND

```
reference_tag must be read from workflow_state.json and preserved unchanged.
```

### REPLACE WITH

```
reference_tag must be read from IMAGE_CONTEXT_JSON and preserved unchanged.
```

---

## PATCH_03C — Replace state-file dependency rule

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03C",
  "expected_match_count": 14,
  "expected_replacement_count": 14,
  "halt_if_match_count_is_not": 14
}
```

### FIND

```
Use only workflow_state.json; do not assume category, product type, or features beyond the state file.
```

### REPLACE WITH

```
Use only IMAGE_CONTEXT_JSON and separately attached reference product images; do not assume category, product type, accessories, specifications, features, or visual details beyond those supplied inputs.
```

---

## PATCH_03D — Replace dataset heading wording

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03D",
  "expected_match_count": 14,
  "expected_replacement_count": 14,
  "halt_if_match_count_is_not": 14
}
```

### FIND

```
The dataset includes:
```

### REPLACE WITH

```
IMAGE_CONTEXT_JSON includes:
```

---

## PATCH_03E — Add package_contents to PROMPT 11 context list

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03E",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```
- product_profile
- attributes
- additional_attributes
- visual_identity
- object_layout_map
- lighting_profile
- camera_profile
- product_geometry
- image_views
```

### REPLACE WITH

```
- product_identity
- included_accessories
- package_contents
- visual_grounding
- visual_identity
- object_layout_map
- lighting_profile
- camera_profile
- product_geometry
- image_views
- style_guidance
- visual_attribute_subset
- image_task
- amazon_rules
```

---

## PATCH_03F — Add package_contents to PROMPT 12 context list

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03F",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```
- product_profile
- attributes
- additional_attributes
- visual_identity
- object_layout_map
- lighting_profile
- camera_profile
- product_geometry
- image_views
- image_strategy
```

### REPLACE WITH

```
- image_task
- image_generation_prompt
- included_accessories
- package_contents
- visual_grounding
- visual_identity
- object_layout_map
- product_geometry
- image_views
- style_lock
- source_images
```

---

## PATCH_03G — Standardize image-prompt-generation context lists

Apply only to PROMPT `13`, `15`, `17`, `19`, `21`, and `23`.

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03G",
  "expected_match_count": 6,
  "expected_replacement_count": 6,
  "halt_if_match_count_is_not": 6
}
```

### FIND

```
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- product_geometry
- image_views
- image_style_lock
```

### REPLACE WITH

```
- image_task
- product_identity
- included_accessories
- visual_grounding
- visual_identity
- object_layout_map
- product_geometry
- image_views
- style_guidance
- image_style_lock
- visual_attribute_subset
- feature_subset
- amazon_rules
- source_images
```

---

## PATCH_03H — Standardize image-generation context lists

Apply only to PROMPT `14`, `16`, `18`, `20`, `22`, and `24`.

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03H",
  "expected_match_count": 6,
  "expected_replacement_count": 6,
  "halt_if_match_count_is_not": 6
}
```

### FIND

```
- product_profile
- attributes
- additional_attributes
- core_features
- visual_identity
- object_layout_map
- product_geometry
- image_views
- image_style_lock
- image_strategy
```

### REPLACE WITH

```
- image_task
- image_generation_prompt
- included_accessories
- visual_grounding
- visual_identity
- object_layout_map
- product_geometry
- image_views
- style_lock
- source_images
```

---

## PATCH_03I — Replace style-lock reference wording: prompt-generation steps

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03I",
  "expected_match_count": 7,
  "expected_replacement_count": 7,
  "halt_if_match_count_is_not": 7
}
```

### FIND

```
Use image_style_lock from workflow_state.json to maintain:
```

### REPLACE WITH

```
Use image_style_lock from IMAGE_CONTEXT_JSON.style_guidance to maintain:
```

---

## PATCH_03J — Replace style-lock reference wording: image-generation steps

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03J",
  "expected_match_count": 5,
  "expected_replacement_count": 5,
  "halt_if_match_count_is_not": 5
}
```

### FIND

```
Maintain the following parameters from workflow_state.json:
```

### REPLACE WITH

```
Maintain the following parameters from IMAGE_CONTEXT_JSON.style_lock:
```

---

## PATCH_SET_03 VALIDATION CHECKPOINT

```json
{
  "patch_set_id": "PATCH_SET_03",
  "expected_behavior": "PROMPT 11 through PROMPT 24 instruct the model to use IMAGE_CONTEXT_JSON only, preserve separately attached reference images, and no longer imply direct access to full workflow_state.json.",
  "expected_present": {
    "Use only the IMAGE_CONTEXT_JSON supplied by the orchestrator for this step.": 14,
    "Reference product images are attached separately through the browser/model workflow and are not embedded inside IMAGE_CONTEXT_JSON.": 14,
    "reference_tag must be read from IMAGE_CONTEXT_JSON and preserved unchanged.": 14,
    "IMAGE_CONTEXT_JSON includes:": 14,
    "package_contents": "present in PROMPT 11 and PROMPT 12 context lists"
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
    "Do not modify PROMPT 1A through PROMPT 10",
    "Do not modify workflow_orchestrator.py",
    "Do not change any JSON output schema",
    "Do not change image_number values",
    "Do not change buyer_question values",
    "Do not imply reference images are embedded inside IMAGE_CONTEXT_JSON"
  ]
}
```

## PATCH_SET_03 validation commands

Run a dry-run first:

```powershell
# Your patch tool should report match counts before applying replacements.
# Halt immediately if any count differs from the metadata above.
```

Then validate:

```powershell
D:\TOOLS\Python314\python.exe - <<'PY'
from pathlib import Path
import re

p = Path("docs/prompts.md")
text = p.read_text(encoding="utf-8")

image_region = text[text.index("# PROMPT 11"):]

assert image_region.count("Use only the IMAGE_CONTEXT_JSON supplied by the orchestrator for this step.") == 14
assert image_region.count("Reference product images are attached separately through the browser/model workflow and are not embedded inside IMAGE_CONTEXT_JSON.") == 14
assert image_region.count("reference_tag must be read from IMAGE_CONTEXT_JSON and preserved unchanged.") == 14
assert image_region.count("IMAGE_CONTEXT_JSON includes:") == 14

for forbidden in [
    "Use the structured dataset contained in workflow_state.json.",
    "reference_tag must be read from workflow_state.json and preserved unchanged.",
    "Use only workflow_state.json; do not assume category, product type, or features beyond the state file.",
]:
    assert forbidden not in image_region, forbidden

pre_image_region = text[:text.index("# PROMPT 11")]
assert "Use only the IMAGE_CONTEXT_JSON supplied by the orchestrator for this step." not in pre_image_region

prompt_11 = image_region.split("# PROMPT 12")[0]
prompt_12 = image_region.split("# PROMPT 12")[1].split("# PROMPT 13")[0]
assert "package_contents" in prompt_11
assert "package_contents" in prompt_12

print("PATCH_SET_03_TARGETED_VALIDATION_OK")
print("image_prompts_checked=14")
print("pre_image_prompts_unchanged=True")
print("prompt_11_package_contents=True")
print("prompt_12_package_contents=True")
PY
```

CONFIRMATION REQUIRED:

YES