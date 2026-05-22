# PATCH_12K — Flow composer attachment + prompt submission hardening

* Proceed with **PATCH_12K**.
* Scope: **Flow reference attachment-to-composer + Flow prompt-box submission only**.
* Do **not** touch image capture, metadata persistence, prompt docs, cooldowns, or step numbering.

Evidence: STEP 7 passed Flow session reuse, Flow readiness, model selection, and initial upload, but failed because references were added to Flow/gallery instead of the active composer, then `_submit_flow_prompt()` timed out at `prompt_box.click(...)`.  Current code logs reference success immediately after `file_input.set_input_files(...)`, before proving the images are usable in the composer. 

---

# PATCH_12K — Flow composer attachment + prompt submission hardening

## STEP 1 — PATCH_12K1: add Flow composer controls

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12K1",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### Apply

Insert after:

```python
FLOW_OUTPUT_COUNT = int(os.getenv("FLOW_OUTPUT_COUNT", "1"))
```

Add:

```python
FLOW_UI_CLICK_TIMEOUT_MS = int(os.getenv("FLOW_UI_CLICK_TIMEOUT_MS", "10000"))
FLOW_REFERENCE_COMPOSER_TIMEOUT_SECONDS = float(os.getenv("FLOW_REFERENCE_COMPOSER_TIMEOUT_SECONDS", "90"))
FLOW_PROMPT_READY_TIMEOUT_SECONDS = float(os.getenv("FLOW_PROMPT_READY_TIMEOUT_SECONDS", "90"))
```

---

## STEP 2 — PATCH_12K2: add Flow composer helper methods

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12K2",
  "expected_insert_anchor_count": 1,
  "expected_existing_helper_count": 0,
  "halt_if_insert_anchor_count_is_not": 1
}
```

### Insert immediately before:

```python
    def _attach_reference_images(self, page, source_images: List[str]) -> None:
```

### Add:

```python
    def _flow_click_first(self, page, selectors: List[str], *, label: str, force: bool = False) -> bool:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() and locator.is_visible() and locator.is_enabled():
                    locator.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=force)
                    json_log(
                        level="DEBUG",
                        message=f"Flow UI clicked {label}",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "flow_ui_click_first",
                            "label": label,
                            "selector": selector,
                            "force": force,
                        },
                    )
                    return True
            except Exception:
                continue
        return False

    def _dismiss_flow_transient_overlays(self, page) -> None:
        for key in ["Escape", "Escape"]:
            try:
                page.keyboard.press(key)
                page.wait_for_timeout(250)
            except Exception:
                pass

    def _finalize_flow_reference_attachment_to_composer(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        json_log(
            level="INFO",
            message="Flow reference composer attachment verification started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_reference_composer_attach_verify_start",
                "source_image_count": len(source_images),
            },
        )

        # Flow may upload files into the project/gallery first. These controls attempt
        # to attach or insert the uploaded/selected assets into the active composer.
        action_selectors = [
            "button:has-text('Add to prompt')",
            "button:has-text('Add selected')",
            "button:has-text('Add selection')",
            "button:has-text('Use selected')",
            "button:has-text('Use selection')",
            "button:has-text('Insert')",
            "button:has-text('Attach')",
            "button:has-text('Done')",
            "button:has-text('Add')",
            "[role='button']:has-text('Add to prompt')",
            "[role='button']:has-text('Add selected')",
            "[role='button']:has-text('Use selected')",
            "[role='button']:has-text('Insert')",
            "[role='button']:has-text('Attach')",
            "[role='button']:has-text('Done')",
            "[role='button']:has-text('Add')",
            "button[aria-label*='Add']",
            "button[aria-label*='Use']",
            "button[aria-label*='Insert']",
            "button[aria-label*='Attach']",
            "button[aria-label*='Done']",
        ]

        deadline = time.time() + FLOW_REFERENCE_COMPOSER_TIMEOUT_SECONDS
        clicked_any = False
        while time.time() < deadline:
            if self._flow_click_first(page, action_selectors, label="reference_attach_to_composer"):
                clicked_any = True
                page.wait_for_timeout(1500)
                break

            # If the gallery requires explicit selection, click the largest visible
            # thumbnails/cards, then try action controls again.
            media_selectors = [
                "[role='dialog'] img",
                "[role='dialog'] canvas",
                "[data-testid*='asset'] img",
                "[data-testid*='media'] img",
                "[data-testid*='gallery'] img",
                "main img",
            ]
            for selector in media_selectors:
                try:
                    collection = page.locator(selector)
                    count = min(collection.count(), len(source_images) + 3)
                    for idx in range(count):
                        item = collection.nth(idx)
                        if not item.is_visible():
                            continue
                        box = item.bounding_box() or {}
                        if float(box.get("width", 0) or 0) < 40 or float(box.get("height", 0) or 0) < 40:
                            continue
                        item.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                        clicked_any = True
                        page.wait_for_timeout(300)
                except Exception:
                    continue

            if self._flow_click_first(page, action_selectors, label="reference_attach_to_composer_after_select"):
                clicked_any = True
                page.wait_for_timeout(1500)
                break

            page.wait_for_timeout(1000)

        self._dismiss_flow_transient_overlays(page)

        if not clicked_any:
            json_log(
                level="WARNING",
                message="Flow reference images uploaded but composer attach control was not confirmed",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_reference_gallery_only_warning",
                    "source_image_count": len(source_images),
                },
            )
        else:
            json_log(
                level="INFO",
                message="Flow reference images attached to composer",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_reference_images_attached_to_composer",
                    "source_image_count": len(source_images),
                },
            )

    def _find_flow_prompt_box(self, page):
        prompt_selectors = [
            "textarea[placeholder*='prompt' i]",
            "textarea[aria-label*='prompt' i]",
            "[contenteditable='true'][aria-label*='prompt' i]",
            "div[role='textbox'][aria-label*='prompt' i]",
            "[contenteditable='true']",
            "div[role='textbox']",
            "textarea",
        ]

        deadline = time.time() + FLOW_PROMPT_READY_TIMEOUT_SECONDS
        last_error = ""

        while time.time() < deadline:
            for selector in prompt_selectors:
                try:
                    collection = page.locator(selector)
                    count = min(collection.count(), 10)
                    for idx in range(count):
                        candidate = collection.nth(idx)
                        if not candidate.is_visible():
                            continue
                        box = candidate.bounding_box() or {}
                        width = float(box.get("width", 0) or 0)
                        height = float(box.get("height", 0) or 0)
                        if width < 120 or height < 24:
                            continue
                        return candidate
                except Exception as exc:
                    last_error = str(exc)[:300]
            page.wait_for_timeout(500)

        fail(
            "FLOW_PROMPT_INPUT_MISSING",
            "Could not find Flow prompt input for image generation.",
            field="flow_prompt_input",
            expected="visible Flow prompt textarea/textbox/contenteditable composer",
            actual=f"url={getattr(page, 'url', '')}; last_error={last_error}",
            stage="PROCESSING",
        )

    def _fill_flow_prompt_box(self, page, prompt_box, prompt: str) -> None:
        try:
            prompt_box.scroll_into_view_if_needed(timeout=FLOW_UI_CLICK_TIMEOUT_MS)
        except Exception:
            pass

        try:
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
        except Exception:
            try:
                handle = prompt_box.element_handle(timeout=FLOW_UI_CLICK_TIMEOUT_MS)
                page.evaluate("(el) => el.focus()", handle)
            except Exception:
                pass

        try:
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass

        try:
            prompt_box.fill(prompt, timeout=FLOW_UI_CLICK_TIMEOUT_MS)
        except Exception:
            try:
                page.keyboard.insert_text(prompt)
            except Exception:
                prompt_box.type(prompt, delay=0, timeout=self.action_timeout_ms)

        json_log(
            level="INFO",
            message="Flow prompt box filled",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_prompt_box_filled",
                "prompt_chars": len(prompt or ""),
            },
        )
