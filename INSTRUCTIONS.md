# INSTRUCTIONS

CONFIRMATION REQUIRED: Before each PATCH and Validation.

YES

## Current source status before PATCH_11H

```json
{
  "workflow_orchestrator": {
    "PATCH_11A_to_11G": "PRESENT",
    "schema_image_prompt_requires_spatial_scene_brief": true,
    "IMAGE_CONTENT_PATH": true,
    "build_spatial_image_contract": true,
    "build_image_prompt_context_includes_spatial_image_contract": true,
    "build_image_generation_context_includes_spatial_image_contract": true
  },
  "prompts_md": {
    "PATCH_11H": "NOT_PRESENT",
    "spatial_scene_brief_mentions": 0,
    "spatial_contract_prompt_wording": "MISSING",
    "image_prompt_output_schemas": "OLD_SCHEMA"
  }
}
```

The current `prompts.md` still uses the old image prompt output schemas for PROMPT `11/13/15/17/19/21/23`; each schema ends at `image_generation_prompt` and does not instruct the browser model to emit `spatial_scene_brief`.

The script already expects `spatial_scene_brief` inside `schema_image_prompt(...)`, so the correct fix is **prompt-doc alignment only**, not another orchestrator patch.

---

# PATCH_11H — Prompt docs: enforce spatial_scene_brief for image prompt steps

## Purpose

Align `docs/prompts.md` with the already-patched runtime schema.

This patch affects only:

```
docs/prompts.md
```

It does **not** touch:

```json
[
  "workflow_orchestrator.py",
  "image context router",
  "image generation backend",
  "browser selector logic",
  "cooldown pacing",
  "step numbering",
  "Flow backend"
]
```

---

## PATCH_11H dry-run expectation

```json
{
  "patch_id": "PATCH_11H",
  "target_file": "docs/prompts.md",
  "expected_prompt_sections": ["11", "13", "15", "17", "19", "21", "23"],
  "expected_spatial_image_contract_include_insertions": 7,
  "expected_spatial_contract_instruction_insertions": 7,
  "expected_output_schema_replacements": 7,
  "halt_if_any_count_is_not_expected": true
}
```

---

# PATCH_11H application script

Run from repo root:

