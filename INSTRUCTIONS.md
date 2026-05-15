# GENERAL

---

# PATCH_SET_11 — Spatial Image Prompt Contract

## Purpose

Upgrade image prompt generation so every `image_generation_prompt` becomes a **photographer-grade, physically grounded scene brief**.

This patch does **not** implement Flow yet.

```json
{
  "PATCH_SET_11": "Spatial Image Prompt Contract",
  "target": [
    "workflow_orchestrator.py",
    "docs/prompts.md"
  ],
  "changes": [
    "extract/derive spatial product geometry from PROMPT 1B outputs",
    "persist spatial_image_contract into workflow_state.json",
    "include spatial_image_contract in IMAGE_CONTEXT_JSON",
    "require image prompt steps to output spatial_scene_brief",
    "force image_generation_prompt to include real-world POV, physical placement, optical axis, scale, screen/environment consistency, and negative spatial constraints"
  ],
  "does_not_touch": [
    "ChatGPT text execution",
    "image adapter handoff",
    "Flow browser backend",
    "cooldown pacing",
    "step numbering",
    "PATCH_SET_10 browser image execution fixes"
  ]
}
```

---

## Important decision: dimensions

Use this rule:

```json
{
  "dimension_policy": {
    "preferred": "Use exact product dimensions from input/source data.",
    "fallback": "If exact dimensions are missing from input/source data, mark dimensions as Unconfirmed and use relative proportions from PROMPT 1B.",
    "external_lookup": "Official product website or Amazon/similar marketplace dimensions may be added later through a separate enrichment patch.",
    "forbidden": "Do not invent exact dimensions."
  }
}
```

Reason: the current orchestrator is local-file driven. It has no product-dimension lookup step yet. So `PATCH_SET_11` should create the field and enforce the policy, but not silently browse or invent dimensions.

---

# Spatial Image Prompt Contract shape

Add this object:

```json
{
  "spatial_image_contract": {
    "product_dimensions": {
      "exact_dimensions": "",
      "dimension_source": "",
      "dimension_status": "confirmed | unconfirmed",
      "relative_scale": ""
    },
    "product_3d_geometry": {
      "overall_shape": "",
      "front_face": "",
      "rear_face": "",
      "top_face": "",
      "bottom_face": "",
      "left_side": "",
      "right_side": "",
      "component_depth_relationships": ""
    },
    "component_interaction_rules": {
      "mounting_or_support_logic": "",
      "lens_or_primary_function_axis": "",
      "screen_or_display_logic": "",
      "controls_and_ports_logic": "",
      "accessory_interaction_logic": ""
    },
    "photographer_scene_rules": {
      "camera_pov_required": "",
      "foreground_midground_background": "",
      "focal_plane_and_depth_of_field": "",
      "environment_sync_rules": "",
      "scale_rules": ""
    },
    "physics_constraints": [],
    "negative_spatial_constraints": []
  }
}
```

---

# What changes in each prompt

## PROMPT 1B

Add a new section to the visual extraction task:

```
**SPATIAL_IMAGE_CONTRACT EXTRACTION**

In addition to visual identity, extract spatial rules needed for future image generation.

Return only visually observable geometry. If exact dimensions are not visible or not provided, set exact_dimensions to "Unconfirmed" and describe relative scale/proportions only.

Extract:
- real 3D product geometry
- front/rear/top/side face roles
- component placement and depth relationships
- mounting/support surfaces if visible
- primary functional axis, such as lens direction, nozzle direction, blade direction, handle direction, display direction, speaker direction, or light beam direction
- screen/display logic if the product has a display
- physical constraints that must be obeyed in generated scenes
- negative constraints that prevent impossible geometry
```

Then require `spatial_image_contract` in the PROMPT 1B JSON output.

## PROMPT 11 / 13 / 15 / 17 / 19 / 21 / 23

Each image-prompt step must now use:

```
IMAGE_CONTEXT_JSON.spatial_image_contract
```

and the generated `image_generation_prompt` must be written with the master-prompt sections:

```
System/Role Context
Technical Specifications
Model Photographer's POV
Binding Geometry
Orientation & Spatial Sync
Scene Composition & Environmental Sync
Typography & Graphic Overlays
Physical Constraints
Negative Spatial Constraints
Amazon Compliance Constraints
```