```

---

## STEP 3 — PATCH_12K3: replace Flow reference attachment method

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12K3",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
```

### Replace entire method:

From:

```python
    def _attach_reference_images(self, page, source_images: List[str]) -> None:
```

Through the line immediately before:

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
```

### Replacement:

```python
    def _attach_reference_images(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        json_log(
            level="INFO",
            message="Flow reference image attachment started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_reference_image_attach_start",
                "source_image_count": len(source_images),
            },
        )

        attach_selectors = [
            "button[aria-label*='Upload']",
            "button[aria-label*='upload']",
            "button[aria-label*='Ingredient']",
            "button[aria-label*='ingredient']",
            "button[aria-label*='Reference']",
            "button[aria-label*='reference']",
            "button:has-text('Upload')",
            "button:has-text('Ingredient')",
            "button:has-text('Reference')",
            "button:has-text('Add media')",
            "[role='button']:has-text('Upload')",
            "[role='button']:has-text('Ingredient')",
            "[role='button']:has-text('Reference')",
            "[role='button']:has-text('Add media')",
        ]

        try:
            if page.locator("input[type=file]").count() == 0:
                self._flow_click_first(page, attach_selectors, label="open_reference_upload", force=True)
        except Exception:
            pass

        try:
            file_input = page.locator("input[type=file]").last
            if not file_input.count():
                fail(
                    "FLOW_REFERENCE_ATTACH_INPUT_MISSING",
                    "Could not find Flow file input for reference image upload.",
                    field="flow_file_input",
                    expected="input[type=file] after opening Flow upload or ingredient control",
                    actual=f"url={getattr(page, 'url', '')}",
                    stage="PROCESSING",
                )

            file_input.set_input_files(source_images, timeout=self.action_timeout_ms)
            page.wait_for_timeout(3000)

            json_log(
                level="INFO",
                message="Flow reference images uploaded",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_reference_image_upload_success",
                    "source_image_count": len(source_images),
                },
            )

            self._finalize_flow_reference_attachment_to_composer(page, source_images)

        except SystemExit:
            raise
        except Exception as exc:
            fail(
                "FLOW_REFERENCE_IMAGE_ATTACH_FAILED",
                "Failed to attach reference images to Flow.",
                field="generation_context.source_images",
                expected="reference images uploaded and attached to Flow composer",
                actual=str(exc)[:1000],
                stage="PROCESSING",
            )

```

---

## STEP 4 — PATCH_12K4: replace Flow prompt submission method

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12K4",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
```

### Replace entire method:

From:

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
```

Through the line immediately before:

```python
    def _capture_flow_generated_image_base64(self, page) -> str:
```

### Replacement:

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
        json_log(
            level="INFO",
            message="Flow model selection started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_model_selection_start",
                "target_model": FLOW_IMAGE_MODEL,
                "strict": FLOW_MODEL_STRICT,
            },
        )

        model_visible = False
        model_selectors = [
            f"button:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='button']:has-text('{FLOW_IMAGE_MODEL}')",
            f"text={FLOW_IMAGE_MODEL}",
            "button[aria-label*='model']",
            "button[aria-label*='Model']",
            "[role='button'][aria-label*='model']",
            "[role='button'][aria-label*='Model']",
        ]

        for selector in model_selectors:
            try:
                candidate = page.locator(selector).first
                if not candidate.count() or not candidate.is_visible():
                    continue
                candidate.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                page.wait_for_timeout(500)
                model_visible = True
                break
            except Exception:
                continue

        if not model_visible:
            try:
                model_option = page.get_by_text(FLOW_IMAGE_MODEL, exact=False).first
                if model_option.count() and model_option.is_visible():
                    model_option.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    page.wait_for_timeout(500)
                    model_visible = True
            except Exception:
                pass

        if not model_visible:
            if FLOW_MODEL_STRICT:
                json_log(
                    level="ERROR",
                    message="Flow model not available",
                    stage="PROCESSING",
                    status="FAILED",
                    context={
                        "operation": "flow_model_not_available",
                        "target_model": FLOW_IMAGE_MODEL,
                    },
                )
                fail(
                    "FLOW_MODEL_NOT_AVAILABLE",
                    "Required Flow image model is not visible or selectable in the Flow UI.",
                    field="FLOW_IMAGE_MODEL",
                    expected=f"{FLOW_IMAGE_MODEL} visible/selectable in Flow model menu",
                    actual=f"url={getattr(page, 'url', '')}",
                    stage="PROCESSING",
                )

            json_log(
                level="WARNING",
                message="Flow model selection skipped",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_model_selection_skipped",
                    "target_model": FLOW_IMAGE_MODEL,
                },
            )
        else:
            json_log(
                level="INFO",
                message="Flow model selected",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_model_selected",
                    "target_model": FLOW_IMAGE_MODEL,
                },
            )

        self._dismiss_flow_transient_overlays(page)
        prompt_box = self._find_flow_prompt_box(page)
        self._fill_flow_prompt_box(page, prompt_box, prompt)

        generate_selectors = [
            "button:has-text('Generate')",
            "button[aria-label*='Generate']",
            "button[aria-label*='generate']",
            "[role='button']:has-text('Generate')",
            "button:has-text('Create')",
            "button[aria-label*='Create']",
            "button[aria-label*='create']",
            "[role='button']:has-text('Create')",
        ]

        if self._flow_click_first(page, generate_selectors, label="flow_generate_button", force=True):
            json_log(
                level="INFO",
                message="Flow image prompt submitted",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_prompt_submitted",
                    "prompt_chars": len(prompt or ""),
                    "target_model": FLOW_IMAGE_MODEL,
                },
            )
            return

        try:
            page.keyboard.press("Control+Enter")
            json_log(
                level="INFO",
                message="Flow image prompt submitted",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_prompt_submitted_keyboard",
                    "prompt_chars": len(prompt or ""),
                    "target_model": FLOW_IMAGE_MODEL,
                },
            )
            return
        except Exception as exc:
            fail(
                "FLOW_PROMPT_SUBMIT_FAILED",
                "Could not submit Flow prompt with visible generate/create button or keyboard shortcut.",
                field="flow_generate_button",
                expected="enabled Flow generate/create control",
                actual=str(exc)[:1000],
                stage="PROCESSING",
            )

```

---

# PATCH_12K validation

## STEP 5 — K-Validation 1: compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

