# INSTRUCTIONS

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

- Confirmed Validation B passed.
- Confirmed Validation C passed.
- Confirmed the only remaining blocker before Validation D is the browser image path still falling back to OpenAI API.
- Providing only the specific fix: `PATCH_10H`.

The current file still has this browser-backend image fallback:

```python
if self.image_fallback is None:
    if OpenAI is None:
        fail("MISSING_DEPENDENCY", "Python package 'openai' is required for image generation.")
    self.image_fallback = OpenAIPromptExecutionAdapter(OpenAI())
return self.image_fallback.execute_image(...)
```

That is the exact defect. It must be replaced with a browser/CDP image-generation workflow.

---

# PATCH_10H — Replace browser image API fallback with browser/CDP image workflow

## Purpose

Use the already launched and authenticated Chrome/CDP session for STEP `12` image generation.

This patch does **not** change:

```json
[
  "Validation B result",
  "Validation C result",
  "STEP 11 behavior",
  "PATCH_SET_02 routing",
  "PATCH_SET_03 prompt wording",
  "OpenAIPromptExecutionAdapter behavior for non-browser backend",
  "run_step image-generation context handoff"
]
```

It only fixes `BrowserPromptExecutionAdapter.execute_image(...)`.

---

## PATCH_10H1 — Add browser image-generation timeout control

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10H1",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
BROWSER_REQUIRE_PARSEABLE_JSON = os.getenv("BROWSER_REQUIRE_PARSEABLE_JSON", "1") == "1"
```

### REPLACE WITH

```python
BROWSER_REQUIRE_PARSEABLE_JSON = os.getenv("BROWSER_REQUIRE_PARSEABLE_JSON", "1") == "1"
BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS = float(os.getenv("BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS", "300"))
```

---

## PATCH_10H2 — Replace browser image API fallback

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10H2",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

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

### REPLACE WITH

```python
    def _extract_generation_source_images(
        self,
        generation_context: Optional[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
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

        return source_images, missing_images

    def _attach_images_for_generation(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        json_log(
            level="INFO",
            message="Browser image generation reference attachment started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_image_reference_attach_start",
                "source_image_count": len(source_images),
            },
        )

        attach_selectors = [
            "button[aria-label*='Attach']",
            "button[aria-label*='attach']",
            "button:has-text('Attach')",
            "button[data-testid*='attach']",
        ]

        try:
            if page.locator("input[type=file]").count() == 0:
                for sel in attach_selectors:
                    btn = page.locator(sel).first
                    if btn.count() and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(250)
                        break
        except Exception:
            pass

        try:
            inp = page.locator("input[type=file]").first
            if not inp.count():
                fail(
                    "BROWSER_IMAGE_ATTACH_INPUT_MISSING",
                    "Could not find browser file input for image generation reference images.",
                    field="browser_file_input",
                    expected="input[type=file]",
                    actual=f"url={getattr(page, 'url', '')}",
                    stage="PROCESSING",
                )

            inp.set_input_files(source_images, timeout=self.action_timeout_ms)
            page.wait_for_timeout(1000)

            json_log(
                level="INFO",
                message="Browser image generation reference images attached",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "browser_image_reference_attach_success",
                    "source_image_count": len(source_images),
                },
            )
        except SystemExit:
            raise
        except Exception as e:
            fail(
                "BROWSER_IMAGE_REFERENCE_ATTACH_FAILED",
                "Failed to attach reference images for browser image generation.",
                field="generation_context.source_images",
                expected="reference images attached through browser file input",
                actual=str(e)[:1000],
                stage="PROCESSING",
            )

    def _submit_image_generation_prompt(self, page, prompt: str) -> int:
        before_assistant_count = page.locator("[data-message-author-role='assistant']").count()
        before_user_count = page.locator("[data-message-author-role='user']").count()

        box = self._input_box(page)
        json_log(
            level="DEBUG",
            message="Browser image prompt input box resolved",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"operation": "browser_image_input_box_resolved"},
        )

        box.click()
        try:
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass

        try:
            box.fill(prompt, timeout=self.action_timeout_ms)
        except Exception:
            try:
                page.keyboard.insert_text(prompt)
            except Exception:
                box.type(prompt, delay=0, timeout=self.action_timeout_ms)

        def try_click_send() -> bool:
            selectors = [
                "button[data-testid='send-button']",
                "button[aria-label*='Send']",
                "button[aria-label*='send']",
                "button:has-text('Send')",
            ]
            for sel in selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() and btn.is_visible() and btn.is_enabled():
                        btn.click()
                        return True
                except Exception:
                    pass
            try:
                btn = page.get_by_role("button", name=re.compile(r"send", re.I)).first
                if btn.count() and btn.is_visible() and btn.is_enabled():
                    btn.click()
                    return True
            except Exception:
                pass
            return False

        json_log(
            level="INFO",
            message="Browser image generation prompt submission attempted",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_image_prompt_submit_attempt",
                "prompt_chars": len(prompt or ""),
            },
        )

        page.keyboard.press("Enter")
        send_deadline = time.time() + 20.0
        ctrl_enter_tried = False

        while time.time() < send_deadline:
            if page.locator("[data-message-author-role='user']").count() > before_user_count:
                break
            try:
                if not ctrl_enter_tried:
                    page.keyboard.press("Control+Enter")
                    ctrl_enter_tried = True
            except Exception:
                pass
            try_click_send()
            page.wait_for_timeout(250)

        return before_assistant_count

    def _capture_latest_browser_generated_image_base64(self, page, before_assistant_count: int) -> str:
        deadline = time.time() + BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS
        last_assistant_excerpt = ""

        json_log(
            level="INFO",
            message="Browser image generation wait started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_image_generation_wait_start",
                "timeout_seconds": BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS,
                "before_assistant_count": before_assistant_count,
            },
        )

        while time.time() < deadline:
            assistant_count = page.locator("[data-message-author-role='assistant']").count()

            if assistant_count > before_assistant_count:
                assistant = page.locator("[data-message-author-role='assistant']").last

                try:
                    last_assistant_excerpt = assistant.inner_text(timeout=5000).strip()[:1000]
                except Exception:
                    last_assistant_excerpt = ""

                try:
                    image_locator = assistant.locator("img").last
                    if image_locator.count() and image_locator.is_visible():
                        page.wait_for_timeout(1500)

                        src = ""
                        try:
                            src = image_locator.get_attribute("src") or ""
                        except Exception:
                            src = ""

                        if src.startswith("data:image") and "," in src:
                            image_base64 = src.split(",", 1)[1]
                            json_log(
                                level="INFO",
                                message="Browser generated image captured from data URL",
                                stage="PROCESSING",
                                status="IN_PROGRESS",
                                context={
                                    "operation": "browser_generated_image_captured_data_url",
                                    "assistant_count": assistant_count,
                                    "image_base64_chars": len(image_base64),
                                },
                            )
                            return image_base64

                        screenshot_bytes = image_locator.screenshot(timeout=self.action_timeout_ms)
                        image_base64 = base64.b64encode(screenshot_bytes).decode("ascii")

                        json_log(
                            level="INFO",
                            message="Browser generated image captured from rendered image",
                            stage="PROCESSING",
                            status="IN_PROGRESS",
                            context={
                                "operation": "browser_generated_image_captured_screenshot",
                                "assistant_count": assistant_count,
                                "image_base64_chars": len(image_base64),
                            },
                        )
                        return image_base64
                except Exception:
                    pass

            try:
                stop_btn = page.get_by_role("button", name=re.compile(r"stop generating", re.I)).first
                if stop_btn.count() and stop_btn.is_visible():
                    page.wait_for_timeout(1000)
                    continue
            except Exception:
                pass

            page.wait_for_timeout(1000)

        fail(
            "BROWSER_IMAGE_GENERATION_TIMEOUT",
            "Timed out waiting for generated image in browser assistant response.",
            field="browser_generated_image",
            expected="visible generated image in latest assistant message",
            actual=last_assistant_excerpt[:1000],
            stage="PROCESSING",
        )

    def execute_image(
        self,
        prompt: str,
        size: str = "1024x1536",
        generation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        source_images, missing_images = self._extract_generation_source_images(generation_context)

        if missing_images and IMAGE_REFERENCE_STRICT:
            fail(
                "IMAGE_REFERENCE_IMAGE_MISSING",
                "One or more reference images listed in generation_context.source_images do not exist.",
                field="generation_context.source_images",
                expected="all listed reference image paths exist",
                actual=json.dumps(missing_images, ensure_ascii=False),
                stage="PROCESSING",
            )

        if IMAGE_REFERENCE_STRICT and not source_images:
            fail(
                "IMAGE_REFERENCE_IMAGES_NOT_AVAILABLE",
                "Strict browser image generation requires source_images at the adapter boundary.",
                field="generation_context.source_images",
                expected="at least one existing reference image path",
                actual=str((generation_context or {}).get("source_images") if isinstance(generation_context, dict) else None),
                stage="PROCESSING",
            )

        json_log(
            level="INFO",
            message="Browser image generation started",
            stage="PROCESSING",
            status="STARTED",
            context={
                "operation": "browser_image_generation_start",
                "source_image_count": len(source_images),
                "size": size,
                "has_generation_context": generation_context is not None,
            },
        )

        page = self._page()

        if os.getenv("BROWSER_NEW_CHAT_EACH_PROMPT", "1") == "1":
            self._start_new_chat(page)
        elif not self._prepared_chat and os.getenv("BROWSER_NEW_CHAT", "1") == "1":
            self._start_new_chat(page)
            self._prepared_chat = True

        self._attach_images_for_generation(page, source_images)
        before_assistant_count = self._submit_image_generation_prompt(page, prompt)
        image_base64 = self._capture_latest_browser_generated_image_base64(page, before_assistant_count)

        return {
            "image_base64": image_base64,
            "revised_prompt": None,
            "source_images_used": source_images,
        }
```

---

# PATCH_10H validation

## H-Validation 1 — compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```
PASS / no output
```

---

## H-Validation 2 — static browser fallback removal check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

browser_class = text.split("class BrowserPromptExecutionAdapter", 1)[1].split("def _json_only_retry_prompt", 1)[0]
browser_execute_image = browser_class.split("def execute_image(", 1)[1]

required = [
    "BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS",
    "Browser image generation started",
    "Browser image generation reference images attached",
    "Browser image generation prompt submission attempted",
    "Browser generated image captured from rendered image",
    "source_images_used",
]

for marker in required:
    assert marker in text, marker

for forbidden in [
    "self.image_fallback = OpenAIPromptExecutionAdapter(OpenAI())",
    "return self.image_fallback.execute_image(",
    "MISSING_DEPENDENCY\", \"Python package 'openai' is required for image generation.",
]:
    assert forbidden not in browser_execute_image, forbidden

print("PATCH_10H_BROWSER_IMAGE_FALLBACK_REMOVAL_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_10H_BROWSER_IMAGE_FALLBACK_REMOVAL_OK
```

---

CONFIRMATION REQUIRED:
YES.

# Validation D — corrected browser/CDP actual STEP 12 runtime

Run this only after H-Validation 1 and H-Validation 2 pass.

```powershell
$env:SKIP_IMAGES="0"
$env:IMAGE_REFERENCE_STRICT="1"
$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"
$env:BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS="300"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --resume --enable-image-generation --stop-after 12
```

Expected:

```json
{
  "expected": [
    "resume starts at 12",
    "Image generation adapter handoff started",
    "Browser image generation started",
    "source_image_count >= 1",
    "Browser image generation reference images attached",
    "Browser image generation prompt submission attempted",
    "Browser generated image captured from rendered image OR data URL",
    "output/generated_images/image_12.png exists",
    "generated_image_1 exists in workflow_state.json",
    "generated_image_1.generated_image.source_images_used is non-empty",
    "last_completed_step=12",
    "OUTPUT/SUCCESS"
  ],
  "forbidden": [
    "OPENAI_API_KEY requirement",
    "OpenAI image edit requested with reference images",
    "Python package 'openai' is required for image generation",
    "MISSING_DEPENDENCY from BrowserPromptExecutionAdapter.execute_image"
  ]
}
```

## Current sequence status

```json
{
  "Validation_B": "PASS",
  "Validation_C": "PASS",
  "PATCH_10H": "READY_TO_APPLY",
  "next": [
    "apply PATCH_10H",
    "run H-Validation 1",
    "run H-Validation 2",
    "run Validation D"
  ],
  "STATE_17": "BLOCKED_UNTIL_VALIDATION_D_PASS"
}
```