```powershell
@'
from pathlib import Path
import re

path = Path("docs/prompts.md")
text = path.read_text(encoding="utf-8")

TARGET_PROMPTS = ["11", "13", "15", "17", "19", "21", "23"]

spatial_instruction_block = """
**SPATIAL IMAGE PROMPT CONTRACT**
Use IMAGE_CONTEXT_JSON.spatial_image_contract as the controlling physical-scene contract.

The image_strategy output MUST include a spatial_scene_brief object with all required fields below.

The image_generation_prompt MUST be written as a photographer-grade scene-construction brief and must incorporate these exact conceptual sections in natural language:
- System/Role Context
- Technical Specifications
- Model Photographer's POV
- Binding Geometry
- Orientation & Spatial Sync
- Scene Composition & Environmental Sync
- Typography & Graphic Overlays
- Physical Constraints
- Negative Spatial Constraints
- Amazon Compliance Constraints

Rules for spatial grounding:
1. Anchor the product in a real physical location or studio setup.
2. State the camera/photographer POV explicitly.
3. Preserve product geometry, component placement, mounting/support logic, and real-world scale from spatial_image_contract.
4. If exact physical dimensions are unconfirmed, do not invent dimensions; use relative scale only.
5. Explain how the product's functional axis interacts with real space: lens direction, display direction, nozzle direction, handle direction, light direction, speaker direction, cutting direction, or equivalent product-specific axis.
6. If the product has a display, lens, mirror, camera, sensor, light, transparent chamber, or reflection, visible content must physically agree with the real environment and product orientation.
7. Do not copy-paste the reference image as a flat sticker. Reconstruct the product as a coherent 3D object.
8. Do not create impossible rotations, floating components, unsupported mounts, contradictory screen/environment content, or invented components.

"""

spatial_scene_schema = '''   "spatial_scene_brief": {
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
   "image_generation_prompt": ""'''

include_insertions = 0
instruction_insertions = 0
schema_replacements = 0

pattern = re.compile(r"(?ms)(^# PROMPT (?P<id>\\d+)\\b.*?)(?=^# PROMPT \\d+\\b|\\Z)")

def patch_section(section: str, prompt_id: str) -> str:
    global include_insertions, instruction_insertions, schema_replacements

    original = section

    if "- spatial_image_contract" not in section:
        if "- image_task\n" not in section:
            raise SystemExit(f"PATCH_11H_FAILED: PROMPT {prompt_id} missing - image_task include anchor")
        section = section.replace("- image_task\n", "- image_task\n- spatial_image_contract\n", 1)
        include_insertions += 1

    if "**SPATIAL IMAGE PROMPT CONTRACT**" not in section:
        if "**WORKFLOW MODE**" in section:
            section = section.replace("**WORKFLOW MODE**", spatial_instruction_block + "**WORKFLOW MODE**", 1)
        elif "WORKFLOW MODE" in section:
            section = section.replace("WORKFLOW MODE", spatial_instruction_block + "WORKFLOW MODE", 1)
        else:
            raise SystemExit(f"PATCH_11H_FAILED: PROMPT {prompt_id} missing WORKFLOW MODE anchor")
        instruction_insertions += 1

    old_schema_tail = '''   "visual_design_direction": "",
   "image_generation_prompt": ""'''

    if old_schema_tail not in section:
        raise SystemExit(f"PATCH_11H_FAILED: PROMPT {prompt_id} missing old schema tail")

    section = section.replace(
        old_schema_tail,
        '''   "visual_design_direction": "",
''' + spatial_scene_schema,
        1,
    )
    schema_replacements += 1

    if section == original:
        raise SystemExit(f"PATCH_11H_FAILED: PROMPT {prompt_id} unchanged")

    return section

def repl(match: re.Match) -> str:
    prompt_id = match.group("id")
    section = match.group(0)
    if prompt_id in TARGET_PROMPTS:
        return patch_section(section, prompt_id)
    return section

new_text = pattern.sub(repl, text)

expected = 7
if include_insertions != expected:
    raise SystemExit(f"PATCH_11H_FAILED: include_insertions={include_insertions}, expected={expected}")
if instruction_insertions != expected:
    raise SystemExit(f"PATCH_11H_FAILED: instruction_insertions={instruction_insertions}, expected={expected}")
if schema_replacements != expected:
    raise SystemExit(f"PATCH_11H_FAILED: schema_replacements={schema_replacements}, expected={expected}")

path.write_text(new_text, encoding="utf-8")

print("PATCH_11H_APPLIED")
print(f"include_insertions={include_insertions}")
print(f"instruction_insertions={instruction_insertions}")
print(f"schema_replacements={schema_replacements}")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_11H_APPLIED
include_insertions=7
instruction_insertions=7
schema_replacements=7
```

---

# PATCH_11H validation

## H-Validation 1 — compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```
PASS / no output
```

---

## H-Validation 2 — static prompt-doc validation

```powershell
@'
from pathlib import Path
import re

text = Path("docs/prompts.md").read_text(encoding="utf-8")
target_prompts = ["11", "13", "15", "17", "19", "21", "23"]

sections = {}
matches = list(re.finditer(r"(?m)^# PROMPT (\\d+)\\b", text))
for i, m in enumerate(matches):
    prompt_id = m.group(1)
    start = m.start()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
    sections[prompt_id] = text[start:end]

required_schema_fields = [
    '"spatial_scene_brief": {',
    '"system_role_context": ""',
    '"technical_specifications": ""',
    '"model_photographer_pov": ""',
    '"binding_geometry": ""',
    '"orientation_and_spatial_sync": ""',
    '"scene_composition_and_environmental_sync": ""',
    '"typography_and_graphic_overlays": ""',
    '"physical_constraints": []',
    '"negative_spatial_constraints": []',
    '"amazon_compliance_constraints": []',
]