## STEP 6 — K-Validation 2: static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "FLOW_UI_CLICK_TIMEOUT_MS",
    "FLOW_REFERENCE_COMPOSER_TIMEOUT_SECONDS",
    "FLOW_PROMPT_READY_TIMEOUT_SECONDS",
    "def _flow_click_first",
    "def _dismiss_flow_transient_overlays",
    "def _finalize_flow_reference_attachment_to_composer",
    "def _find_flow_prompt_box",
    "def _fill_flow_prompt_box",
    "Flow reference images uploaded",
    "Flow reference images attached to composer",
    "Flow prompt box filled",
]

for marker in required:
    assert marker in text, marker

for old_marker in [
    "prompt_box.click(timeout=self.action_timeout_ms)",
]:
    assert old_marker not in text, old_marker

print("PATCH_12K_FLOW_COMPOSER_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12K_FLOW_COMPOSER_STATIC_OK
```

## STEP 7 — K-Validation 3: no-browser routing sanity

```powershell
$env:IMAGE_EXECUTION_BACKEND="flow_browser"

@'
import workflow_orchestrator as w

w.IMAGE_EXECUTION_ADAPTER = None
w.TEXT_EXECUTION_ADAPTER = w.BrowserPromptExecutionAdapter(
    w.BROWSER_CDP_URL,
    w.BROWSER_CHAT_URL,
    w.BROWSER_ACTION_TIMEOUT_MS,
)

adapter = w.get_image_execution_adapter()

assert isinstance(adapter, w.FlowBrowserImageGenerationAdapter)
assert hasattr(adapter, "_finalize_flow_reference_attachment_to_composer")
assert hasattr(adapter, "_find_flow_prompt_box")
assert hasattr(adapter, "_fill_flow_prompt_box")

print("PATCH_12K_FLOW_COMPOSER_ROUTING_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12K_FLOW_COMPOSER_ROUTING_OK
```

---

# Resume STEP 7 after PATCH_12K

Run the same smoke test:

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

## Expected checks

```json
{
  "expected": [
    "resume starts at step 12",
    "Image generation adapter handoff started",
    "Flow adapter reused shared browser session",
    "Flow page ready",
    "Flow reference images uploaded",
    "Flow reference images attached to composer",
    "Flow model selected",
    "Flow prompt box filled",
    "Flow image prompt submitted",
    "Flow generated image captured",
    "output/generated_images/image_12.png exists",
    "generated_image_1.generation_backend=flow_browser",
    "generated_image_1.generation_model=Nano Banana 2",
    "last_completed_step=12",
    "OUTPUT/SUCCESS"
  ],
  "forbidden": [
    "Playwright Sync API inside the asyncio loop",
    "FLOW_IMAGE_BACKEND_NOT_IMPLEMENTED",
    "OpenAI image generation",
    "ChatGPT browser image generation",
    "Locator.click: Timeout 120000ms exceeded",
    "prompt_box.click(timeout=self.action_timeout_ms)"
  ]
}
```

## Decision rule

```json
{
  "if_STEP_7_passes": "PATCH_12K_CONFIRMED; proceed to Validation 6 full Flow run",
  "if_STEP_7_fails_before_prompt_submission": "patch only Flow composer/reference attach logic",
  "if_STEP_7_fails_after_prompt_submission": "patch only Flow generated-image capture logic"
}
```

# PATCH_12L — Flow prompt composer discovery/activation

* Proceed with **PATCH_12L**.
* Scope: **Flow prompt-composer discovery/activation only**.
* Do **not** change reference upload, image capture, metadata persistence, prompt docs, cooldowns, or step numbering.

Current blocker: `FLOW_PROMPT_INPUT_MISSING`; Flow project URL is reachable, but `_find_flow_prompt_box(...)` cannot discover a visible Flow prompt composer. 

---

## STEP 1 — PATCH_12L1: add Flow prompt surface activation helper

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12L1",
  "expected_insert_anchor_count": 1,
  "expected_existing_helper_count": 0,
  "halt_if_insert_anchor_count_is_not": 1
}
```

### Insert immediately before

```python
    def _find_flow_prompt_box(self, page):
```

### Add

```python
    def _flow_prompt_surface_summary(self, page) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "url": getattr(page, "url", ""),
            "textarea_count": 0,
            "textbox_count": 0,
            "contenteditable_count": 0,
            "input_text_count": 0,
            "visible_button_texts": [],
        }

        try:
            summary["textarea_count"] = page.locator("textarea").count()
        except Exception:
            pass

        try:
            summary["textbox_count"] = page.locator("[role='textbox']").count()
        except Exception:
            pass

        try:
            summary["contenteditable_count"] = page.locator("[contenteditable='true']").count()
        except Exception:
            pass

        try:
            summary["input_text_count"] = page.locator("input[type='text'], input:not([type])").count()
        except Exception:
            pass

        try:
            buttons = page.locator("button, [role='button']")
            count = min(buttons.count(), 30)
            texts: List[str] = []
            for idx in range(count):
                try:
                    button = buttons.nth(idx)
                    if button.is_visible():
                        text = (button.inner_text(timeout=500) or "").strip()
                        aria = button.get_attribute("aria-label") or ""
                        label = text or aria
                        if label:
                            texts.append(label[:80])
                except Exception:
                    continue
            summary["visible_button_texts"] = texts[:20]
        except Exception:
            pass

        return summary

    def _activate_flow_prompt_surface(self, page) -> None:
        self._dismiss_flow_transient_overlays(page)

        activation_selectors = [
            "button:has-text('Text to image')",
            "[role='button']:has-text('Text to image')",
            "button:has-text('Create image')",
            "[role='button']:has-text('Create image')",
            "button:has-text('New image')",
            "[role='button']:has-text('New image')",
            "button:has-text('Start creating')",
            "[role='button']:has-text('Start creating')",
            "button:has-text('Image')",
            "[role='button']:has-text('Image')",
            "button:has-text('Prompt')",
            "[role='button']:has-text('Prompt')",
            "button[aria-label*='Prompt']",
            "[role='button'][aria-label*='Prompt']",
            "button[aria-label*='Create']",
            "[role='button'][aria-label*='Create']",
            "button[aria-label*='New']",
            "[role='button'][aria-label*='New']",
        ]

        clicked = self._flow_click_first(
            page,
            activation_selectors,
            label="flow_prompt_surface_activation",
            force=True,
        )

        if clicked:
            page.wait_for_timeout(1500)
            json_log(
                level="INFO",
                message="Flow prompt surface activation attempted",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_prompt_surface_activation_attempted",
                    "summary": self._flow_prompt_surface_summary(page),
                },
            )
        else:
            json_log(
                level="DEBUG",
                message="Flow prompt surface activation controls not found",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_prompt_surface_activation_not_found",
                    "summary": self._flow_prompt_surface_summary(page),
                },
            )
```

---

## STEP 2 — PATCH_12L2: replace `_find_flow_prompt_box(...)`

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12L2",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
```

### Replace entire method

From:

```python
    def _find_flow_prompt_box(self, page):
```

Through the line immediately before:

```python
    def _fill_flow_prompt_box(self, page, prompt_box, prompt: str) -> None:
```

### Replacement

```python
    def _find_flow_prompt_box(self, page):
        self._activate_flow_prompt_surface(page)

        prompt_selectors = [
            "textarea[placeholder*='prompt' i]",
            "textarea[aria-label*='prompt' i]",
            "textarea[placeholder*='describe' i]",
            "textarea[aria-label*='describe' i]",
            "[contenteditable='true'][aria-label*='prompt' i]",
            "[contenteditable='true'][aria-label*='describe' i]",
            "div[role='textbox'][aria-label*='prompt' i]",
            "div[role='textbox'][aria-label*='describe' i]",
            "[data-lexical-editor='true']",
            ".ProseMirror",
            "[contenteditable='true']",
            "div[role='textbox']",
            "textarea",
            "input[type='text']",
            "input:not([type])",
        ]

        def candidate_is_usable(candidate) -> bool:
            try:
                if not candidate.is_visible():
                    return False
            except Exception:
                return False

            try:
                box = candidate.bounding_box() or {}
                width = float(box.get("width", 0) or 0)
                height = float(box.get("height", 0) or 0)
                if width < 120 or height < 20:
                    return False
            except Exception:
                return False

            try:
                disabled = candidate.get_attribute("disabled")
                readonly = candidate.get_attribute("readonly")
                aria_disabled = candidate.get_attribute("aria-disabled")
                input_type = (candidate.get_attribute("type") or "").lower()
                if disabled is not None or readonly is not None or aria_disabled == "true" or input_type == "file":
                    return False
            except Exception:
                pass

            return True

        def scan_scope(scope, scope_label: str):
            for selector in prompt_selectors:
                try:
                    collection = scope.locator(selector)
                    count = min(collection.count(), 15)
                    for idx in range(count):
                        candidate = collection.nth(idx)
                        if candidate_is_usable(candidate):
                            json_log(
                                level="INFO",
                                message="Flow prompt box discovered",
                                stage="PROCESSING",
                                status="COMPLETED",
                                context={
                                    "operation": "flow_prompt_box_discovered",
                                    "selector": selector,
                                    "scope": scope_label,
                                    "index": idx,
                                },
                            )
                            return candidate
                except Exception:
                    continue
            return None

        deadline = time.time() + FLOW_PROMPT_READY_TIMEOUT_SECONDS
        last_summary: Dict[str, Any] = {}
        last_activation = 0.0

        while time.time() < deadline:
            found = scan_scope(page, "page")
            if found is not None:
                return found

            try:
                for frame in page.frames:
                    if frame == page.main_frame:
                        continue
                    found = scan_scope(frame, f"frame:{getattr(frame, 'url', '')[:120]}")
                    if found is not None:
                        return found
            except Exception:
                pass

            now = time.time()
            if now - last_activation >= 5.0:
                last_activation = now
                self._activate_flow_prompt_surface(page)
                last_summary = self._flow_prompt_surface_summary(page)
                json_log(
                    level="DEBUG",
                    message="Flow prompt composer discovery continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "flow_prompt_box_discovery_continue",
                        "summary": last_summary,
                    },
                )

            page.wait_for_timeout(500)

        fail(
            "FLOW_PROMPT_INPUT_MISSING",
            "Could not find Flow prompt input for image generation.",
            field="flow_prompt_input",
            expected="visible Flow prompt textarea/textbox/contenteditable composer",
            actual=json.dumps(
                {
                    "url": getattr(page, "url", ""),
                    "summary": last_summary or self._flow_prompt_surface_summary(page),
                },
                ensure_ascii=False,
            ),
            stage="PROCESSING",
        )
```

---

## STEP 3 — PATCH_12L3: replace `_fill_flow_prompt_box(...)`

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12L3",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
```

### Replace entire method

From:

```python
    def _fill_flow_prompt_box(self, page, prompt_box, prompt: str) -> None:
```

Through the line immediately before:

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
```

### Replacement

```python
    def _fill_flow_prompt_box(self, page, prompt_box, prompt: str) -> None:
        try:
            prompt_box.scroll_into_view_if_needed(timeout=FLOW_UI_CLICK_TIMEOUT_MS)
        except Exception:
            pass

        try:
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
        except Exception:
            try:
                prompt_box.evaluate("(el) => el.focus()")
            except Exception:
                pass

        try:
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass

        filled = False

        try:
            prompt_box.fill(prompt, timeout=FLOW_UI_CLICK_TIMEOUT_MS)
            filled = True
        except Exception:
            pass

        if not filled:
            try:
                prompt_box.evaluate(
                    """
                    (el, value) => {
                      el.focus();
                      if ("value" in el) {
                        el.value = value;
                      } else {
                        el.textContent = value;
                      }
                      el.dispatchEvent(new InputEvent("input", {
                        bubbles: true,
                        cancelable: true,
                        inputType: "insertText",
                        data: value
                      }));
                      el.dispatchEvent(new Event("change", { bubbles: true }));
                    }
                    """,
                    prompt,
                )
                filled = True
            except Exception:
                pass

        if not filled:
            try:
                page.keyboard.insert_text(prompt)
                filled = True
            except Exception:
                prompt_box.type(prompt, delay=0, timeout=self.action_timeout_ms)
                filled = True

        try:
            value_len = prompt_box.evaluate(
                """
                (el) => {
                  if ("value" in el) return String(el.value || "").length;
                  return String(el.innerText || el.textContent || "").length;
                }
                """
            )
        except Exception:
            value_len = -1

        if value_len == 0:
            fail(
                "FLOW_PROMPT_INPUT_NOT_FILLED",
                "Flow prompt input was discovered but did not retain prompt text.",
                field="flow_prompt_input",
                expected="prompt text inserted into Flow composer",
                actual=f"value_len={value_len}; prompt_chars={len(prompt or '')}",
                stage="PROCESSING",
            )

        json_log(
            level="INFO",
            message="Flow prompt box filled",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_prompt_box_filled",
                "prompt_chars": len(prompt or ""),
                "detected_value_chars": value_len,
            },
        )