For hero image `11`, the lifestyle/environment pieces should be replaced with studio-product spatial logic:

```json
{
  "hero_image_rule": "No environment, no lifestyle scene, no screen/environment sync unless the product screen must be shown as a physical component only."
}
```

For lifestyle, benefit, problem/solution, and tech images, the full POV/environment/screen-sync rules apply where relevant.

---

# Required script changes

## PATCH_11A — Extend `schema_1b`

Current `schema_1b()` requires:

```json
[
  "image_views",
  "visual_identity",
  "object_layout_map",
  "lighting_profile",
  "camera_profile",
  "product_geometry"
]
```

Add:

```json
"spatial_image_contract"
```

to required fields and properties.

## PATCH_11B — Add fallback contract builder

Add:

```python
def build_spatial_image_contract(product_data: Dict[str, Any], visual_data: Dict[str, Any]) -> Dict[str, Any]:
    ...
```

Purpose:

- Use `visual_data["spatial_image_contract"]` if present.
- Otherwise synthesize a safe fallback from:
    - `visual_identity`
    - `object_layout_map`
    - `product_geometry`
    - `image_views`
    - `attributes`
    - `additional_attributes`
    - `package_contents`

This protects older states or failed 1B outputs.

## PATCH_11C — Persist contract after `01B`

In `run_step()`, after:

```python
elif step.step_id == "01B":
    state["visual_grounding"] = output
```

add:

```python
    state["spatial_image_contract"] = build_spatial_image_contract(
        get_extraction_output(state, "01A"),
        output,
    )
```

## PATCH_11D — Include contract in prompt context

Add `spatial_image_contract` to `build_image_prompt_context(...)`.

Current context already includes visual grounding, style guidance, feature subset, and source images.

Add:

```python
"spatial_image_contract": build_spatial_image_contract(product_data, visual_data),
```

## PATCH_11E — Include contract in generation context

Current `build_image_generation_context(...)` sends only `image_task`, `image_generation_prompt`, accessories, visual grounding, style lock, and source images.

Add:

```python
"spatial_image_contract": build_spatial_image_contract(product_data, visual_data),
```

## PATCH_11F — Expand `schema_image_prompt`

Add required:

```json
"spatial_scene_brief"
```

inside `image_strategy`.

Proposed object:

```json
"spatial_scene_brief": {
  "type": "object",
  "additionalProperties": false,
  "required": [
    "system_role_context",
    "technical_specifications",
    "model_photographer_pov",
    "binding_geometry",
    "orientation_and_spatial_sync",
    "scene_composition_and_environmental_sync",
    "typography_and_graphic_overlays",
    "physical_constraints",
    "negative_spatial_constraints",
    "amazon_compliance_constraints"
  ],
  "properties": {
    "system_role_context": {"type": "string"},
    "technical_specifications": {"type": "string"},
    "model_photographer_pov": {"type": "string"},
    "binding_geometry": {"type": "string"},
    "orientation_and_spatial_sync": {"type": "string"},
    "scene_composition_and_environmental_sync": {"type": "string"},
    "typography_and_graphic_overlays": {"type": "string"},
    "physical_constraints": {"type": "array", "items": {"type": "string"}},
    "negative_spatial_constraints": {"type": "array", "items": {"type": "string"}},
    "amazon_compliance_constraints": {"type": "array", "items": {"type": "string"}}
  }
}
```

Then require `image_generation_prompt` to incorporate that `spatial_scene_brief` in plain language.

## PATCH_11G — Write `image_content.json`

Add:

```python
IMAGE_CONTENT_PATH = OUTPUT_DIR / "image_content.json"
```

Then save a compact file after image prompt steps:

```json
{
  "reference_tag": "",
  "spatial_image_contract": {},
  "image_prompts": []
}
```

This gives us the Flow payload file.

---

# Updated image prompt generation rule

Every image prompt step should now produce output like:

```json
{
  "reference_tag": "",
  "image_strategy": {
    "image_number": 2,
    "image_type": "Core Benefit Image",
    "buyer_question": "Why do I need this product?",
    "layout_description": "",
    "headline_text": "Capture Every Detail in Full HD",
    "supporting_text": "Record your drive in crisp 1080p resolution for reliable evidence and peace of mind on the road.",
    "visual_design_direction": "",
    "spatial_scene_brief": {
      "system_role_context": "",
      "technical_specifications": "",
      "model_photographer_pov": "",
      "binding_geometry": "",
      "orientation_and_spatial_sync": "",
      "scene_composition_and_environmental_sync": "",
      "typography_and_graphic_overlays": "",
      "physical_constraints": [],
      "negative_spatial_constraints": [],
      "amazon_compliance_constraints": []
    },
    "image_generation_prompt": ""
  }
}
```

