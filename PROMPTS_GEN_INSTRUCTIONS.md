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

# PATCH_12O — Flow settings + clipboard paste primary path

* Proceed with **PATCH_12O**.
* Scope: replace Flow’s primary reference-attachment path with the confirmed **settings + clipboard paste + Control+Enter** workflow.
* Keep gallery helpers in file as fallback/legacy code, but do **not** call them from the primary Flow execution path.
* Add explicit wait after every pasted image so Flow finishes rendering/uploading the reference before the next action.

Current uploaded `workflow_orchestrator.py` still has the old gallery-selection attachment path and Flow configuration variables already present.  The confirmed working smoke scripts are `flow_clipboard_paste_smoke.py` and `flow_settings_smoke.py`.  

---

## STEP 0 - Cleanup before PATCH_12O

Run only this cleanup:

```powershell
Remove-Item -Recurse -Force .\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\output\flow_inspect -ErrorAction SilentlyContinue
Remove-Item -Force .\output\generated_images\image_12.png -ErrorAction SilentlyContinue
```

Do **not** delete:

```text
output/workflow_state.json
output/image_prompts.json
output/image_content.json
```

---

## STEP 1 — PATCH_12O1: add subprocess import + clipboard timing env vars

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "import_os": text.count("import os"),
    "import_subprocess_existing": text.count("import subprocess"),
    "flow_reference_attach_strict": text.count('FLOW_REFERENCE_ATTACH_STRICT = os.getenv("FLOW_REFERENCE_ATTACH_STRICT", "1") == "1"'),
    "flow_clipboard_wait_existing": text.count("FLOW_CLIPBOARD_PASTE_WAIT_SECONDS"),
}

print(checks)

assert checks["import_os"] == 1
assert checks["import_subprocess_existing"] == 0
assert checks["flow_reference_attach_strict"] == 1
assert checks["flow_clipboard_wait_existing"] == 0
print("PATCH_12O1_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Apply

1. After:

```python
import os
```

Add:

```python
import subprocess
```

2. After:

```python
FLOW_REFERENCE_ATTACH_STRICT = os.getenv("FLOW_REFERENCE_ATTACH_STRICT", "1") == "1"
```

Add:

```python
FLOW_CLIPBOARD_PASTE_WAIT_SECONDS = float(os.getenv("FLOW_CLIPBOARD_PASTE_WAIT_SECONDS", "6"))
FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS = float(os.getenv("FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS", "3"))
FLOW_REFERENCE_ATTACH_METHOD = os.getenv("FLOW_REFERENCE_ATTACH_METHOD", "clipboard").lower()
```

---

## STEP 2 — PATCH_12O2: add Flow settings + clipboard helper methods

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "anchor": text.count("    def _flow_visible_media_count(self, page, *, scope_label: str = \"page\") -> int:"),
    "existing_clipboard_helper": text.count("def _copy_image_to_windows_clipboard"),
    "existing_settings_helper": text.count("def _configure_flow_generation_settings"),
    "existing_paste_helper": text.count("def _paste_flow_reference_images_into_composer"),
}

print(checks)