```

---

# PATCH_12L validation

## STEP 4 — L-Validation 1: compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

---

## STEP 5 — L-Validation 2: static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "def _flow_prompt_surface_summary",
    "def _activate_flow_prompt_surface",
    "Flow prompt surface activation attempted",
    "Flow prompt box discovered",
    "flow_prompt_box_discovery_continue",
    "FLOW_PROMPT_INPUT_NOT_FILLED",
    "Flow prompt box filled",
    "detected_value_chars",
]

for marker in required:
    assert marker in text, marker

for forbidden in [
    "prompt_box.click(timeout=self.action_timeout_ms)",
]:
    assert forbidden not in text, forbidden

print("PATCH_12L_FLOW_PROMPT_DISCOVERY_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12L_FLOW_PROMPT_DISCOVERY_STATIC_OK
```

---

## STEP 6 — L-Validation 3: no-browser method sanity

```powershell
$env:IMAGE_EXECUTION_BACKEND="flow_browser"

@'
import workflow_orchestrator as w

adapter = w.FlowBrowserImageGenerationAdapter(
    w.BROWSER_CDP_URL,
    w.FLOW_URL,
    w.BROWSER_ACTION_TIMEOUT_MS,
)

assert hasattr(adapter, "_flow_prompt_surface_summary")
assert hasattr(adapter, "_activate_flow_prompt_surface")
assert hasattr(adapter, "_find_flow_prompt_box")
assert hasattr(adapter, "_fill_flow_prompt_box")

print("PATCH_12L_FLOW_PROMPT_DISCOVERY_METHODS_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12L_FLOW_PROMPT_DISCOVERY_METHODS_OK
```

