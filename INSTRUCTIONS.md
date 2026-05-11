# NEXT CHAT

- Reconciled the failed `PATCH_03H` dry-run.
- Identified the correct cause: PROMPT 14 has the same generation-context fields as PROMPT 16/18/20/22/24 but with `image_strategy` and `image_style_lock` reversed, so the original exact `FIND` block can only match 5 prompts.
- Also identified a second upcoming issue: original `PATCH_03I` expected 7 matches, but prompt-generation style wording should apply only to PROMPT 13/15/17/19/21/23. PROMPT 14 is an image-generation prompt and should use `style_lock`, not `style_guidance`.

SEARCH VALIDATION RESULT:

- OpenAI’s image generation tool supports text prompts with optional image inputs, validating the continued separation between `IMAGE_CONTEXT_JSON` and attached reference images. ([OpenAI Developers](https://developers.openai.com/api/docs/guides/tools-image-generation?utm_source=chatgpt.com))
- OpenAI’s image edit API supports one or more source images plus a prompt, confirming that reference images should be treated as separate image inputs rather than serialized inside the JSON context. ([OpenAI Developers](https://developers.openai.com/api/reference/python/resources/images/methods/edit/?utm_source=chatgpt.com))

VALIDATED DECISION:

- Do **not** force `PATCH_03H` as originally written.
- Replace it with split patches:
    - `PATCH_03H1` for PROMPT 14’s variant list.
    - `PATCH_03H2` for PROMPT 16/18/20/22/24.
- Revise the remaining style-lock patches:
    - `PATCH_03I` should target only 6 prompt-generation steps.
    - `PATCH_03J` should target the 5 generation steps that use `Maintain the following parameters...`.
    - Add `PATCH_03K` for PROMPT 14’s generation-style wording.

OUTPUT:

## Revised remaining PATCH_SET_03 sequence

### PATCH_03H1 — Standardize PROMPT 14 image-generation context list

Apply only inside `# PROMPT 14`.

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03H1",
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
- core_features
- visual_identity
- object_layout_map
- product_geometry
- image_views
- image_strategy
- image_style_lock
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

### PATCH_03H2 — Standardize remaining image-generation context lists

Apply only to PROMPT `16`, `18`, `20`, `22`, and `24`.

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03H2",
  "expected_match_count": 5,
  "expected_replacement_count": 5,
  "halt_if_match_count_is_not": 5
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

### PATCH_03I — Replace style-lock wording in prompt-generation steps

Apply only to PROMPT `13`, `15`, `17`, `19`, `21`, and `23`.

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03I",
  "expected_match_count": 6,
  "expected_replacement_count": 6,
  "halt_if_match_count_is_not": 6
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

### PATCH_03J — Replace style-lock wording in image-generation steps

Apply only to PROMPT `16`, `18`, `20`, `22`, and `24`.

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

### PATCH_03K — Replace PROMPT 14 generation-style wording

Apply only inside `# PROMPT 14`.

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_03K",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```
Use image_style_lock from workflow_state.json to maintain:
```

### REPLACE WITH

```
Use style_lock from IMAGE_CONTEXT_JSON to maintain:
```

---

## Revised PATCH_SET_03 validation checkpoint

```json
{
  "patch_set_id": "PATCH_SET_03",
  "expected_behavior": "PROMPT 11 through PROMPT 24 instruct the model to use IMAGE_CONTEXT_JSON only, preserve separately attached reference images, and no longer imply direct access to full workflow_state.json.",
  "expected_present": {
    "Use only the IMAGE_CONTEXT_JSON supplied by the orchestrator for this step.": 14,
    "Reference product images are attached separately through the browser/model workflow and are not embedded inside IMAGE_CONTEXT_JSON.": 14,
    "reference_tag must be read from IMAGE_CONTEXT_JSON and preserved unchanged.": 14,
    "IMAGE_CONTEXT_JSON includes:": 14,
    "Use image_style_lock from IMAGE_CONTEXT_JSON.style_guidance to maintain:": 6,
    "Maintain the following parameters from IMAGE_CONTEXT_JSON.style_lock:": 5,
    "Use style_lock from IMAGE_CONTEXT_JSON to maintain:": 1,
    "package_contents": "present in PROMPT 11 and PROMPT 12 context lists"
  },
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

## Continue order

```json
{
  "next_patch": "PATCH_03H1",
  "then": [
    "PATCH_03H2",
    "PATCH_03I",
    "PATCH_03J",
    "PATCH_03K",
    "PATCH_SET_03 targeted validation"
  ]
}
```

CONFIRMATION REQUIRED:

YES