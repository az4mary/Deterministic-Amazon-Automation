# INSTRUCTIONS

- Proceeding with `PATCH_SET_10 — Image generation adapter context handoff`.
- Targeting only the even-step image-generation adapter boundary.
- First runtime target remains STEP `12`.

This follows the uploaded controlling plan: the remaining gap is that `generation_context` is already built, but not handed to the image execution adapter.

OpenAI’s current Image API supports image edits from one or more source images plus a prompt, and the Python API accepts a file or sequence of image files for GPT image models; GPT image models accept text and image inputs. This supports PATCH_SET_10’s adapter handoff design. ([OpenAI Developers](https://developers.openai.com/api/reference/resources/images/methods/edit/?utm_source=chatgpt.com))

---

# PATCH_SET_10 — Image generation adapter context handoff

## Scope

Target file:

```
workflow_orchestrator.py
```

Do **not** modify:

```json
[
  "docs/prompts.md",
  "STEP 11 behavior",
  "PROMPT 11 behavior",
  "PATCH_SET_02 image prompt routing",
  "PATCH_SET_03 prompt wording",
  "normal text steps 01A-10"
]
```

---

## PATCH_10A — Add strict reference-image handoff control

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10A",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
```

### REPLACE WITH

```python
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
IMAGE_REFERENCE_STRICT = os.getenv("IMAGE_REFERENCE_STRICT", "1") == "1"
```

---

## PATCH_10B — Extend base adapter image interface

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10B",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    def execute_image(self, prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
        raise NotImplementedError
```

### REPLACE WITH

```python
    def execute_image(
        self,
        prompt: str,
        size: str = "1024x1536",
        generation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError
```

---

## PATCH_10C — Replace OpenAI image adapter with context-aware implementation

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10C",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    def execute_image(self, prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
        response = self.client.responses.create(
            model=IMAGE_MODEL,
            input=prompt,
            tools=[{"type": "image_generation"}],
            tool_choice={"type": "image_generation"},
        )
        image_data = [
            output.result
            for output in response.output
            if getattr(output, "type", None) == "image_generation_call"
        ]
        revised_prompt = None
        for output in response.output:
            if getattr(output, "type", None) == "image_generation_call":
                revised_prompt = getattr(output, "revised_prompt", None)
                break
        if not image_data:
            fail("IMAGE_GENERATION_FAILED", "No image returned by model.")
        return {"image_base64": image_data[0], "revised_prompt": revised_prompt}
```

### REPLACE WITH

```python
    def execute_image(
        self,
        prompt: str,
        size: str = "1024x1536",
        generation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        source_images: List[str] = []
        missing_images: List[str] = []

        if isinstance(generation_context, dict):
            raw_source_images = generation_context.get("source_images") or []
            if isinstance(raw_source_images, list):
                for item in raw_source_images:
                    if not isinstance(item, str):
                        continue
                    path = Path(item)
                    if path.exists() and path.is_file():
                        source_images.append(str(path))
                    else:
                        missing_images.append(item)

        if missing_images and IMAGE_REFERENCE_STRICT:
            fail(
                "IMAGE_REFERENCE_IMAGE_MISSING",
                "One or more reference images listed in generation_context.source_images do not exist.",
                field="generation_context.source_images",
                expected="all listed reference image paths exist",
                actual=json.dumps(missing_images, ensure_ascii=False),
                stage="PROCESSING",
            )

        if isinstance(generation_context, dict) and IMAGE_REFERENCE_STRICT and not source_images:
            fail(
                "IMAGE_REFERENCE_IMAGES_NOT_AVAILABLE",
                "Strict image generation requires source_images at the adapter boundary.",
                field="generation_context.source_images",
                expected="at least one existing reference image path",
                actual=str(generation_context.get("source_images")),
                stage="PROCESSING",
            )

        if source_images:
            json_log(
                level="INFO",
                message="OpenAI image edit requested with reference images",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "openai_image_edit",
                    "source_image_count": len(source_images),
                    "image_model": IMAGE_MODEL,
                    "size": size,
                },
            )

            files = []
            try:
                for image_path in source_images:
                    files.append(open(image_path, "rb"))

                response = self.client.images.edit(
                    model=IMAGE_MODEL,
                    image=files,
                    prompt=prompt,
                    size=size,
                    n=1,
                )
            finally:
                for f in files:
                    try:
                        f.close()
                    except Exception:
                        pass

            data = getattr(response, "data", None) or []
            if not data:
                fail("IMAGE_GENERATION_FAILED", "No image returned by image edit model.", stage="PROCESSING")

            first = data[0]
            image_base64 = getattr(first, "b64_json", None)
            revised_prompt = getattr(first, "revised_prompt", None)

            if isinstance(first, dict):
                image_base64 = image_base64 or first.get("b64_json")
                revised_prompt = revised_prompt or first.get("revised_prompt")

            if not image_base64:
                fail(
                    "IMAGE_GENERATION_FAILED",
                    "Image edit model returned no base64 image payload.",
                    field="image_base64",
                    expected="b64_json",
                    actual=str(first)[:1000],
                    stage="PROCESSING",
                )

            return {
                "image_base64": image_base64,
                "revised_prompt": revised_prompt,
                "source_images_used": source_images,
            }

        json_log(
            level="WARNING",
            message="OpenAI image generation requested without reference images",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "openai_image_generate_without_references",
                "image_model": IMAGE_MODEL,
                "size": size,
                "strict": IMAGE_REFERENCE_STRICT,
            },
        )

        response = self.client.responses.create(
            model=IMAGE_MODEL,
            input=prompt,
            tools=[{"type": "image_generation"}],
            tool_choice={"type": "image_generation"},
        )
        image_data = [
            output.result
            for output in response.output
            if getattr(output, "type", None) == "image_generation_call"
        ]
        revised_prompt = None
        for output in response.output:
            if getattr(output, "type", None) == "image_generation_call":
                revised_prompt = getattr(output, "revised_prompt", None)
                break
        if not image_data:
            fail("IMAGE_GENERATION_FAILED", "No image returned by model.", stage="PROCESSING")
        return {"image_base64": image_data[0], "revised_prompt": revised_prompt}
```

---

## PATCH_10D — Extend browser adapter image interface and pass context to fallback

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10D",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    def execute_image(self, prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
        if self.image_fallback is None:
            # Delay OpenAI client initialization until image generation is requested so
            # browser-backed text steps don't require OPENAI_API_KEY.
            if OpenAI is None:
                fail("MISSING_DEPENDENCY", "Python package 'openai' is required for image generation.")
            self.image_fallback = OpenAIPromptExecutionAdapter(OpenAI())
        return self.image_fallback.execute_image(prompt, size=size)
```

### REPLACE WITH

```python
    def execute_image(
        self,
        prompt: str,
        size: str = "1024x1536",
        generation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if self.image_fallback is None:
            # Delay OpenAI client initialization until image generation is requested so
            # browser-backed text steps don't require OPENAI_API_KEY.
            if OpenAI is None:
                fail("MISSING_DEPENDENCY", "Python package 'openai' is required for image generation.")
            self.image_fallback = OpenAIPromptExecutionAdapter(OpenAI())
        return self.image_fallback.execute_image(
            prompt,
            size=size,
            generation_context=generation_context,
        )
```

---

## PATCH_10E — Extend `call_image_generation(...)` adapter boundary

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10E",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
def call_image_generation(prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
    json_log("step_start", kind="image_generation", size=size)
    return get_execution_adapter().execute_image(prompt, size=size)
```

### REPLACE WITH

```python
def call_image_generation(
    prompt: str,
    size: str = "1024x1536",
    generation_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    source_images = []
    image_task = {}

    if isinstance(generation_context, dict):
        raw_source_images = generation_context.get("source_images") or []
        if isinstance(raw_source_images, list):
            source_images = [p for p in raw_source_images if isinstance(p, str)]
        raw_image_task = generation_context.get("image_task") or {}
        if isinstance(raw_image_task, dict):
            image_task = raw_image_task

    json_log(
        level="INFO",
        message="Image generation adapter handoff started",
        stage="PROCESSING",
        status="STARTED",
        context={
            "kind": "image_generation",
            "size": size,
            "image_number": image_task.get("image_number"),
            "image_type": image_task.get("image_type"),
            "source_image_count": len(source_images),
            "has_generation_context": generation_context is not None,
        },
    )
    return get_execution_adapter().execute_image(
        prompt,
        size=size,
        generation_context=generation_context,
    )
```

---

## PATCH_10F — Pass `generation_context` from even image-generation steps

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10F",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        result = call_image_generation(prompt)
```

### REPLACE WITH

```python
        result = call_image_generation(prompt, generation_context=generation_context)
```

---

## PATCH_10G — Persist adapter source-image usage metadata

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10G",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
                "saved_path": saved_path,
                "revised_prompt": result.get("revised_prompt"),
```

### REPLACE WITH

```python
                "saved_path": saved_path,
                "revised_prompt": result.get("revised_prompt"),
                "source_images_used": result.get("source_images_used", []),
```

---

# PATCH_SET_10 validation checkpoint

```json
{
  "patch_set_id": "PATCH_SET_10",
  "expected_behavior": "Even image-generation steps pass the slim generation_context into the image adapter, source_images are visible at the adapter boundary, and STEP 12 can use reference images through the image edit path when available.",
  "expected_present": {
    "IMAGE_REFERENCE_STRICT": true,
    "generation_context: Optional[Dict[str, Any]] = None": true,
    "OpenAI image edit requested with reference images": true,
    "Image generation adapter handoff started": true,
    "source_images_used": true,
    "result = call_image_generation(prompt, generation_context=generation_context)": true
  },
  "forbidden_changes": [
    "Do not modify docs/prompts.md",
    "Do not alter STEP 11 behavior",
    "Do not attach raw binary reference images to STEP 11",
    "Do not send full workflow_state.json to image-generation adapter",
    "Do not change image prompt routing from PATCH_SET_02",
    "Do not change prompt wording from PATCH_SET_03",
    "Do not proceed to STATE 17 before STEP 12 actual image generation passes"
  ]
}
```

---

# Validation commands

## Validation A — compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

---

## Validation B — static marker validation

```powershell
D:\TOOLS\Python314\python.exe - <<'PY'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "IMAGE_REFERENCE_STRICT",
    "generation_context: Optional[Dict[str, Any]] = None",
    "OpenAI image edit requested with reference images",
    "Image generation adapter handoff started",
    "source_images_used",
    "result = call_image_generation(prompt, generation_context=generation_context)",
]

for marker in required:
    assert marker in text, marker

for forbidden in [
    "result = call_image_generation(prompt)\n",
]:
    assert forbidden not in text, forbidden

print("PATCH_SET_10_STATIC_VALIDATION_OK")
PY
```

---

## Validation C — focused STEP 12 dry-run contract test

Run this from a state that already passed through STEP `11`.

```powershell
$env:SKIP_IMAGES="0"
$env:IMAGE_REFERENCE_STRICT="1"

D:\TOOLS\Python314\python.exe - <<'PY'
import base64
import copy
import workflow_orchestrator as w

state = w.load_json(w.STATE_PATH)
assert state.get("last_completed_step") == "11", state.get("last_completed_step")
assert "image_strategy_1" in state, "missing image_strategy_1"

calls = {}

orig_call_image_generation = w.call_image_generation
orig_save_image = w.save_image
orig_save_json_atomic = w.save_json_atomic
orig_apply_step_wait = w.apply_step_wait

def fake_call_image_generation(prompt, size="1024x1536", generation_context=None):
    calls["prompt"] = prompt
    calls["size"] = size
    calls["generation_context"] = copy.deepcopy(generation_context)

    assert generation_context is not None
    assert generation_context["image_task"]["image_number"] == 1
    assert generation_context["image_task"]["image_type"] == "Hero Product Image"
    assert generation_context["image_generation_prompt"] == prompt
    assert isinstance(generation_context.get("source_images"), list)
    assert len(generation_context["source_images"]) >= 1

    forbidden = [
        "outputs",
        "source_payload",
        "amazon_product_title",
        "amazon_bullet_points",
        "amazon_product_description",
        "customer_faq",
        "social_media_posts",
    ]
    for key in forbidden:
        assert key not in generation_context, key

    return {
        "image_base64": base64.b64encode(b"DRY_RUN_IMAGE_BYTES").decode("ascii"),
        "revised_prompt": None,
        "source_images_used": generation_context["source_images"],
    }

def fake_save_image(image_base64, name):
    calls["save_image_name"] = name
    calls["save_image_base64_len"] = len(image_base64)
    return "DRY_RUN_NO_FILE_WRITE/" + name

def fake_save_json_atomic(path, data):
    calls["save_json_path"] = str(path)
    calls["saved_last_completed_step"] = data.get("last_completed_step")

def fake_apply_step_wait(kind):
    calls["wait_kind"] = kind

try:
    w.call_image_generation = fake_call_image_generation
    w.save_image = fake_save_image
    w.save_json_atomic = fake_save_json_atomic
    w.apply_step_wait = fake_apply_step_wait

    step = w.Step("12", "image_generate", None, "generated_image_1", None)
    w.run_step(step, state)

finally:
    w.call_image_generation = orig_call_image_generation
    w.save_image = orig_save_image
    w.save_json_atomic = orig_save_json_atomic
    w.apply_step_wait = orig_apply_step_wait

assert calls["generation_context"]["image_task"]["image_number"] == 1
assert calls["generation_context"]["image_generation_prompt"] == calls["prompt"]
assert calls["save_image_name"] == "image_12.png"
assert calls["wait_kind"] == "image_generate"
assert state["last_completed_step"] == "12"
assert "generated_image_1" in state
assert state["generated_image_1"]["generated_image"]["image_number"] == 1
assert state["generated_image_1"]["generated_image"]["source_images_used"]

print("PATCH_SET_10_STEP_12_DRY_RUN_OK")
print("step=12")
print("image_number=1")
print("uses_image_strategy_1_prompt=True")
print("passes_generation_context_to_call_image_generation=True")
print("source_images_available_at_adapter_boundary=True")
print("does_not_pass_full_workflow_state_to_image_adapter=True")
print("generated_image_1_written_to_state=True")
PY
```

---

## Validation D — actual STEP 12 runtime

Only run after Validation C passes.

```powershell
$env:OPENAI_API_KEY="YOUR_KEY_HERE"
$env:SKIP_IMAGES="0"
$env:IMAGE_REFERENCE_STRICT="1"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --resume --enable-image-generation --stop-after 12
```

Expected:

```json
{
  "expected": [
    "resume starts at 12",
    "Image generation adapter handoff started",
    "source_image_count >= 1",
    "OpenAI image edit requested with reference images",
    "output/generated_images/image_12.png exists",
    "generated_image_1 exists in workflow_state.json",
    "generated_image_1.generated_image.source_images_used is non-empty",
    "last_completed_step=12",
    "OUTPUT/SUCCESS"
  ]
}
```

---

## Current status after issuing PATCH_SET_10

```json
{
  "STATE": "10",
  "PATCH_SET_10": "READY_TO_APPLY",
  "STATE_17": "BLOCKED_UNTIL_STEP_12_RUNTIME_PASS",
  "next_required_result_from_you": [
    "PATCH_SET_10 apply report",
    "compile result",
    "static marker validation result",
    "STEP 12 dry-run contract result",
    "actual STEP 12 runtime result"
  ]
}
```