---

# PATCH_12M — Flow gallery attach + submit confirmation

* Proceed with **PATCH_12M**.
* Scope: **Flow gallery reference selection + attach-to-composer + submit confirmation only**.
* Do **not** patch image capture yet.

Reason: the Expected checklist says the run reached Flow, uploaded references to the gallery, selected Nano Banana 2, and filled the prompt box, but **did not attach the gallery image into the composer** and **did not actually submit the prompt**. The terminal timeout is downstream noise, not the first blocker. 

---

## STEP 1 — PATCH_12M1: add Flow submit/attach verification controls

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12M1",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
FLOW_PROMPT_READY_TIMEOUT_SECONDS = float(os.getenv("FLOW_PROMPT_READY_TIMEOUT_SECONDS", "90"))
```

### REPLACE WITH

```python
FLOW_PROMPT_READY_TIMEOUT_SECONDS = float(os.getenv("FLOW_PROMPT_READY_TIMEOUT_SECONDS", "90"))
FLOW_GALLERY_ATTACH_TIMEOUT_SECONDS = float(os.getenv("FLOW_GALLERY_ATTACH_TIMEOUT_SECONDS", "120"))
FLOW_SUBMIT_CONFIRM_TIMEOUT_SECONDS = float(os.getenv("FLOW_SUBMIT_CONFIRM_TIMEOUT_SECONDS", "45"))
FLOW_REFERENCE_ATTACH_STRICT = os.getenv("FLOW_REFERENCE_ATTACH_STRICT", "1") == "1"
```

---

## STEP 2 — PATCH_12M2: add gallery/composer verification helpers

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12M2",
  "expected_insert_anchor_count": 1,
  "expected_existing_helper_count": 0,
  "halt_if_insert_anchor_count_is_not": 1
}
```

### Insert immediately before

```python
    def _finalize_flow_reference_attachment_to_composer(self, page, source_images: List[str]) -> None:
```

### ADD

```python
    def _flow_visible_media_count(self, page, *, scope_label: str = "page") -> int:
        selectors = [
            "img",
            "canvas",
            "[role='img']",
            "[data-testid*='image']",
            "[data-testid*='asset']",
            "[data-testid*='media']",
            "[data-testid*='thumbnail']",
        ]
        seen = 0
        for selector in selectors:
            try:
                collection = page.locator(selector)
                count = min(collection.count(), 80)
                for idx in range(count):
                    item = collection.nth(idx)
                    if not item.is_visible():
                        continue
                    box = item.bounding_box() or {}
                    width = float(box.get("width", 0) or 0)
                    height = float(box.get("height", 0) or 0)
                    if width >= 40 and height >= 40:
                        seen += 1
            except Exception:
                continue
        return seen

    def _flow_composer_reference_count(self, page) -> int:
        composer_scopes = [
            "form",
            "[role='form']",
            "[data-testid*='composer']",
            "[data-testid*='prompt']",
            "[class*='composer']",
            "[class*='prompt']",
            "main",
        ]

        media_selectors = [
            "img",
            "canvas",
            "[role='img']",
            "[data-testid*='attachment']",
            "[data-testid*='chip']",
            "[data-testid*='asset']",
            "[data-testid*='media']",
            "[aria-label*='Remove']",
        ]

        max_seen = 0
        for scope_selector in composer_scopes:
            try:
                scopes = page.locator(scope_selector)
                scope_count = min(scopes.count(), 10)
                for sidx in range(scope_count):
                    scope = scopes.nth(sidx)
                    if not scope.is_visible():
                        continue
                    seen = 0
                    for media_selector in media_selectors:
                        try:
                            media = scope.locator(media_selector)
                            count = min(media.count(), 30)
                            for midx in range(count):
                                item = media.nth(midx)
                                if item.is_visible():
                                    box = item.bounding_box() or {}
                                    width = float(box.get("width", 0) or 0)
                                    height = float(box.get("height", 0) or 0)
                                    if width >= 16 and height >= 16:
                                        seen += 1
                        except Exception:
                            continue
                    max_seen = max(max_seen, seen)
            except Exception:
                continue

        return max_seen

    def _flow_reference_attach_summary(self, page) -> Dict[str, Any]:
        return {
            "url": getattr(page, "url", ""),
            "visible_media_count": self._flow_visible_media_count(page),
            "composer_reference_count": self._flow_composer_reference_count(page),
            "surface_summary": self._flow_prompt_surface_summary(page),
        }

    def _flow_select_gallery_assets(self, page, expected_count: int) -> int:
        gallery_selectors = [
            "[role='dialog'] img",
            "[role='dialog'] canvas",
            "[role='dialog'] [role='img']",
            "[data-testid*='gallery'] img",
            "[data-testid*='gallery'] canvas",
            "[data-testid*='asset'] img",
            "[data-testid*='media'] img",
            "[data-testid*='thumbnail'] img",
            "main img",
            "main canvas",
        ]

        selected = 0
        for selector in gallery_selectors:
            try:
                collection = page.locator(selector)
                count = min(collection.count(), max(expected_count + 5, 8))
                for idx in range(count):
                    if selected >= expected_count:
                        return selected
                    item = collection.nth(idx)
                    if not item.is_visible():
                        continue
                    box = item.bounding_box() or {}
                    width = float(box.get("width", 0) or 0)
                    height = float(box.get("height", 0) or 0)
                    if width < 48 or height < 48:
                        continue
                    item.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    selected += 1
                    page.wait_for_timeout(500)
            except Exception:
                continue
        return selected

    def _flow_click_attach_selected_to_composer(self, page) -> bool:
        attach_selectors = [
            "button:has-text('Add to prompt')",
            "[role='button']:has-text('Add to prompt')",
            "button:has-text('Add selected')",
            "[role='button']:has-text('Add selected')",
            "button:has-text('Use selected')",
            "[role='button']:has-text('Use selected')",
            "button:has-text('Insert selected')",
            "[role='button']:has-text('Insert selected')",
            "button:has-text('Attach selected')",
            "[role='button']:has-text('Attach selected')",
            "button:has-text('Add image')",
            "[role='button']:has-text('Add image')",
            "button:has-text('Use image')",
            "[role='button']:has-text('Use image')",
            "button:has-text('Insert')",
            "[role='button']:has-text('Insert')",
            "button:has-text('Attach')",
            "[role='button']:has-text('Attach')",
            "button:has-text('Done')",
            "[role='button']:has-text('Done')",
            "button:has-text('Add')",
            "[role='button']:has-text('Add')",
            "button[aria-label*='Add']",
            "button[aria-label*='Use']",
            "button[aria-label*='Insert']",
            "button[aria-label*='Attach']",
            "button[aria-label*='Done']",
        ]
        return self._flow_click_first(page, attach_selectors, label="gallery_attach_selected_to_composer", force=True)

    def _wait_for_flow_references_in_composer(self, page, expected_count: int) -> bool:
        deadline = time.time() + FLOW_GALLERY_ATTACH_TIMEOUT_SECONDS
        last_log = 0.0

        while time.time() < deadline:
            count = self._flow_composer_reference_count(page)
            if count >= max(1, min(expected_count, 2)):
                json_log(
                    level="INFO",
                    message="Flow reference composer attachment confirmed",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_reference_composer_attach_confirmed",
                        "composer_reference_count": count,
                        "expected_source_image_count": expected_count,
                    },
                )
                return True

            now = time.time()
            if now - last_log >= 5.0:
                last_log = now
                json_log(
                    level="DEBUG",
                    message="Flow reference composer attachment wait continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "flow_reference_composer_attach_wait_continue",
                        "summary": self._flow_reference_attach_summary(page),
                    },
                )

            page.wait_for_timeout(1000)

        return False

    def _flow_submit_started(self, page) -> bool:
        indicators = [
            "text=/generating/i",
            "text=/creating/i",
            "text=/queued/i",
            "text=/rendering/i",
            "text=/processing/i",
            "[aria-label*='Cancel']",
            "[aria-label*='Stop']",
            "button:has-text('Cancel')",
            "button:has-text('Stop')",
            "[role='progressbar']",
            "[data-testid*='progress']",
            "[data-testid*='generating']",
            "[class*='spinner']",
            "[class*='loading']",
        ]

        for selector in indicators:
            try:
                loc = page.locator(selector).first
                if loc.count() and loc.is_visible():
                    return True
            except Exception:
                continue

        return False

    def _wait_for_flow_submit_confirmation(self, page) -> bool:
        deadline = time.time() + FLOW_SUBMIT_CONFIRM_TIMEOUT_SECONDS
        last_log = 0.0

        while time.time() < deadline:
            if self._flow_submit_started(page):
                json_log(
                    level="INFO",
                    message="Flow prompt submission confirmed",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_prompt_submission_confirmed",
                        "summary": self._flow_prompt_surface_summary(page),
                    },
                )
                return True

            now = time.time()
            if now - last_log >= 5.0:
                last_log = now
                json_log(
                    level="DEBUG",
                    message="Flow prompt submission confirmation wait continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "flow_prompt_submit_confirm_wait_continue",
                        "summary": self._flow_prompt_surface_summary(page),
                    },
                )

            page.wait_for_timeout(1000)

        return False
```