assert checks["anchor"] == 1
assert checks["existing_clipboard_helper"] == 0
assert checks["existing_settings_helper"] == 0
assert checks["existing_paste_helper"] == 0
print("PATCH_12O2_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Insert immediately before

```python
    def _flow_visible_media_count(self, page, *, scope_label: str = "page") -> int:
```

### Add

```python
    def _flow_norm(self, text_value: str) -> str:
        return re.sub(r"\s+", " ", (text_value or "").strip())

    def _copy_image_to_windows_clipboard(self, image_path: str) -> None:
        path = str(Path(image_path).resolve())

        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Path = @'
{path}
'@

$img = [System.Drawing.Image]::FromFile($Path)
$bmp = New-Object System.Drawing.Bitmap $img
$img.Dispose()

[System.Windows.Forms.Clipboard]::SetImage($bmp)
Start-Sleep -Milliseconds 300
"""

        subprocess.run(
            [
                "powershell.exe",
                "-STA",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps_script,
            ],
            check=True,
            timeout=max(30, int(self.action_timeout_ms / 1000)),
        )

    def _open_flow_composer_settings_pill(self, page) -> None:
        selectors = [
            "button:has-text('Nano Banana')",
            "[role='button']:has-text('Nano Banana')",
            "button:has-text('Imagen')",
            "[role='button']:has-text('Imagen')",
            "button:has-text('1x')",
            "[role='button']:has-text('1x')",
        ]

        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() and locator.is_visible() and locator.is_enabled():
                    locator.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    page.wait_for_timeout(1000)
                    json_log(
                        level="INFO",
                        message="Flow composer settings menu opened",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "flow_composer_settings_menu_opened",
                            "selector": selector,
                        },
                    )
                    return
            except Exception:
                continue

        fail(
            "FLOW_SETTINGS_MENU_NOT_FOUND",
            "Could not find Flow composer model/settings pill.",
            field="flow_composer_settings",
            expected="composer pill containing Nano Banana, Imagen, or 1x",
            actual=f"url={getattr(page, 'url', '')}",
            stage="PROCESSING",
        )

    def _flow_open_menu(self, page):
        menu = page.locator(
            "[data-radix-menu-content][data-state='open'], [role='menu'][data-state='open']"
        ).last

        if not menu.count() or not menu.is_visible():
            fail(
                "FLOW_SETTINGS_MENU_NOT_OPEN",
                "Flow composer settings menu was not open after clicking the composer model/settings pill.",
                field="flow_settings_menu",
                expected="open Radix menu from composer model/settings pill",
                actual=f"url={getattr(page, 'url', '')}",
                stage="PROCESSING",
            )

        return menu

    def _flow_click_menu_button_containing(self, page, wanted: str, label: str) -> bool:
        menu = self._flow_open_menu(page)
        buttons = menu.locator("button, [role='tab'], [role='button'], [role='menuitem'], [role='option']")
        wanted_l = wanted.lower()

        for idx in range(min(buttons.count(), 80)):
            try:
                button = buttons.nth(idx)
                if not button.is_visible() or not button.is_enabled():
                    continue

                text = self._flow_norm(button.inner_text(timeout=500))
                if wanted_l not in text.lower():
                    continue

                button.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                page.wait_for_timeout(700)

                json_log(
                    level="INFO",
                    message="Flow settings option clicked",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "flow_settings_option_clicked",
                        "label": label,
                        "wanted": wanted,
                        "actual_text": text,
                    },
                )
                return True
            except Exception:
                continue

        return False

    def _select_flow_image_mode(self, page) -> bool:
        return self._flow_click_menu_button_containing(page, "Image", "image_mode")

    def _select_flow_aspect_ratio(self, page) -> bool:
        return self._flow_click_menu_button_containing(page, FLOW_ASPECT_RATIO, "aspect_ratio")

    def _select_flow_output_count(self, page) -> bool:
        count = str(FLOW_OUTPUT_COUNT).strip()
        label = "1x" if count == "1" else f"x{count}"
        return self._flow_click_menu_button_containing(page, label, "output_count")

    def _select_flow_model(self, page) -> bool:
        menu = self._flow_open_menu(page)

        buttons = menu.locator("button, [role='button']")
        model_button = None

        for idx in range(min(buttons.count(), 80)):
            try:
                button = buttons.nth(idx)
                if not button.is_visible() or not button.is_enabled():
                    continue

                text = self._flow_norm(button.inner_text(timeout=500))
                if "Nano Banana" in text or "Imagen" in text:
                    model_button = button

                    if FLOW_IMAGE_MODEL.lower() in text.lower():
                        json_log(
                            level="INFO",
                            message="Flow model selected",
                            stage="PROCESSING",
                            status="COMPLETED",
                            context={
                                "operation": "flow_model_already_selected",
                                "target_model": FLOW_IMAGE_MODEL,
                                "actual_text": text,
                            },
                        )
                        return True

                    button.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    page.wait_for_timeout(1000)
                    break
            except Exception:
                continue

        if model_button is None:
            return False

        selectors = [
            f"text={FLOW_IMAGE_MODEL}",
            f"button:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='menuitem']:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='option']:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='button']:has-text('{FLOW_IMAGE_MODEL}')",
        ]

        for selector in selectors:
            try:
                option = page.locator(selector).last
                if option.count() and option.is_visible():
                    option.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    page.wait_for_timeout(800)

                    json_log(
                        level="INFO",
                        message="Flow model selected",
                        stage="PROCESSING",
                        status="COMPLETED",
                        context={
                            "operation": "flow_model_selected",
                            "target_model": FLOW_IMAGE_MODEL,
                            "selector": selector,
                        },
                    )
                    return True
            except Exception:
                continue

        return False

    def _configure_flow_generation_settings(self, page) -> None:
        json_log(
            level="INFO",
            message="Flow generation settings selection started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_generation_settings_selection_start",
                "target_model": FLOW_IMAGE_MODEL,
                "aspect_ratio": FLOW_ASPECT_RATIO,
                "output_count": FLOW_OUTPUT_COUNT,
            },
        )

        self._open_flow_composer_settings_pill(page)

        image_ok = self._select_flow_image_mode(page)
        aspect_ok = self._select_flow_aspect_ratio(page)
        output_ok = self._select_flow_output_count(page)
        model_ok = self._select_flow_model(page)

        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass

        if FLOW_MODEL_STRICT and not model_ok:
            fail(
                "FLOW_MODEL_NOT_AVAILABLE",
                "Required Flow image model is not visible or selectable in the Flow composer settings menu.",
                field="FLOW_IMAGE_MODEL",
                expected=f"{FLOW_IMAGE_MODEL} selected from Flow composer settings menu",
                actual=json.dumps(
                    {
                        "image_ok": image_ok,
                        "aspect_ok": aspect_ok,
                        "output_ok": output_ok,
                        "model_ok": model_ok,
                        "url": getattr(page, "url", ""),
                    },
                    ensure_ascii=False,
                ),
                stage="PROCESSING",
            )

        if not image_ok or not aspect_ok or not output_ok:
            fail(
                "FLOW_SETTINGS_NOT_CONFIGURED",
                "Flow image mode, aspect ratio, or output count could not be selected.",
                field="flow_generation_settings",
                expected="Image mode, requested aspect ratio, and requested output count selected",
                actual=json.dumps(
                    {
                        "image_ok": image_ok,
                        "aspect_ok": aspect_ok,
                        "output_ok": output_ok,
                        "model_ok": model_ok,
                        "target_model": FLOW_IMAGE_MODEL,
                        "aspect_ratio": FLOW_ASPECT_RATIO,
                        "output_count": FLOW_OUTPUT_COUNT,
                    },
                    ensure_ascii=False,
                ),
                stage="PROCESSING",
            )

        json_log(
            level="INFO",
            message="Flow generation settings selected",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_generation_settings_selected",
                "image_ok": image_ok,
                "aspect_ok": aspect_ok,
                "output_ok": output_ok,
                "model_ok": model_ok,
                "target_model": FLOW_IMAGE_MODEL,
                "aspect_ratio": FLOW_ASPECT_RATIO,
                "output_count": FLOW_OUTPUT_COUNT,
            },
        )

    def _paste_flow_reference_images_into_composer(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        prompt_box = self._find_flow_prompt_box(page)

        json_log(
            level="INFO",
            message="Flow reference image clipboard paste started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_reference_clipboard_paste_start",
                "source_image_count": len(source_images),
                "paste_wait_seconds": FLOW_CLIPBOARD_PASTE_WAIT_SECONDS,
                "final_settle_seconds": FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS,
            },
        )

        for idx, image_path in enumerate(source_images, start=1):
            before_count = self._flow_composer_reference_count(page)

            self._copy_image_to_windows_clipboard(image_path)

            try:
                prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
            except Exception:
                prompt_box = self._find_flow_prompt_box(page)
                prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)

            page.keyboard.press("Control+V")

            # Required: let Flow finish rendering/uploading this pasted image before the next action.
            page.wait_for_timeout(int(FLOW_CLIPBOARD_PASTE_WAIT_SECONDS * 1000))

            after_count = self._flow_composer_reference_count(page)

            json_log(
                level="INFO",
                message="Flow reference image pasted into composer",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_reference_image_pasted_into_composer",
                    "image_index": idx,
                    "source_image_count": len(source_images),
                    "image_path": image_path,
                    "before_composer_reference_count": before_count,
                    "after_composer_reference_count": after_count,
                    "paste_wait_seconds": FLOW_CLIPBOARD_PASTE_WAIT_SECONDS,
                },
            )

        page.wait_for_timeout(int(FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS * 1000))

        json_log(
            level="INFO",
            message="Flow reference images pasted into composer",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_reference_images_pasted_into_composer",
                "source_image_count": len(source_images),
                "composer_reference_count": self._flow_composer_reference_count(page),
                "attach_method": "clipboard",
            },
        )
```

---

## STEP 3 — PATCH_12O3: replace `_attach_reference_images(...)`

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "method": text.count("    def _attach_reference_images(self, page, source_images: List[str]) -> None:"),
    "old_upload_marker": text.count("Flow reference images uploaded"),
    "old_finalize_call": text.count("self._finalize_flow_reference_attachment_to_composer(page, source_images)"),
}

print(checks)

