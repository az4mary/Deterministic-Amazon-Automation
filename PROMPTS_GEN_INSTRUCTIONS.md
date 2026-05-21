# INSTRUCTIONS

Source response: `PROMPTS_GEN_response.md`

Current messenger decision:

```text
STEP 6 - J-Validation 3 - Routing/session dry-run is confirmed proceed with STEP 7 - Resume Validation 5 - Step 12 Flow actual generation smoke test.
```

Previous cleanup decision:

```text
No cleanup is needed.
```

Preserve current artifacts for troubleshooting and resume:

```text
output/workflow_state.json
output/logs/execution.jsonl
output/image_prompts.json
output/image_content.json
output/generated_images/
```

Proceed with PATCH_12J on the current workspace.

## Global step rule

After every STEP:

1. Update `PATCH_SET_12_Progress.md` as-is.
2. Commit and push only the files required for that STEP.
3. Attach `PATCH_SET_12_Progress.md` to the current ChatGPT tab.
4. Wait until the upload is complete.
5. Prompt the messenger to confirm with this format:

```text
<STEP_ID> is complete. Please reply "<STEP_ID> is confirmed proceed with <NEXT_STEP_ID>".
```

Do not proceed to the next STEP until the current STEP is confirmed.

## **CURRENT BLOCKER -** **STEP 2 troubleshooting packet requested by messenger**

Do not retry or fix PATCH_12J2 yet.

Provide the messenger with:

```text
1. Exact apply_patch payload/command used for PATCH_12J2, including full *** Begin Patch to *** End Patch text.
2. Full terminal output from the failed apply_patch, not only the summary line.
3. Output of git diff -- workflow_orchestrator.py.
4. Output of git status --short.
5. Confirmation whether workflow_orchestrator.py had any manual formatting, line-ending, or whitespace changes after PATCH_12J1 and before attempting PATCH_12J2.
```

No additional source files are needed right now, according to the messenger.

## **STEP 1 -** **PATCH_12J1 - Allow Flow adapter to receive a shared browser adapter**

Target file:

```text
workflow_orchestrator.py
```

Dry-run expectation:

```json
{
  "patch_id": "PATCH_12J1",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

Find:

```python
class FlowBrowserImageGenerationAdapter(PromptExecutionAdapter):
    def __init__(self, cdp_url: str, flow_url: str, action_timeout_ms: int) -> None:
        self.cdp_url = cdp_url
        self.flow_url = flow_url
        self.action_timeout_ms = action_timeout_ms
        self._playwright = None
        self._browser = None
        self._context = None
        self._page_obj = None
```

Replace with:

```python
class FlowBrowserImageGenerationAdapter(PromptExecutionAdapter):
    def __init__(
        self,
        cdp_url: str,
        flow_url: str,
        action_timeout_ms: int,
        shared_browser_adapter: Optional[BrowserPromptExecutionAdapter] = None,
    ) -> None:
        self.cdp_url = cdp_url
        self.flow_url = flow_url
        self.action_timeout_ms = action_timeout_ms
        self.shared_browser_adapter = shared_browser_adapter
        self._playwright = None
        self._browser = None
        self._context = None
        self._page_obj = None