---

## STEP 3 — PATCH_12M3: replace reference finalization method

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12M3",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
```

### Replace entire method

From:

```python
    def _finalize_flow_reference_attachment_to_composer(self, page, source_images: List[str]) -> None:
```

Through the line immediately before:

```python
    def _flow_prompt_surface_summary(self, page) -> Dict[str, Any]:
```

### Replacement

```python
    def _finalize_flow_reference_attachment_to_composer(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        expected_count = len(source_images)

        json_log(
            level="INFO",
            message="Flow reference composer attachment verification started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_reference_composer_attach_verify_start",
                "source_image_count": expected_count,
                "strict": FLOW_REFERENCE_ATTACH_STRICT,
            },
        )

        before_count = self._flow_composer_reference_count(page)

        selected_count = self._flow_select_gallery_assets(page, expected_count)
        clicked_attach = self._flow_click_attach_selected_to_composer(page)

        page.wait_for_timeout(1500)
        self._dismiss_flow_transient_overlays(page)

        attached = self._wait_for_flow_references_in_composer(page, expected_count)
        after_count = self._flow_composer_reference_count(page)

        if attached:
            json_log(
                level="INFO",
                message="Flow reference images attached to composer",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_reference_images_attached_to_composer",
                    "source_image_count": expected_count,
                    "selected_gallery_asset_count": selected_count,
                    "clicked_attach_control": clicked_attach,
                    "before_composer_reference_count": before_count,
                    "after_composer_reference_count": after_count,
                },
            )
            return

        context = {
            "operation": "flow_reference_gallery_attach_failed",
            "source_image_count": expected_count,
            "selected_gallery_asset_count": selected_count,
            "clicked_attach_control": clicked_attach,
            "before_composer_reference_count": before_count,
            "after_composer_reference_count": after_count,
            "summary": self._flow_reference_attach_summary(page),
        }

        if FLOW_REFERENCE_ATTACH_STRICT:
            fail(
                "FLOW_REFERENCE_NOT_ATTACHED_TO_COMPOSER",
                "Flow reference images were uploaded to the gallery but were not confirmed attached to the active composer.",
                field="flow_reference_composer",
                expected="uploaded gallery image selected and attached into prompt composer",
                actual=json.dumps(context, ensure_ascii=False),
                stage="PROCESSING",
            )

        json_log(
            level="WARNING",
            message="Flow reference images uploaded but composer attachment was not confirmed",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context=context,
        )
```

---

## STEP 4 — PATCH_12M4: strengthen prompt submission confirmation

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12M4",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND inside `_submit_flow_prompt(...)`

```python
        if self._flow_click_first(page, generate_selectors, label="flow_generate_button", force=True):
            json_log(
                level="INFO",
                message="Flow image prompt submitted",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_prompt_submitted",
                    "prompt_chars": len(prompt or ""),
                    "target_model": FLOW_IMAGE_MODEL,
                },
            )
            return

        try:
            page.keyboard.press("Control+Enter")
            json_log(
                level="INFO",
                message="Flow image prompt submitted",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_prompt_submitted_keyboard",
                    "prompt_chars": len(prompt or ""),
                    "target_model": FLOW_IMAGE_MODEL,
                },
            )
            return
        except Exception as exc:
            fail(
                "FLOW_PROMPT_SUBMIT_FAILED",
                "Could not submit Flow prompt with visible generate/create button or keyboard shortcut.",
                field="flow_generate_button",
                expected="enabled Flow generate/create control",
                actual=str(exc)[:1000],
                stage="PROCESSING",
            )
```

### REPLACE WITH

```python
        clicked_generate = self._flow_click_first(page, generate_selectors, label="flow_generate_button", force=True)

        if clicked_generate and self._wait_for_flow_submit_confirmation(page):
            json_log(
                level="INFO",
                message="Flow image prompt submitted",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_prompt_submitted",
                    "prompt_chars": len(prompt or ""),
                    "target_model": FLOW_IMAGE_MODEL,
                    "submit_method": "button",
                },
            )
            return

        try:
            page.keyboard.press("Control+Enter")
            if self._wait_for_flow_submit_confirmation(page):
                json_log(
                    level="INFO",
                    message="Flow image prompt submitted",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_prompt_submitted_keyboard",
                        "prompt_chars": len(prompt or ""),
                        "target_model": FLOW_IMAGE_MODEL,
                        "submit_method": "keyboard",
                    },
                )
                return
        except Exception:
            pass

        fail(
            "FLOW_PROMPT_SUBMIT_NOT_CONFIRMED",
            "Flow prompt text was filled but generation start was not confirmed.",
            field="flow_generate_button",
            expected="Flow generation indicator after button click or Control+Enter",
            actual=json.dumps(
                {
                    "clicked_generate": clicked_generate,
                    "summary": self._flow_prompt_surface_summary(page),
                    "reference_attach_summary": self._flow_reference_attach_summary(page),
                },
                ensure_ascii=False,
            ),
            stage="PROCESSING",
        )