assert checks["method"] == 1
assert checks["old_upload_marker"] >= 1
assert checks["old_finalize_call"] == 1
print("PATCH_12O3_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Replace entire method

From:

```python
    def _attach_reference_images(self, page, source_images: List[str]) -> None:
```

Through the line immediately before:

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
```

### Replacement

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
                "attach_method": FLOW_REFERENCE_ATTACH_METHOD,
            },
        )

        if FLOW_REFERENCE_ATTACH_METHOD != "clipboard":
            fail(
                "FLOW_REFERENCE_ATTACH_METHOD_UNSUPPORTED",
                "Only the confirmed clipboard Flow reference attachment method is enabled for PATCH_12O.",
                field="FLOW_REFERENCE_ATTACH_METHOD",
                expected="clipboard",
                actual=FLOW_REFERENCE_ATTACH_METHOD,
                stage="PROCESSING",
            )

        try:
            self._paste_flow_reference_images_into_composer(page, source_images)
        except SystemExit:
            raise
        except Exception as exc:
            fail(
                "FLOW_REFERENCE_CLIPBOARD_PASTE_FAILED",
                "Failed to paste Flow reference images into the composer via Windows clipboard.",
                field="generation_context.source_images",
                expected="each source image copied to clipboard and pasted into Flow composer with upload wait",
                actual=str(exc)[:1000],
                stage="PROCESSING",
            )
```

---

## STEP 4 — PATCH_12O4: replace `_submit_flow_prompt(...)`

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "method": text.count("    def _submit_flow_prompt(self, page, prompt: str) -> None:"),
    "old_generate_click": text.count("clicked_generate = self._flow_click_first(page, generate_selectors, label=\"flow_generate_button\", force=True)"),
    "old_model_selection_started": text.count("Flow model selection started"),
}

print(checks)

assert checks["method"] == 1
assert checks["old_generate_click"] == 1
assert checks["old_model_selection_started"] >= 1
print("PATCH_12O4_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Replace entire method

From:

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
```

Through the line immediately before:

```python
    def _capture_flow_generated_image_base64(self, page) -> str:
```

### Replacement

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
        prompt_box = self._find_flow_prompt_box(page)
        self._fill_flow_prompt_box(page, prompt_box, prompt)

        json_log(
            level="INFO",
            message="Flow image prompt submit command started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_prompt_submit_control_enter_start",
                "prompt_chars": len(prompt or ""),
                "target_model": FLOW_IMAGE_MODEL,
            },
        )

        try:
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
        except Exception:
            prompt_box = self._find_flow_prompt_box(page)
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)

        # Confirmed smoke-test behavior: submit once with Control+Enter only.
        # Do not scan/click Create, because Flow may expose a nearby Add Media/+ Create control.
        page.keyboard.press("Control+Enter")

        json_log(
            level="INFO",
            message="Flow image prompt submitted",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_prompt_submitted_keyboard_only",
                "prompt_chars": len(prompt or ""),
                "target_model": FLOW_IMAGE_MODEL,
                "submit_method": "Control+Enter",
            },
        )

        if self._wait_for_flow_submit_confirmation(page):
            return

        json_log(
            level="WARNING",
            message="Flow prompt submission confirmation was not observed before capture wait",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_prompt_submit_confirmation_not_observed_continue_to_capture",
                "prompt_chars": len(prompt or ""),
                "target_model": FLOW_IMAGE_MODEL,
            },
        )
```

---

## STEP 5 — PATCH_12O5: replace Flow `execute_image(...)` ordering

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

old = """        source_images, _missing_images = self._extract_reference_images(generation_context)
        page = self._page()
        self._attach_reference_images(page, source_images)
        self._submit_flow_prompt(page, prompt)
        image_base64 = self._capture_flow_generated_image_base64(page)
"""

print({"old_execute_sequence_count": text.count(old), "configure_existing": text.count("self._configure_flow_generation_settings(page)")})

assert text.count(old) == 1
assert text.count("self._configure_flow_generation_settings(page)") == 0
print("PATCH_12O5_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Replace this sequence inside Flow `execute_image(...)`

```python
        source_images, _missing_images = self._extract_reference_images(generation_context)
        page = self._page()
        self._attach_reference_images(page, source_images)
        self._submit_flow_prompt(page, prompt)
        image_base64 = self._capture_flow_generated_image_base64(page)
```

### With

```python
        source_images, _missing_images = self._extract_reference_images(generation_context)
        page = self._page()

        self._configure_flow_generation_settings(page)
        self._attach_reference_images(page, source_images)
        self._submit_flow_prompt(page, prompt)

        image_base64 = self._capture_flow_generated_image_base64(page)
```

---

# PATCH_12O validation

## STEP 6 — O-Validation 1: compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

---

## STEP 7 — O-Validation 2: static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "import subprocess",
    "FLOW_CLIPBOARD_PASTE_WAIT_SECONDS",
    "FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS",
    "FLOW_REFERENCE_ATTACH_METHOD",
    "def _copy_image_to_windows_clipboard",
    "def _open_flow_composer_settings_pill",
    "def _configure_flow_generation_settings",
    "def _paste_flow_reference_images_into_composer",
    "Flow generation settings selected",
    "Flow reference image pasted into composer",
    "Flow reference images pasted into composer",
    "flow_prompt_submitted_keyboard_only",
    "self._configure_flow_generation_settings(page)",
]

for marker in required:
    assert marker in text, marker

for forbidden in [
    "self._finalize_flow_reference_attachment_to_composer(page, source_images)",
    "clicked_generate = self._flow_click_first(page, generate_selectors, label=\"flow_generate_button\", force=True)",
]:
    assert forbidden not in text, forbidden

print("PATCH_12O_FLOW_CLIPBOARD_SETTINGS_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12O_FLOW_CLIPBOARD_SETTINGS_STATIC_OK
```

---

## STEP 8 — O-Validation 3: method sanity

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
    "_copy_image_to_windows_clipboard",
    "_open_flow_composer_settings_pill",
    "_configure_flow_generation_settings",
    "_paste_flow_reference_images_into_composer",
    "_attach_reference_images",
    "_submit_flow_prompt",
]

for name in required:
    assert hasattr(adapter, name), name

assert w.FLOW_REFERENCE_ATTACH_METHOD == "clipboard"
assert w.FLOW_CLIPBOARD_PASTE_WAIT_SECONDS >= 6

print("PATCH_12O_FLOW_CLIPBOARD_SETTINGS_METHODS_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12O_FLOW_CLIPBOARD_SETTINGS_METHODS_OK
```

---

# Resume STEP 7 after PATCH_12O

# PATCH_12P = submit-button correction + no-click capture correction

Reason: the working smoke script submits by locating/clicking the real composer submit button near the prompt box, while the current orchestrator still submits with `Control+Enter` only. The current Flow capture logic also still contains `expect_download` + button click behavior, which can cause the unwanted image/download interaction.   The working submit pattern is in `click_submit_arrow(page)`. 

---

# STEP 0 - Cleanup before PATCH_12P

```powershell
Remove-Item -Recurse -Force .\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Force .\output\generated_images\image_12.png -ErrorAction SilentlyContinue
```

Do **not** delete:

```text
output/workflow_state.json
output/image_prompts.json
output/image_content.json
```

---

# STEP 1 - PATCH_12P1: add composer-scoped submit helper

## Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "anchor": text.count("    def _submit_flow_prompt(self, page, prompt: str) -> None:"),
    "existing_helper": text.count("def _click_flow_submit_arrow"),
    "keyboard_only_marker": text.count("flow_prompt_submitted_keyboard_only"),
}

print(checks)

assert checks["anchor"] == 1
assert checks["existing_helper"] == 0
assert checks["keyboard_only_marker"] == 1
print("PATCH_12P1_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

## Insert immediately before

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
```

## Add

```python
    def _click_flow_submit_arrow(self, page, prompt_box) -> None:
        rect = prompt_box.bounding_box() or {}

        if not rect:
            fail(
                "FLOW_SUBMIT_PROMPT_BOX_RECT_MISSING",
                "Could not resolve Flow prompt box geometry before submit.",
                field="flow_prompt_box",
                expected="prompt box bounding rectangle available",
                actual=f"url={getattr(page, 'url', '')}",
                stage="PROCESSING",
            )

        json_log(
            level="INFO",
            message="Flow submit button search started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_submit_button_search_start",
                "prompt_box_rect": {
                    "x": rect.get("x"),
                    "y": rect.get("y"),
                    "width": rect.get("width"),
                    "height": rect.get("height"),
                },
            },
        )

        buttons = page.locator("button, [role='button']")

        for idx in range(min(buttons.count(), 140)):
            try:
                button = buttons.nth(idx)
                if not button.is_visible() or not button.is_enabled():
                    continue

                text = (button.inner_text(timeout=500) or "").strip()
                aria = button.get_attribute("aria-label") or ""
                label = f"{text} {aria}".strip()
                normalized = label.lower()

                if any(
                    bad in normalized
                    for bad in [
                        "add",
                        "add_2",
                        "media",
                        "upload",
                        "attach",
                        "agent",
                        "nano banana",
                        "imagen",
                        "settings",
                        "more",
                        "download",
                    ]
                ):
                    continue

                if not any(
                    good in normalized
                    for good in [
                        "submit",
                        "send",
                        "generate",
                        "create",
                        "arrow_forward",
                    ]
                ):
                    continue

                box = button.bounding_box() or {}
                if not box:
                    continue

                cx = box["x"] + box["width"] / 2
                cy = box["y"] + box["height"] / 2

                near_composer = (
                    rect["x"] - 80 <= cx <= rect["x"] + rect["width"] + 180
                    and rect["y"] - 120 <= cy <= rect["y"] + rect["height"] + 160
                )

                if not near_composer:
                    continue

                json_log(
                    level="INFO",
                    message="Flow submit button clicked",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_submit_button_clicked",
                        "button_label": label,
                        "button_index": idx,
                    },
                )

                button.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                page.wait_for_timeout(3000)
                return

            except Exception:
                continue

        x = rect["x"] + rect["width"] + 36
        y = rect["y"] + rect["height"] / 2

        json_log(
            level="WARNING",
            message="Flow submit button selector not found; using composer arrow coordinate fallback",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_submit_coordinate_fallback_clicked",
                "x": x,
                "y": y,
            },
        )

        page.mouse.click(x, y)
        page.wait_for_timeout(3000)