---

# Improved Flow-ready master prompt template

This is the reusable version of flow working prompt.

```
System/Role Context:
Act as an expert commercial product photographer and digital composite designer creating a high-converting, Amazon-compliant [IMAGE_ROLE].

Technical Specifications:
- Aspect Ratio: Vertical 9:16
- Resolution Target: 1080 × 1920 pixels
- Lighting Profile: [use style_lock / lighting_profile]
- Product Scale: [use exact dimensions if confirmed; otherwise use relative_scale from spatial_image_contract]
- Lens / Camera Feel: [use camera_profile or 50mm product photography unless scene requires interior POV]

Model Photographer's POV:
Describe the real-world camera position as if a photographer is physically standing or seated in the scene. Specify:
- where the photographer/camera is
- what direction the camera points
- what is foreground, midground, and background
- what object is in focus
- what is softly blurred

Binding Geometry:
Describe where the product exists in real 3D space:
- support surface or mounting point
- product face orientation
- how the product body attaches, rests, hangs, stands, or connects
- how scale relates to nearby real objects

Orientation & Spatial Sync:
Use the product's extracted geometry:
- front face:
- rear face:
- top face:
- side face:
- primary functional axis:
- screen/display orientation:
- mounting/support logic:

Scene Composition & Environmental Sync:
State what exists outside or around the product. If the product has a screen, display, lens, mirror, transparent chamber, light beam, nozzle, or sensor:
- anything shown on the product's display must physically correspond to the real environment or functional direction
- do not create contradictory screen/environment content

Typography & Graphic Overlays:
Use only permitted Amazon secondary-image text. Text must not obstruct the product. For hero images, use N/A and no text.

Physical Constraints:
List strict physics rules:
- product cannot float unless explicitly suspended by visible support
- lens/functional axis must point toward what it is capturing/affecting
- screen content must match real-world line of sight
- component placement must match reference images
- exact dimensions must not be invented

Negative Spatial Constraints:
- Do not copy-paste the reference image as a flat sticker.
- Do not use impossible rotations.
- Do not show screen content that contradicts the visible environment.
- Do not place real-world objects outside the product's plausible field of view while showing them on the screen.
- Do not invent unverified product components, accessories, ports, lights, labels, or markings.

Amazon Compliance Constraints:
- Use only verified product features and included accessories.
- Maintain accurate product shape, color, materials, and markings.
- Keep all text legible and secondary to the product.
- Do not use exaggerated claims, fake awards, badges, or unverifiable guarantees.
```

---

---

# Validation after PATCH_SET_11

## Static validation

Expected markers:

```json
{
  "required_markers": [
    "spatial_image_contract",
    "spatial_scene_brief",
    "model_photographer_pov",
    "binding_geometry",
    "orientation_and_spatial_sync",
    "scene_composition_and_environmental_sync",
    "negative_spatial_constraints",
    "IMAGE_CONTENT_PATH"
  ]
}
```

## Targeted dry-run

Run prompt step `13` only with mocked browser response or against browser if preferred.

Expected output:

```json
{
  "image_strategy": {
    "image_number": 2,
    "spatial_scene_brief": {
      "model_photographer_pov": "present",
      "binding_geometry": "present",
      "orientation_and_spatial_sync": "present",
      "physical_constraints": "non-empty",
      "negative_spatial_constraints": "non-empty"
    },
    "image_generation_prompt": "contains System/Role Context, Technical Specifications, Model Photographer's POV, Binding Geometry, Orientation & Spatial Sync, Scene Composition & Environmental Sync"
  }
}
```

## Full prompt validation

Re-run through prompt generation only:

```powershell
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 23
```

Expected:

```json
{
  "image_prompts_json_count": 7,
  "all_image_prompts_have_spatial_scene_brief": true,
  "all_image_generation_prompts_have_photographer_pov": true,
  "all_image_generation_prompts_have_physical_constraints": true,
  "image_content_json_exists": true
}
```

---