```

---

# PATCH_12M validation

## STEP 5 — M-Validation 1: compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

---

## STEP 6 — M-Validation 2: static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "FLOW_GALLERY_ATTACH_TIMEOUT_SECONDS",
    "FLOW_SUBMIT_CONFIRM_TIMEOUT_SECONDS",
    "FLOW_REFERENCE_ATTACH_STRICT",
    "def _flow_composer_reference_count",
    "def _flow_select_gallery_assets",
    "def _flow_click_attach_selected_to_composer",
    "def _wait_for_flow_references_in_composer",
    "def _flow_submit_started",
    "def _wait_for_flow_submit_confirmation",
    "FLOW_REFERENCE_NOT_ATTACHED_TO_COMPOSER",
    "FLOW_PROMPT_SUBMIT_NOT_CONFIRMED",
    "Flow prompt submission confirmed",
]

for marker in required:
    assert marker in text, marker

for forbidden in [
    "Flow reference images attached to composer\",\n                stage=\"PROCESSING\",\n                status=\"COMPLETED\",\n                context={\n                    \"operation\": \"flow_reference_images_attached_to_composer\",\n                    \"source_image_count\": len(source_images)",
]:
    assert forbidden not in text, forbidden

print("PATCH_12M_FLOW_GALLERY_ATTACH_SUBMIT_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12M_FLOW_GALLERY_ATTACH_SUBMIT_STATIC_OK
```

---

## STEP 7 — M-Validation 3: no-browser method sanity

```powershell
$env:IMAGE_EXECUTION_BACKEND="flow_browser"

@'
import workflow_orchestrator as w

adapter = w.FlowBrowserImageGenerationAdapter(
    w.BROWSER_CDP_URL,
    w.FLOW_URL,
    w.BROWSER_ACTION_TIMEOUT_MS,
)

required = [
    "_flow_composer_reference_count",
    "_flow_reference_attach_summary",
    "_flow_select_gallery_assets",
    "_flow_click_attach_selected_to_composer",
    "_wait_for_flow_references_in_composer",
    "_flow_submit_started",
    "_wait_for_flow_submit_confirmation",
]

for name in required:
    assert hasattr(adapter, name), name

print("PATCH_12M_FLOW_GALLERY_ATTACH_SUBMIT_METHODS_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12M_FLOW_GALLERY_ATTACH_SUBMIT_METHODS_OK
```

---

# PATCH_12N — Flow uploaded-gallery asset selection refinement

* Proceed with **PATCH_12N**.
* Scope: **Flow uploaded-gallery asset selection refinement only**.
* Do **not** touch model selection, prompt fill, prompt submit, image capture, metadata, docs, or step numbering.

Current code selects gallery assets **before** opening the attach/gallery control, so `selected_gallery_asset_count=0` while the page still reports many visible media items. The next patch should open the relevant media/gallery surface first, then select uploaded media, then attach it. 

---

## STEP 1 — PATCH_12N1: add uploaded-media gallery helpers

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12N1",
  "expected_insert_anchor_count": 1,
  "expected_existing_helper_count": 0,
  "halt_if_insert_anchor_count_is_not": 1
}
```

### Insert immediately before

```python
    def _flow_select_gallery_assets(self, page, expected_count: int) -> int:
```

### Add

```python
    def _flow_open_uploaded_media_gallery(self, page) -> bool:
        open_selectors = [
            "button:has-text('View uploaded media')",
            "[role='button']:has-text('View uploaded media')",
            "button:has-text('Uploaded media')",
            "[role='button']:has-text('Uploaded media')",
            "button:has-text('All Media')",
            "[role='button']:has-text('All Media')",
            "button:has-text('Add Media')",
            "[role='button']:has-text('Add Media')",
            "button[aria-label*='uploaded media']",
            "button[aria-label*='Uploaded media']",
            "button[aria-label*='All Media']",
            "button[aria-label*='Add Media']",
            "[aria-label*='View uploaded media']",
            "[aria-label*='View images']",
            "[aria-label*='All Media']",
            "[aria-label*='Add Media']",
        ]

        clicked = self._flow_click_first(
            page,
            open_selectors,
            label="open_uploaded_media_gallery",
            force=True,
        )

        if clicked:
            page.wait_for_timeout(2000)

        json_log(
            level="INFO" if clicked else "DEBUG",
            message="Flow uploaded media gallery open attempted",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_open_uploaded_media_gallery",
                "clicked": clicked,
                "summary": self._flow_reference_attach_summary(page),
            },
        )

        return clicked

    def _flow_media_candidate_summary(self, page) -> Dict[str, Any]:
        selectors = [
            "[role='dialog'] img",
            "[role='dialog'] canvas",
            "[role='dialog'] [role='img']",
            "[data-testid*='gallery'] img",
            "[data-testid*='asset'] img",
            "[data-testid*='media'] img",
            "[data-testid*='thumbnail'] img",
            "main img",
            "main canvas",
            "[role='button'] img",
            "button img",
        ]

        details: List[Dict[str, Any]] = []
        for selector in selectors:
            try:
                collection = page.locator(selector)
                count = min(collection.count(), 20)
                visible_count = 0
                large_count = 0
                for idx in range(count):
                    try:
                        item = collection.nth(idx)
                        if not item.is_visible():
                            continue
                        visible_count += 1
                        box = item.bounding_box() or {}
                        width = float(box.get("width", 0) or 0)
                        height = float(box.get("height", 0) or 0)
                        if width >= 48 and height >= 48:
                            large_count += 1
                    except Exception:
                        continue
                if count or visible_count or large_count:
                    details.append(
                        {
                            "selector": selector,
                            "count": count,
                            "visible_count": visible_count,
                            "large_count": large_count,
                        }
                    )
            except Exception:
                continue

        return {
            "url": getattr(page, "url", ""),
            "selectors": details[:20],
        }

    def _flow_click_media_candidate(self, candidate) -> bool:
        try:
            candidate.scroll_into_view_if_needed(timeout=FLOW_UI_CLICK_TIMEOUT_MS)
        except Exception:
            pass

        try:
            candidate.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
            return True
        except Exception:
            pass

        try:
            box = candidate.bounding_box() or {}
            x = float(box.get("x", 0) or 0) + (float(box.get("width", 0) or 0) / 2)
            y = float(box.get("y", 0) or 0) + (float(box.get("height", 0) or 0) / 2)
            candidate.page.mouse.click(x, y)
            return True
        except Exception:
            return False
```

---

## STEP 2 — PATCH_12N2: replace `_flow_select_gallery_assets(...)`

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12N2",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
```

### Replace entire method

From:

```python
    def _flow_select_gallery_assets(self, page, expected_count: int) -> int:
```

Through the line immediately before:

```python
    def _flow_click_attach_selected_to_composer(self, page) -> bool:
```

### Replacement