```

---

# STEP 2 - PATCH_12P2: replace `_submit_flow_prompt(...)`

## Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "method": text.count("    def _submit_flow_prompt(self, page, prompt: str) -> None:"),
    "old_keyboard_marker": text.count("flow_prompt_submitted_keyboard_only"),
    "old_control_enter_comment": text.count("Confirmed smoke-test behavior: submit once with Control+Enter only."),
    "new_helper_call": text.count("self._click_flow_submit_arrow(page, prompt_box)"),
}

print(checks)

assert checks["method"] == 1
assert checks["old_keyboard_marker"] == 1
assert checks["old_control_enter_comment"] == 1
assert checks["new_helper_call"] == 0
print("PATCH_12P2_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

## Replace entire method

From:

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
```

Through the line immediately before:

```python
    def _capture_flow_generated_image_base64(self, page) -> str:
```

## Replacement

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
        prompt_box = self._find_flow_prompt_box(page)
        self._fill_flow_prompt_box(page, prompt_box, prompt)

        json_log(
            level="INFO",
            message="Flow image prompt submit command started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_prompt_submit_click_button_start",
                "prompt_chars": len(prompt or ""),
                "target_model": FLOW_IMAGE_MODEL,
            },
        )

        try:
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
        except Exception:
            prompt_box = self._find_flow_prompt_box(page)
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)

        self._click_flow_submit_arrow(page, prompt_box)

        json_log(
            level="INFO",
            message="Flow image prompt submitted",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_prompt_submitted_click_button",
                "prompt_chars": len(prompt or ""),
                "target_model": FLOW_IMAGE_MODEL,
                "submit_method": "composer_scoped_submit_button",
            },
        )

        if self._wait_for_flow_submit_confirmation(page):
            return

        json_log(
            level="WARNING",
            message="Flow prompt submission confirmation was not observed before capture wait",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_prompt_submit_confirmation_not_observed_continue_to_capture",
                "prompt_chars": len(prompt or ""),
                "target_model": FLOW_IMAGE_MODEL,
            },
        )
```

---

# STEP 3 - PATCH_12P3: disable download-click capture path

## Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "download_selectors": text.count("download_selectors = ["),
    "expect_download": text.count("with page.expect_download(timeout=3000) as download_info:"),
    "captured_download_marker": text.count("flow_generated_image_captured_download"),
    "capture_method": text.count("    def _capture_flow_generated_image_base64(self, page) -> str:"),
}

print(checks)

assert checks["capture_method"] == 1
assert checks["download_selectors"] == 1
assert checks["expect_download"] == 1
assert checks["captured_download_marker"] == 1
print("PATCH_12P3_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

## Remove this block inside `_capture_flow_generated_image_base64(...)`

Remove from:

```python
        download_selectors = [
            "button[aria-label*='Download']",
            "button[aria-label*='download']",
            "[role='button'][aria-label*='Download']",
            "[role='button'][aria-label*='download']",
            "button:has-text('Download')",
            "[data-testid*='download']",
        ]
```

Through the end of this loop inside `while time.time() < deadline:`:

```python
            for selector in download_selectors:
                try:
                    button = page.locator(selector).last
                    if not button.count() or not button.is_visible() or not button.is_enabled():
                        continue
                    with page.expect_download(timeout=3000) as download_info:
                        button.click(timeout=self.action_timeout_ms)
                    download = download_info.value
                    download_path = download.path()
                    if download_path:
                        image_base64 = base64.b64encode(Path(download_path).read_bytes()).decode("ascii")
                        json_log(
                            level="INFO",
                            message="Flow generated image captured from download",
                            stage="PROCESSING",
                            status="COMPLETED",
                            context={
                                "operation": "flow_generated_image_captured_download",
                                "image_base64_chars": len(image_base64),
                            },
                        )
                        return image_base64
                except Exception as exc:
                    last_error = str(exc)[:500]