```

Execution:

1. Run dry-run match count.
2. If actual match count is not `1`, stop and report.
3. Apply only PATCH_12J1.
4. Commit only PATCH_12J1.
5. Push only PATCH_12J1 to origin.

## **STEP 2 -** **PATCH_12J2 - Reuse shared Playwright/CDP objects inside Flow `_page()`**

Target file:

```text
workflow_orchestrator.py
```

Messenger override:

```text
Use a method-body replacement, not the failed hunk.
Replace the entire FlowBrowserImageGenerationAdapter._page() method from def _page(self): through the line immediately before def _flow_ready(self, page) -> bool:.
```

Dry-run expectation:

```json
{
  "patch_id": "PATCH_12J2",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

Find method boundary:

```python
class FlowBrowserImageGenerationAdapter(PromptExecutionAdapter):
    ...
    def _page(self):
        ...
    def _flow_ready(self, page) -> bool:
```

Replacement rule:

```text
Replace only the full _page() method. Preserve def _flow_ready(self, page) -> bool: and everything after it.
```

Replacement method:

```python
    def _page(self):
        if self._page_obj is not None:
            try:
                if not self._page_obj.is_closed() and "labs.google/fx/tools/flow" in (self._page_obj.url or ""):
                    return self._page_obj
            except Exception:
                self._page_obj = None

        if self._browser is None:
            shared = self.shared_browser_adapter
            if shared is not None and getattr(shared, "_browser", None) is not None:
                self._playwright = getattr(shared, "_playwright", None)
                self._browser = getattr(shared, "_browser", None)
                self._context = getattr(shared, "_context", None)
                json_log(
                    level="INFO",
                    message="Flow adapter reused shared browser session",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_reuse_shared_browser_session",
                        "source_adapter": "BrowserPromptExecutionAdapter",
                    },
                )
            else:
                self._playwright = sync_playwright().start()
                try:
                    self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
                except Exception:
                    if "localhost" in self.cdp_url:
                        alt = self.cdp_url.replace("localhost", "127.0.0.1")
                        try:
                            self._browser = self._playwright.chromium.connect_over_cdp(alt)
                            self.cdp_url = alt
                        except Exception as exc:
                            fail(
                                "FLOW_PAGE_UNAVAILABLE",
                                "Unable to connect to Chrome over CDP for Flow image generation.",
                                field="BROWSER_CDP_URL",
                                expected="reachable Chrome remote debugging endpoint",
                                actual=f"{alt}: {exc}",
                                stage="PROCESSING",
                            )
                    else:
                        fail(
                            "FLOW_PAGE_UNAVAILABLE",
                            "Unable to connect to Chrome over CDP for Flow image generation.",
                            field="BROWSER_CDP_URL",
                            expected="reachable Chrome remote debugging endpoint",
                            actual=self.cdp_url,
                            stage="PROCESSING",
                        )

        chosen_context = None
        chosen_page = None
        for ctx in self._browser.contexts:
            for page in ctx.pages:
                try:
                    if "labs.google/fx/tools/flow" in (page.url or ""):
                        chosen_context = ctx
                        chosen_page = page
                        break
                except Exception:
                    continue
            if chosen_page is not None:
                break

        if chosen_context is None:
            if self._context is not None:
                chosen_context = self._context
            elif self._browser.contexts:
                chosen_context = self._browser.contexts[0]
            else:
                chosen_context = self._browser.new_context()

        if chosen_page is None:
            try:
                chosen_page = chosen_context.new_page()
                chosen_page.goto(self.flow_url, wait_until="domcontentloaded", timeout=self.action_timeout_ms)
            except Exception as exc:
                fail(
                    "FLOW_PAGE_UNAVAILABLE",
                    "Flow page could not be opened or navigated.",
                    field="FLOW_URL",
                    expected="reachable Flow project URL",
                    actual=f"{self.flow_url}: {exc}",
                    stage="PROCESSING",
                )

        self._context = chosen_context
        self._page_obj = chosen_page
        try:
            chosen_page.bring_to_front()
        except Exception:
            pass
        self._wait_for_flow_ready(chosen_page)
        return chosen_page
```

Execution:

1. Run dry-run method-boundary match count.
2. If actual match count is not `1`, stop and report.
3. Apply only PATCH_12J2.
4. Commit only PATCH_12J2.
5. Push only PATCH_12J2 to origin.

## **STEP 3 -** **PATCH_12J3 - Pass active ChatGPT browser adapter into Flow adapter factory**

Target file:

```text
workflow_orchestrator.py
```

Dry-run expectation:

```json
{
  "patch_id": "PATCH_12J3",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

Find:

```python
def get_image_execution_adapter() -> PromptExecutionAdapter:
    global IMAGE_EXECUTION_ADAPTER
    if IMAGE_EXECUTION_ADAPTER is None:
        if IMAGE_EXECUTION_BACKEND == "flow_browser":
            IMAGE_EXECUTION_ADAPTER = FlowBrowserImageGenerationAdapter(
                BROWSER_CDP_URL,
                FLOW_URL,
                BROWSER_ACTION_TIMEOUT_MS,
            )
        else:
            IMAGE_EXECUTION_ADAPTER = get_text_execution_adapter()
    return IMAGE_EXECUTION_ADAPTER
```

Replace with:

```python
def get_image_execution_adapter() -> PromptExecutionAdapter:
    global IMAGE_EXECUTION_ADAPTER
    if IMAGE_EXECUTION_ADAPTER is None:
        if IMAGE_EXECUTION_BACKEND == "flow_browser":
            text_adapter = get_text_execution_adapter()
            shared_browser_adapter = text_adapter if isinstance(text_adapter, BrowserPromptExecutionAdapter) else None
            IMAGE_EXECUTION_ADAPTER = FlowBrowserImageGenerationAdapter(
                BROWSER_CDP_URL,
                FLOW_URL,
                BROWSER_ACTION_TIMEOUT_MS,
                shared_browser_adapter=shared_browser_adapter,
            )
        else:
            IMAGE_EXECUTION_ADAPTER = get_text_execution_adapter()
    return IMAGE_EXECUTION_ADAPTER
```

Execution:

1. Run dry-run match count.
2. If actual match count is not `1`, stop and report.
3. Apply only PATCH_12J3.
4. Commit only PATCH_12J3.
5. Push only PATCH_12J3 to origin.

## **STEP 4 -** **J-Validation 1 - Compile**

Run only after PATCH_12J1, PATCH_12J2, and PATCH_12J3 are confirmed.

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```text
PASS / no output
```

## **STEP 5 -** **J-Validation 2 - Static marker check**

Run only after J-Validation 1 is confirmed.

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "shared_browser_adapter: Optional[BrowserPromptExecutionAdapter] = None",
    "self.shared_browser_adapter = shared_browser_adapter",
    "Flow adapter reused shared browser session",
    "flow_reuse_shared_browser_session",
    "shared_browser_adapter=shared_browser_adapter",
]

for marker in required:
    assert marker in text, marker

print("PATCH_12J_SHARED_BROWSER_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12J_SHARED_BROWSER_STATIC_OK
```

## **STEP 6 -** **J-Validation 3 - Routing/session dry-run**

Run only after J-Validation 2 is confirmed. No browser call.

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

assert isinstance(adapter, w.FlowBrowserImageGenerationAdapter), type(adapter)
assert adapter.shared_browser_adapter is w.TEXT_EXECUTION_ADAPTER
assert adapter.cdp_url == w.BROWSER_CDP_URL
assert adapter.flow_url == w.FLOW_URL

print("PATCH_12J_SHARED_BROWSER_ROUTING_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```text
PATCH_12J_SHARED_BROWSER_ROUTING_OK
```

## **STEP 7 -** **Resume Validation 5 - Step 12 Flow actual generation smoke test**

Run only after J-Validation 3 is confirmed.

Because the current failed state reached `last_completed_step=11`, resume directly into step 12.

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

Expected:

```json
{
  "expected": [
    "resume starts at step 12",
    "Image generation adapter handoff started",
    "Flow adapter reused shared browser session",
    "Flow page ready",
    "Flow reference images attached",
    "Flow model selected",
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
    "ChatGPT browser image generation"
  ]
}
```

# PATCH_12K — Flow composer attachment + prompt submission hardening

* Scope: **Flow reference attachment-to-composer + Flow prompt-box submission only**.
* Do **not** touch image capture, metadata persistence, prompt docs, cooldowns, or step numbering.

Evidence: STEP 7 passed Flow session reuse, Flow readiness, model selection, and initial upload, but failed because references were added to Flow/gallery instead of the active composer, then `_submit_flow_prompt()` timed out at `prompt_box.click(...)`.  Current code logs reference success immediately after `file_input.set_input_files(...)`, before proving the images are usable in the composer. 

---


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