```python
    def _flow_select_gallery_assets(self, page, expected_count: int) -> int:
        self._flow_open_uploaded_media_gallery(page)

        gallery_selectors = [
            "[role='dialog'] [aria-selected='false']",
            "[role='dialog'] [aria-checked='false']",
            "[role='dialog'] [role='checkbox']",
            "[role='dialog'] [role='option']",
            "[role='dialog'] [role='gridcell']",
            "[role='dialog'] [role='button'] img",
            "[role='dialog'] button img",
            "[role='dialog'] img",
            "[role='dialog'] canvas",
            "[data-testid*='uploaded'] img",
            "[data-testid*='gallery'] img",
            "[data-testid*='asset'] img",
            "[data-testid*='media'] img",
            "[data-testid*='thumbnail'] img",
            "[aria-label*='uploaded'] img",
            "[aria-label*='Uploaded'] img",
            "main [data-testid*='asset'] img",
            "main [data-testid*='media'] img",
            "main [data-testid*='thumbnail'] img",
            "main [role='button'] img",
            "main button img",
        ]

        selected = 0
        attempted = 0
        seen_keys = set()

        for selector in gallery_selectors:
            try:
                collection = page.locator(selector)
                count = min(collection.count(), 40)

                for idx in range(count):
                    if selected >= expected_count:
                        break

                    item = collection.nth(idx)

                    try:
                        if not item.is_visible():
                            continue
                    except Exception:
                        continue

                    try:
                        box = item.bounding_box() or {}
                    except Exception:
                        continue

                    width = float(box.get("width", 0) or 0)
                    height = float(box.get("height", 0) or 0)
                    x = float(box.get("x", 0) or 0)
                    y = float(box.get("y", 0) or 0)

                    if width < 48 or height < 48:
                        continue

                    key = f"{int(x)}:{int(y)}:{int(width)}:{int(height)}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    attempted += 1

                    target = item
                    try:
                        # Prefer clicking a containing card/button when the image itself
                        # is not the selectable element.
                        container = item.locator(
                            "xpath=ancestor-or-self::*[@role='button' or @role='option' or @role='gridcell' or self::button][1]"
                        ).first
                        if container.count() and container.is_visible():
                            target = container
                    except Exception:
                        pass

                    if self._flow_click_media_candidate(target):
                        selected += 1
                        page.wait_for_timeout(700)

                if selected >= expected_count:
                    break

            except Exception:
                continue

        json_log(
            level="INFO" if selected else "WARNING",
            message="Flow gallery asset selection attempted",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_gallery_asset_selection_attempted",
                "expected_count": expected_count,
                "selected_count": selected,
                "attempted_click_count": attempted,
                "candidate_summary": self._flow_media_candidate_summary(page),
            },
        )

        return selected
```

---

## STEP 3 — PATCH_12N3: replace reference finalization order

### Dry-run expectation

```json
{
  "patch_id": "PATCH_12N3",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
```

### Replace entire method

From:

```python
    def _finalize_flow_reference_attachment_to_composer(self, page, source_images: List[str]) -> None:
```

Through the line immediately before:

```python
    def _flow_prompt_surface_summary(self, page) -> Dict[str, Any]:
```

### Replacement

```python
    def _finalize_flow_reference_attachment_to_composer(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        expected_count = len(source_images)

        json_log(
            level="INFO",
            message="Flow reference composer attachment verification started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_reference_composer_attach_verify_start",
                "source_image_count": expected_count,
                "strict": FLOW_REFERENCE_ATTACH_STRICT,
            },
        )

        before_count = self._flow_composer_reference_count(page)

        # Correct Flow order:
        # 1. Open the uploaded-media/gallery surface.
        # 2. Select uploaded image assets.
        # 3. Click the attach/add/use control.
        # 4. Confirm visible composer reference chips/assets.
        opened_gallery = self._flow_open_uploaded_media_gallery(page)
        selected_count = self._flow_select_gallery_assets(page, expected_count)
        clicked_attach = self._flow_click_attach_selected_to_composer(page)

        page.wait_for_timeout(2000)
        self._dismiss_flow_transient_overlays(page)

        attached = self._wait_for_flow_references_in_composer(page, expected_count)
        after_count = self._flow_composer_reference_count(page)

        if attached:
            json_log(
                level="INFO",
                message="Flow reference images attached to composer",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_reference_images_attached_to_composer",
                    "source_image_count": expected_count,
                    "opened_gallery": opened_gallery,
                    "selected_gallery_asset_count": selected_count,
                    "clicked_attach_control": clicked_attach,
                    "before_composer_reference_count": before_count,
                    "after_composer_reference_count": after_count,
                },
            )
            return

        context = {
            "operation": "flow_reference_gallery_attach_failed",
            "source_image_count": expected_count,
            "opened_gallery": opened_gallery,
            "selected_gallery_asset_count": selected_count,
            "clicked_attach_control": clicked_attach,
            "before_composer_reference_count": before_count,
            "after_composer_reference_count": after_count,
            "summary": self._flow_reference_attach_summary(page),
            "media_candidate_summary": self._flow_media_candidate_summary(page),
        }

        if FLOW_REFERENCE_ATTACH_STRICT:
            fail(
                "FLOW_REFERENCE_NOT_ATTACHED_TO_COMPOSER",
                "Flow reference images were uploaded to the gallery but were not confirmed attached to the active composer.",
                field="flow_reference_composer",
                expected="uploaded gallery image selected and attached into prompt composer",
                actual=json.dumps(context, ensure_ascii=False),
                stage="PROCESSING",
            )

        json_log(
            level="WARNING",
            message="Flow reference images uploaded but composer attachment was not confirmed",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context=context,
        )
```

---

# PATCH_12N validation

## STEP 4 — N-Validation 1: compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

---

## STEP 5 — N-Validation 2: static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "def _flow_open_uploaded_media_gallery",
    "def _flow_media_candidate_summary",
    "def _flow_click_media_candidate",
    "Flow uploaded media gallery open attempted",
    "Flow gallery asset selection attempted",
    "candidate_summary",
    "media_candidate_summary",
    "opened_gallery",
    "Correct Flow order:",
]

for marker in required:
    assert marker in text, marker

print("PATCH_12N_FLOW_GALLERY_SELECTION_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12N_FLOW_GALLERY_SELECTION_STATIC_OK
```

---

## STEP 6 — N-Validation 3: no-browser method sanity

```powershell
$env:IMAGE_EXECUTION_BACKEND="flow_browser"

@'
import workflow_orchestrator as w

adapter = w.FlowBrowserImageGenerationAdapter(
    w.BROWSER_CDP_URL,
    w.FLOW_URL,
    w.BROWSER_ACTION_TIMEOUT_MS,
)

required = [
    "_flow_open_uploaded_media_gallery",
    "_flow_media_candidate_summary",
    "_flow_click_media_candidate",
    "_flow_select_gallery_assets",
    "_finalize_flow_reference_attachment_to_composer",
]

for name in required:
    assert hasattr(adapter, name), name

print("PATCH_12N_FLOW_GALLERY_SELECTION_METHODS_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12N_FLOW_GALLERY_SELECTION_METHODS_OK
```

---

# Resume STEP 7 after PATCH_12N