```

## Insert after `last_error = ""`

```python
        json_log(
            level="INFO",
            message="Flow download-click capture disabled",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_download_click_capture_disabled",
                "reason": "avoid clicking uploaded reference images or opening image/download surfaces before generated output is detected",
            },
        )
```

Result: capture may still read/screenshot generated image candidates, but it must **not click any image/download button**.

---

# STEP 4 - P-Validation 1: compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

---

# STEP 5 - P-Validation 2: static marker check

```powershell
@'
from pathlib import Path
import re

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "def _click_flow_submit_arrow",
    "flow_submit_button_search_start",
    "flow_submit_button_clicked",
    "flow_submit_coordinate_fallback_clicked",
    "flow_prompt_submit_click_button_start",
    "flow_prompt_submitted_click_button",
    "flow_download_click_capture_disabled",
]

for marker in required:
    assert marker in text, marker

for forbidden in [
    "flow_prompt_submitted_keyboard_only",
    "Confirmed smoke-test behavior: submit once with Control+Enter only.",
    "with page.expect_download(timeout=3000) as download_info:",
    "flow_generated_image_captured_download",
    "download_selectors = [",
]:
    assert forbidden not in text, forbidden

method = re.search(
    r"    def _submit_flow_prompt\(self, page, prompt: str\) -> None:\n(?P<body>.*?)\n    def _capture_flow_generated_image_base64",
    text,
    re.S,
)
assert method, "submit method not found"

submit_body = method.group("body")
assert "self._click_flow_submit_arrow(page, prompt_box)" in submit_body
assert "page.keyboard.press(\"Control+Enter\")" not in submit_body

capture = re.search(
    r"    def _capture_flow_generated_image_base64\(self, page\) -> str:\n(?P<body>.*?)\n    def execute_image",
    text,
    re.S,
)
assert capture, "capture method not found"

capture_body = capture.group("body")
assert "expect_download" not in capture_body
assert ".click(timeout=self.action_timeout_ms)" not in capture_body

print("PATCH_12P_SUBMIT_CAPTURE_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12P_SUBMIT_CAPTURE_STATIC_OK
```

---

# STEP 6 - P-Validation 3: method sanity

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
    "_click_flow_submit_arrow",
    "_submit_flow_prompt",
    "_capture_flow_generated_image_base64",
    "_paste_flow_reference_images_into_composer",
    "_configure_flow_generation_settings",
]

for name in required:
    assert hasattr(adapter, name), name

assert w.FLOW_REFERENCE_ATTACH_METHOD == "clipboard"
assert w.FLOW_CLIPBOARD_PASTE_WAIT_SECONDS >= 6

print("PATCH_12P_SUBMIT_CAPTURE_METHODS_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12P_SUBMIT_CAPTURE_METHODS_OK
```

---

# Resume STEP 7 after PATCH_12O


# PATCH_12Q — submit-only no-activation repair + live Flow INFO tracing

## STEP 0 - Cleanup before PATCH_12Q

```powershell
Remove-Item -Recurse -Force .\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Force .\output\generated_images\image_12.png -ErrorAction SilentlyContinue
```

Do not delete state JSON files.

---

## STEP 1 - PATCH_12Q1: add submit-safe composer finder + user INFO trace

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "click_helper_anchor": text.count("    def _click_flow_submit_arrow(self, page, prompt_box) -> None:"),
    "existing_user_info": text.count("def _flow_user_info"),
    "existing_submit_finder": text.count("def _find_flow_prompt_box_for_submit"),
}

print(checks)

assert checks["click_helper_anchor"] == 1
assert checks["existing_user_info"] == 0
assert checks["existing_submit_finder"] == 0
print("PATCH_12Q1_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Insert immediately before

```python
    def _click_flow_submit_arrow(self, page, prompt_box) -> None:
```

### Add

```python
    def _flow_user_info(self, message: str, **context: Any) -> None:
        try:
            details = ""
            if context:
                details = " | " + json.dumps(context, ensure_ascii=False, default=str)
            print(f"Flow: {message}{details}", flush=True)
        except Exception:
            pass

        try:
            json_log(
                level="INFO",
                message=f"Flow: {message}",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_user_tracking_info",
                    "tracking_message": message,
                    **context,
                },
            )
        except Exception:
            pass

    def _find_flow_prompt_box_for_submit(self, page):
        selectors = [
            "textarea",
            "[contenteditable='true']",
            "div[role='textbox']",
            "[role='textbox']",
        ]

        viewport = page.viewport_size or {}
        viewport_height = float(viewport.get("height") or 0)

        self._flow_user_info("Looking for composer before submit", url=getattr(page, "url", ""))

        for selector in selectors:
            try:
                collection = page.locator(selector)
                for idx in range(min(collection.count(), 20)):
                    candidate = collection.nth(idx)

                    if not candidate.is_visible():
                        continue

                    box = candidate.bounding_box() or {}
                    width = float(box.get("width", 0) or 0)
                    height = float(box.get("height", 0) or 0)
                    y = float(box.get("y", 0) or 0)

                    if width < 120 or height < 20:
                        continue

                    # Flow composer is the lower composer surface.
                    # Reject gallery/full-view text surfaces that can appear after image clicks.
                    if viewport_height and y < viewport_height * 0.35:
                        self._flow_user_info(
                            "Skipped non-composer textbox candidate",
                            selector=selector,
                            index=idx,
                            rect=box,
                            viewport_height=viewport_height,
                        )
                        continue

                    self._flow_user_info(
                        "Composer found",
                        selector=selector,
                        index=idx,
                        rect=box,
                    )
                    return candidate

            except Exception as exc:
                self._flow_user_info(
                    "Composer selector skipped",
                    selector=selector,
                    error=str(exc)[:200],
                )

        fail(
            "FLOW_SUBMIT_COMPOSER_NOT_FOUND",
            "Could not find the visible lower Flow composer before submit without activating gallery/image UI.",
            field="flow_submit_composer",
            expected="visible composer textbox near lower Flow composer area",
            actual=json.dumps(
                {
                    "url": getattr(page, "url", ""),
                    "summary": self._flow_prompt_surface_summary(page),
                },
                ensure_ascii=False,
            ),
            stage="PROCESSING",
        )
```

---

## STEP 2 - PATCH_12Q2: replace submit click helper

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "old_signature": text.count("    def _click_flow_submit_arrow(self, page, prompt_box) -> None:"),
    "old_rect_fail": text.count("FLOW_SUBMIT_PROMPT_BOX_RECT_MISSING"),
    "old_coord_fallback": text.count("flow_submit_coordinate_fallback_clicked"),
    "new_signature": text.count("    def _click_flow_submit_arrow(self, page) -> None:"),
}

print(checks)