required_instruction_markers = [
    "- spatial_image_contract",
    "**SPATIAL IMAGE PROMPT CONTRACT**",
    "System/Role Context",
    "Technical Specifications",
    "Model Photographer's POV",
    "Binding Geometry",
    "Orientation & Spatial Sync",
    "Scene Composition & Environmental Sync",
    "Typography & Graphic Overlays",
    "Physical Constraints",
    "Negative Spatial Constraints",
    "Amazon Compliance Constraints",
]

for prompt_id in target_prompts:
    section = sections.get(prompt_id)
    assert section, f"missing PROMPT {prompt_id}"

    for marker in required_instruction_markers:
        assert marker in section, f"PROMPT {prompt_id} missing instruction marker: {marker}"

    for marker in required_schema_fields:
        assert marker in section, f"PROMPT {prompt_id} missing schema marker: {marker}"

assert text.count('"spatial_scene_brief": {') == 7, text.count('"spatial_scene_brief": {')
assert text.count("**SPATIAL IMAGE PROMPT CONTRACT**") == 7, text.count("**SPATIAL IMAGE PROMPT CONTRACT**")

print("PATCH_11H_PROMPT_DOC_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_11H_PROMPT_DOC_STATIC_OK
```

---

## H-Validation 3 — runtime schema/static alignment check

```powershell
@'
import workflow_orchestrator as w

target = {
    "11": (1, "What is this product?", "Hero Product Image"),
    "13": (2, "Why do I need this product?", "Core Benefit Image"),
    "15": (3, "What problem does this product solve?", "Problem Solution Image"),
    "17": (4, "When would I use this product?", "Lifestyle Use Image"),
    "19": (5, "What technology makes this product better?", "Technology Feature Image"),
    "21": (6, "How easy is it to install or use?", "Ease of Use / Installation Image"),
    "23": (7, "What specifications matter?", "Specifications Infographic"),
}

for step_id, (image_number, buyer_question, image_type) in target.items():
    schema = w.schema_image_prompt(image_number, buyer_question, image_type)
    image_strategy = schema["properties"]["image_strategy"]
    required = image_strategy["required"]
    props = image_strategy["properties"]

    assert "spatial_scene_brief" in required, step_id
    brief = props["spatial_scene_brief"]
    for field in [
        "system_role_context",
        "technical_specifications",
        "model_photographer_pov",
        "binding_geometry",
        "orientation_and_spatial_sync",
        "scene_composition_and_environmental_sync",
        "typography_and_graphic_overlays",
        "physical_constraints",
        "negative_spatial_constraints",
        "amazon_compliance_constraints",
    ]:
        assert field in brief["required"], (step_id, field)

print("PATCH_11H_SCHEMA_ALIGNMENT_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_11H_SCHEMA_ALIGNMENT_OK
```

---

# Clean full prompt validation after PATCH_11H

Do not run image generation. This is prompt validation only.

## Clean workspace prep

```powershell
Remove-Item output\workflow_state.json -Force -ErrorAction SilentlyContinue
Remove-Item output\image_prompts.json -Force -ErrorAction SilentlyContinue
Remove-Item output\image_content.json -Force -ErrorAction SilentlyContinue
Remove-Item output\logs\execution.jsonl -Force -ErrorAction SilentlyContinue
```

## Run through prompt generation

```powershell
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 23
```

Expected process result:

```json
{
  "exit_status": 0,
  "last_completed_step": "23",
  "image_prompts_json_exists": true,
  "image_content_json_exists": true
}
```

---

# Final PATCH_SET_11 quality gate

Run this after the clean `--stop-after 23` finishes:

```powershell
@'
import json
from pathlib import Path

state = json.loads(Path("output/workflow_state.json").read_text(encoding="utf-8"))
image_prompts = json.loads(Path("output/image_prompts.json").read_text(encoding="utf-8"))
image_content = json.loads(Path("output/image_content.json").read_text(encoding="utf-8"))

assert state.get("last_completed_step") == "23", state.get("last_completed_step")
assert len(image_prompts) == 7, len(image_prompts)
assert len(image_content.get("image_prompts", [])) == 7, len(image_content.get("image_prompts", []))
assert isinstance(image_content.get("spatial_image_contract"), dict), "missing spatial_image_contract"
assert image_content["spatial_image_contract"], "empty spatial_image_contract"

required_brief_fields = [
    "system_role_context",
    "technical_specifications",
    "model_photographer_pov",
    "binding_geometry",
    "orientation_and_spatial_sync",
    "scene_composition_and_environmental_sync",
    "typography_and_graphic_overlays",
    "physical_constraints",
    "negative_spatial_constraints",
    "amazon_compliance_constraints",
]

required_prompt_markers = [
    "System/Role Context",
    "Technical Specifications",
    "Model Photographer",
    "Binding Geometry",
    "Orientation",
    "Spatial",
    "Physical",
    "Negative",
    "Amazon",
]

seen_numbers = []

for idx, prompt in enumerate(image_prompts, start=1):
    assert prompt.get("image_number") == idx, (idx, prompt.get("image_number"))
    seen_numbers.append(prompt.get("image_number"))

    brief = prompt.get("spatial_scene_brief")
    assert isinstance(brief, dict), f"image {idx} missing spatial_scene_brief"

    for field in required_brief_fields:
        assert field in brief, f"image {idx} missing {field}"

    assert isinstance(brief["physical_constraints"], list) and brief["physical_constraints"], f"image {idx} physical_constraints empty"
    assert isinstance(brief["negative_spatial_constraints"], list) and brief["negative_spatial_constraints"], f"image {idx} negative_spatial_constraints empty"
    assert isinstance(brief["amazon_compliance_constraints"], list) and brief["amazon_compliance_constraints"], f"image {idx} amazon_compliance_constraints empty"

    generation_prompt = prompt.get("image_generation_prompt", "")
    assert isinstance(generation_prompt, str) and len(generation_prompt) > 300, f"image {idx} prompt too short"

    # The natural language can vary; require enough exact section markers to prove the master-prompt contract is present.
    marker_hits = sum(1 for marker in required_prompt_markers if marker.lower() in generation_prompt.lower())
    assert marker_hits >= 6, f"image {idx} lacks master-section grounding markers; hits={marker_hits}"

assert seen_numbers == [1, 2, 3, 4, 5, 6, 7], seen_numbers

print("PATCH_SET_11_FULL_PROMPT_VALIDATION_OK")
print("last_completed_step=23")
print("image_prompts_count=7")
print("image_content_prompts_count=7")
print("all_have_spatial_scene_brief=True")
print("all_have_physical_constraints=True")
print("all_have_negative_spatial_constraints=True")
print("all_have_amazon_compliance_constraints=True")
print("all_generation_prompts_have_spatial_master_contract=True")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_SET_11_FULL_PROMPT_VALIDATION_OK
last_completed_step=23
image_prompts_count=7
image_content_prompts_count=7
all_have_spatial_scene_brief=True
all_have_physical_constraints=True
all_have_negative_spatial_constraints=True
all_have_amazon_compliance_constraints=True
all_generation_prompts_have_spatial_master_contract=True
```

---

# Current expected state after this patch

```json
{
  "PATCH_11H": "READY_TO_APPLY",
  "expected_result_after_validation": {
    "PATCH_SET_11": "CONFIRMED",
    "Flow_backend_work": "NEXT_AFTER_CONFIRMATION",
    "STATE_17": "STILL_BLOCKED_UNTIL_FLOW_BACKEND_DECISION_AND_VALIDATION"
  }
}
```

This is the corrected `PATCH_11H`: it is narrow, deterministic, prompt-doc-only, and it avoids the previous mistake of using a targeted dry-run that wrote files and contaminated the validation workspace.