assert checks["old_signature"] == 1
assert checks["old_rect_fail"] == 1
assert checks["old_coord_fallback"] == 1
assert checks["new_signature"] == 0
print("PATCH_12Q2_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Replace entire method

From:

```python
    def _click_flow_submit_arrow(self, page, prompt_box) -> None:
```

through the line immediately before:

```python
    def _submit_flow_prompt(self, page, prompt: str) -> None:
```

### Replacement

```python
    def _click_flow_submit_arrow(self, page) -> None:
        prompt_box = self._find_flow_prompt_box_for_submit(page)
        rect = prompt_box.bounding_box() or {}

        if not rect:
            fail(
                "FLOW_SUBMIT_PROMPT_BOX_RECT_MISSING",
                "Could not resolve Flow submit composer geometry before submit.",
                field="flow_prompt_box",
                expected="visible lower Flow composer bounding rectangle",
                actual=json.dumps(
                    {
                        "url": getattr(page, "url", ""),
                        "summary": self._flow_prompt_surface_summary(page),
                    },
                    ensure_ascii=False,
                ),
                stage="PROCESSING",
            )

        self._flow_user_info("Click submit button", prompt_box_rect=rect)

        buttons = page.locator("button, [role='button']")
        button_count = min(buttons.count(), 140)

        self._flow_user_info("Scanning visible buttons near composer", button_count=button_count)

        for idx in range(button_count):
            try:
                button = buttons.nth(idx)
                if not button.is_visible() or not button.is_enabled():
                    continue

                text = (button.inner_text(timeout=500) or "").strip()
                aria = button.get_attribute("aria-label") or ""
                label = f"{text} {aria}".strip()
                normalized = label.lower()

                if any(
                    bad in normalized
                    for bad in [
                        "add",
                        "add_2",
                        "media",
                        "upload",
                        "attach",
                        "agent",
                        "nano banana",
                        "imagen",
                        "settings",
                        "more",
                        "download",
                        "gallery",
                    ]
                ):
                    continue

                if not any(
                    good in normalized
                    for good in [
                        "submit",
                        "send",
                        "generate",
                        "create",
                        "arrow_forward",
                    ]
                ):
                    continue

                box = button.bounding_box() or {}
                if not box:
                    continue

                cx = box["x"] + box["width"] / 2
                cy = box["y"] + box["height"] / 2

                near_composer = (
                    rect["x"] - 80 <= cx <= rect["x"] + rect["width"] + 180
                    and rect["y"] - 120 <= cy <= rect["y"] + rect["height"] + 160
                )

                self._flow_user_info(
                    "Submit candidate inspected",
                    button_index=idx,
                    label=label,
                    rect=box,
                    near_composer=near_composer,
                )

                if not near_composer:
                    continue

                self._flow_user_info("Click submit", button_index=idx, label=label)

                button.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                page.wait_for_timeout(3000)

                self._flow_user_info("Submitted")
                return

            except Exception as exc:
                self._flow_user_info(
                    "Submit candidate skipped",
                    button_index=idx,
                    error=str(exc)[:200],
                )

        # Coordinate fallback is allowed only after a verified composer rectangle exists.
        x = rect["x"] + rect["width"] + 36
        y = rect["y"] + rect["height"] / 2

        self._flow_user_info(
            "Submit selector not found; clicking right-side composer arrow fallback",
            x=x,
            y=y,
        )

        page.mouse.click(x, y)
        page.wait_for_timeout(3000)
        self._flow_user_info("Submitted by coordinate fallback")
```

---

## STEP 3 - PATCH_12Q3: replace submit method to avoid prompt-surface activation

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "method": text.count("    def _submit_flow_prompt(self, page, prompt: str) -> None:"),
    "old_find_call": text.count("prompt_box = self._find_flow_prompt_box(page)"),
    "old_helper_call": text.count("self._click_flow_submit_arrow(page, prompt_box)"),
    "new_safe_find_call": text.count("prompt_box = self._find_flow_prompt_box_for_submit(page)"),
    "new_helper_call": text.count("self._click_flow_submit_arrow(page)"),
}

print(checks)

assert checks["method"] == 1
assert checks["old_find_call"] >= 1
assert checks["old_helper_call"] == 1
print("PATCH_12Q3_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Replace only inside `_submit_flow_prompt(...)`

Replace:

```python
        prompt_box = self._find_flow_prompt_box(page)
```

with:

```python
        prompt_box = self._find_flow_prompt_box_for_submit(page)
```

Replace this whole block:

```python
        try:
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
        except Exception:
            prompt_box = self._find_flow_prompt_box(page)
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)

        self._click_flow_submit_arrow(page, prompt_box)
```

with:

```python
        self._flow_user_info("Prompt filled; preparing submit click")
        self._click_flow_submit_arrow(page)
```

---

## STEP 4 - Q-Validation 1: compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

---

## STEP 5 - Q-Validation 2: static marker check

```powershell
@'
from pathlib import Path
import re

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "def _flow_user_info",
    "def _find_flow_prompt_box_for_submit",
    "Flow: ",
    "Looking for composer before submit",
    "Composer found",
    "Click submit button",
    "Scanning visible buttons near composer",
    "Submit candidate inspected",
    "Prompt filled; preparing submit click",
    "self._click_flow_submit_arrow(page)",
]

for marker in required:
    assert marker in text, marker

submit = re.search(
    r"    def _submit_flow_prompt\(self, page, prompt: str\) -> None:\n(?P<body>.*?)\n    def _capture_flow_generated_image_base64",
    text,
    re.S,
)
assert submit, "submit method missing"

body = submit.group("body")
assert "self._find_flow_prompt_box_for_submit(page)" in body
assert "self._find_flow_prompt_box(page)" not in body
assert "self._click_flow_submit_arrow(page, prompt_box)" not in body

print("PATCH_12Q_SUBMIT_NO_ACTIVATION_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12Q_SUBMIT_NO_ACTIVATION_STATIC_OK
```

---

## STEP 6 - Q-Validation 3: method sanity

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
    "_flow_user_info",
    "_find_flow_prompt_box_for_submit",
    "_click_flow_submit_arrow",
    "_submit_flow_prompt",
]

for name in required:
    assert hasattr(adapter, name), name

print("PATCH_12Q_SUBMIT_NO_ACTIVATION_METHODS_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12Q_SUBMIT_NO_ACTIVATION_METHODS_OK
```

---

# Resume STEP 7 after PATCH_12Q

# PATCH_12R — enforce pasted-reference readiness before submit + recover from Flow page closure during capture

## STEP 0 - Cleanup before PATCH_12R

```powershell
Remove-Item -Recurse -Force .\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Force .\output\generated_images\image_12.png -ErrorAction SilentlyContinue
```

Do not delete state JSON files.

## STEP 1 - PATCH_12R1: add strict reference upload-ready wait

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "paste_method": text.count("def _paste_flow_reference_images_into_composer"),
    "reference_count_method": text.count("def _flow_composer_reference_count"),
    "existing_wait_helper": text.count("def _wait_for_flow_reference_uploads_ready"),
}

print(checks)

assert checks["paste_method"] == 1
assert checks["reference_count_method"] == 1
assert checks["existing_wait_helper"] == 0
print("PATCH_12R1_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Insert immediately before

```python
    def _paste_flow_reference_images_into_composer(self, page, source_images: List[str]) -> None:
```

### Add

```python
    def _wait_for_flow_reference_uploads_ready(self, page, expected_count: int) -> None:
        deadline = time.time() + max(
            FLOW_REFERENCE_COMPOSER_TIMEOUT_SECONDS,
            FLOW_CLIPBOARD_PASTE_WAIT_SECONDS * max(1, expected_count) + FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS,
        )

        stable_required = 3
        stable_seen = 0
        last_count = -1

        self._flow_user_info(
            "Waiting for pasted reference uploads to finish",
            expected_count=expected_count,
            timeout_seconds=round(deadline - time.time(), 2),
        )

        while time.time() < deadline:
            try:
                current_count = self._flow_composer_reference_count(page)
            except Exception as exc:
                current_count = -1
                self._flow_user_info("Reference upload count check skipped", error=str(exc)[:200])

            if current_count >= expected_count:
                if current_count == last_count:
                    stable_seen += 1
                else:
                    stable_seen = 1
                    last_count = current_count

                self._flow_user_info(
                    "Reference upload count observed",
                    expected_count=expected_count,
                    current_count=current_count,
                    stable_seen=stable_seen,
                    stable_required=stable_required,
                )

                if stable_seen >= stable_required:
                    self._flow_user_info(
                        "Reference uploads ready",
                        expected_count=expected_count,
                        current_count=current_count,
                    )
                    return
            else:
                stable_seen = 0
                last_count = current_count
                self._flow_user_info(
                    "Reference uploads still pending",
                    expected_count=expected_count,
                    current_count=current_count,
                )

            page.wait_for_timeout(1000)

        fail(
            "FLOW_REFERENCE_UPLOAD_NOT_READY",
            "Flow pasted reference images did not become stable in the composer before submit.",
            field="flow_reference_uploads",
            expected=f"composer_reference_count >= {expected_count} and stable before submit",
            actual=json.dumps(
                {
                    "composer_reference_count": self._flow_composer_reference_count(page),
                    "source_image_count": expected_count,
                    "url": getattr(page, "url", ""),
                },
                ensure_ascii=False,
            ),
            stage="PROCESSING",
        )
```

## STEP 2 - PATCH_12R2: call upload-ready wait before submit

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "final_settle_log": text.count("Flow reference images pasted into composer"),
    "ready_call": text.count("self._wait_for_flow_reference_uploads_ready(page, len(source_images))"),
}

print(checks)

assert checks["final_settle_log"] >= 1
assert checks["ready_call"] == 0
print("PATCH_12R2_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Insert in `_paste_flow_reference_images_into_composer(...)`

Immediately after:

```python
        page.wait_for_timeout(int(FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS * 1000))
```

Add:

```python
        self._wait_for_flow_reference_uploads_ready(page, len(source_images))
```

## STEP 3 - PATCH_12R3: make Flow capture tolerate closed/replaced page

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "capture_method": text.count("def _capture_flow_generated_image_base64"),
    "raw_wait": text.count("page.wait_for_timeout(1000)"),
    "existing_safe_wait": text.count("def _flow_safe_capture_wait"),
}

print(checks)

assert checks["capture_method"] == 1
assert checks["raw_wait"] >= 1
assert checks["existing_safe_wait"] == 0
print("PATCH_12R3_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Insert immediately before

```python
    def _capture_flow_generated_image_base64(self, page) -> str:
```

### Add

```python
    def _flow_safe_capture_wait(self, page, wait_ms: int):
        try:
            if page is None or page.is_closed():
                self._flow_user_info("Flow capture page closed; reacquiring Flow page")
                return self._page()

            page.wait_for_timeout(wait_ms)
            return page

        except Exception as exc:
            error_text = str(exc)
            if "Target page, context or browser has been closed" in error_text or "TargetClosedError" in error_text:
                self._flow_user_info(
                    "Flow capture page target closed; reacquiring Flow page",
                    error=error_text[:300],
                )
                self._page_obj = None
                return self._page()

            raise
```

### Replace inside `_capture_flow_generated_image_base64(...)`

Replace:

```python
            page.wait_for_timeout(1000)
```

with:

```python
            page = self._flow_safe_capture_wait(page, 1000)
```

## STEP 4 - PATCH_12R4: add capture INFO at start and scan loop

### Dry-run

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

checks = {
    "capture_method": text.count("def _capture_flow_generated_image_base64"),
    "capture_info_existing": text.count("Flow capture scan started"),
}

print(checks)

assert checks["capture_method"] == 1
assert checks["capture_info_existing"] == 0
print("PATCH_12R4_DRY_RUN_PASS")
'@ | D:\TOOLS\Python314\python.exe -
```

### Insert after

```python
        deadline = time.time() + FLOW_IMAGE_TIMEOUT_SECONDS
        last_error = ""
```

Add:

```python
        self._flow_user_info(
            "Flow capture scan started",
            timeout_seconds=FLOW_IMAGE_TIMEOUT_SECONDS,
            url=getattr(page, "url", ""),
        )
```

### Insert before each existing successful capture `return image_base64`

Add the matching user trace:

```python
                        self._flow_user_info("Flow generated image captured", capture_method="tile", selector=selector)
```

and:

```python
                    self._flow_user_info("Flow generated image captured", capture_method="screenshot", selector=selector)
```

## STEP 5 - R-Validation 1: compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

## STEP 6 - R-Validation 2: static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "def _wait_for_flow_reference_uploads_ready",
    "Reference uploads ready",
    "FLOW_REFERENCE_UPLOAD_NOT_READY",
    "self._wait_for_flow_reference_uploads_ready(page, len(source_images))",
    "def _flow_safe_capture_wait",
    "Flow capture page target closed; reacquiring Flow page",
    "page = self._flow_safe_capture_wait(page, 1000)",
    "Flow capture scan started",
]

for marker in required:
    assert marker in text, marker

print("PATCH_12R_UPLOAD_READY_CAPTURE_RESILIENCE_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12R_UPLOAD_READY_CAPTURE_RESILIENCE_STATIC_OK
```

## STEP 7 - R-Validation 3: method sanity

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
    "_wait_for_flow_reference_uploads_ready",
    "_flow_safe_capture_wait",
    "_capture_flow_generated_image_base64",
    "_paste_flow_reference_images_into_composer",
]

for name in required:
    assert hasattr(adapter, name), name

print("PATCH_12R_UPLOAD_READY_CAPTURE_RESILIENCE_METHODS_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12R_UPLOAD_READY_CAPTURE_RESILIENCE_METHODS_OK
```

# Resume STEP 7 after PATCH_12R



In the code, `_wait_for_flow_reference_uploads_ready(...)` relies entirely on `_flow_composer_reference_count(page)`. After each paste, the code calls `_flow_composer_reference_count(page)` again and later blocks submit until that count reaches the number of source images. 

The problem is likely here: `_flow_composer_reference_count(...)` only counts visible `img`, `canvas`, `[role='img']`, some `data-testid` nodes, and remove buttons inside broad scopes like `form`, `[data-testid*='composer']`, `[class*='composer']`, `[class*='prompt']`, or `main`. 

So if Flow renders the attached reference images as any of these, the counter can stay zero even though the UI looks correct:

```text
1. CSS background-image instead of <img>
2. attachment chip outside the searched composer scope
3. Radix/React portal outside the form/main subtree being inspected
4. hidden input/state object with visible canvas elsewhere
5. thumbnail rendered inside a shadow-like component structure
6. visible thumbnail smaller/different than the current >=16px media rules
7. attachment represented by text/button metadata, not img/canvas
```

So this is not an upload failure yet. It is a **DOM contract mismatch** between Flow’s actual attachment UI and our detector.

## What we need to inspect

Do this with the page in the exact state where the two reference images are visibly attached in the composer, before clicking submit.

### STEP 1. Inspect the actual attached image/chip element

In Chrome:

```text
F12 → Elements tab → click the element picker → click one attached reference image/chip in the composer
```

Then run this in the DevTools Console:

```javascript
(() => {
  const el = $0;

  function attrs(node) {
    if (!node || !node.attributes) return {};
    return Object.fromEntries([...node.attributes].map(a => [a.name, a.value]));
  }

  function rect(node) {
    const r = node.getBoundingClientRect();
    return {
      x: Math.round(r.x),
      y: Math.round(r.y),
      width: Math.round(r.width),
      height: Math.round(r.height),
      visible: !!(r.width && r.height)
    };
  }

  const chain = [];
  let node = el;

  for (let i = 0; node && i < 12; i++, node = node.parentElement) {
    chain.push({
      depth: i,
      tag: node.tagName,
      attrs: attrs(node),
      text: (node.innerText || node.textContent || "").trim().slice(0, 300),
      rect: rect(node),
      outerHTML: node.outerHTML.slice(0, 1200)
    });
  }

  const result = {
    url: location.href,
    selected: chain[0],
    ancestors: chain
  };

  console.log(result);
  copy(JSON.stringify(result, null, 2));
})();
```

Send back the copied JSON.

This tells us the real tag, classes, `data-testid`, ARIA labels, bounding box, and ancestor structure of the visible attachment.

---

### STEP 2. Inspect all visible media-like nodes near the composer

Run this while the images are visibly attached:

```javascript
(() => {
  function attrs(node) {
    if (!node || !node.attributes) return {};
    return Object.fromEntries([...node.attributes].map(a => [a.name, a.value]));
  }

  function rect(node) {
    const r = node.getBoundingClientRect();
    return {
      x: Math.round(r.x),
      y: Math.round(r.y),
      width: Math.round(r.width),
      height: Math.round(r.height),
      visible: !!(r.width && r.height)
    };
  }

  const selectors = [
    "img",
    "canvas",
    "[role='img']",
    "[aria-label*='Remove']",
    "[aria-label*='remove']",
    "[data-testid]",
    "[class*='attach' i]",
    "[class*='media' i]",
    "[class*='image' i]",
    "[class*='asset' i]",
    "[class*='chip' i]",
    "[class*='prompt' i]",
    "[class*='composer' i]"
  ].join(",");

  const rows = [...document.querySelectorAll(selectors)]
    .map((node, index) => ({
      index,
      tag: node.tagName,
      attrs: attrs(node),
      text: (node.innerText || node.textContent || "").trim().slice(0, 200),
      rect: rect(node),
      src: node.getAttribute("src") || "",
      bg: getComputedStyle(node).backgroundImage || "",
      outerHTML: node.outerHTML.slice(0, 800)
    }))
    .filter(row => row.rect.visible)
    .sort((a, b) => a.rect.y - b.rect.y || a.rect.x - b.rect.x);

  console.table(rows.map(r => ({
    index: r.index,
    tag: r.tag,
    y: r.rect.y,
    x: r.rect.x,
    w: r.rect.width,
    h: r.rect.height,
    text: r.text,
    src: r.src.slice(0, 60),
    bg: r.bg.slice(0, 60),
    testid: r.attrs["data-testid"] || "",
    cls: r.attrs["class"] || "",
    aria: r.attrs["aria-label"] || ""
  })));

  copy(JSON.stringify({
    url: location.href,
    viewport: { width: innerWidth, height: innerHeight },
    visible_media_like_nodes: rows
  }, null, 2));
})();
```

Send back the copied JSON.

This will show whether the visible attachment is an `img`, `canvas`, CSS background, chip, button, or some other node.

---

### STEP 3. Inspect the composer textbox and its nearby DOM

Run this after images are attached:

```javascript
(() => {
  function attrs(node) {
    if (!node || !node.attributes) return {};
    return Object.fromEntries([...node.attributes].map(a => [a.name, a.value]));
  }

  function rect(node) {
    const r = node.getBoundingClientRect();
    return {
      x: Math.round(r.x),
      y: Math.round(r.y),
      width: Math.round(r.width),
      height: Math.round(r.height),
      visible: !!(r.width && r.height)
    };
  }

  const boxes = [...document.querySelectorAll("textarea,[contenteditable='true'],[role='textbox']")]
    .map((node, index) => ({
      index,
      tag: node.tagName,
      attrs: attrs(node),
      text: (node.innerText || node.textContent || node.value || "").trim().slice(0, 300),
      rect: rect(node),
      outerHTML: node.outerHTML.slice(0, 1000)
    }))
    .filter(row => row.rect.visible)
    .sort((a, b) => b.rect.y - a.rect.y);

  const composer = boxes[0] ? document.querySelectorAll("textarea,[contenteditable='true'],[role='textbox']")[boxes[0].index] : null;

  const ancestors = [];
  let node = composer;
  for (let i = 0; node && i < 10; i++, node = node.parentElement) {
    ancestors.push({
      depth: i,
      tag: node.tagName,
      attrs: attrs(node),
      text: (node.innerText || node.textContent || "").trim().slice(0, 500),
      rect: rect(node),
      outerHTML: node.outerHTML.slice(0, 1500)
    });
  }

  const result = {
    url: location.href,
    composer_candidates: boxes,
    selected_bottom_composer: boxes[0] || null,
    composer_ancestors: ancestors
  };

  console.log(result);
  copy(JSON.stringify(result, null, 2));
})();
```

Send back the copied JSON.

This tells us whether our current scope assumptions are wrong. Specifically, it will show whether the attachments are siblings/ancestors of the composer, or rendered somewhere else entirely.

## What I expect we will learn

Most likely, the reference images are being rendered in a container that `_flow_composer_reference_count(...)` is not scanning correctly. The current script says “0” because it is not looking at the same DOM structure that the human-visible composer is using.

Once we have the three JSON outputs above, we can define the detector against the actual Flow DOM instead of guessing. No further patch should be written until those outputs identify the correct selector/relationship.
