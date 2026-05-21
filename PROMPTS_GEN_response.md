# PROMPTS_GEN Messenger Checkpoint - 2026-05-21T04:30:32.4687895-05:00

- Source URL: https://chatgpt.com/c/69b16c98-11c4-8328-8582-145ea2e5affa
- Page title: PROMPTS_GEN
- Local checkpoint time: `2026-05-21T04:30:32.4687895-05:00`
- Response detection: latest assistant response detected and stable

## Extracted response

STATE 16:
ACTION:

Proceed with PATCH_12L.

Scope: Flow prompt-composer discovery/activation only.

Do not change reference upload, image capture, metadata persistence, prompt docs, cooldowns, or step numbering.

Current blocker: FLOW_PROMPT_INPUT_MISSING; Flow project URL is reachable, but _find_flow_prompt_box(...) cannot discover a visible Flow prompt composer. 

PROMPTS_GEN_Progress

PATCH_12L — Flow prompt composer discovery/activation
STEP 1 — PATCH_12L1: add Flow prompt surface activation helper
Dry-run expectation
JSON
{
  "patch_id": "PATCH_12L1",
  "expected_insert_anchor_count": 1,
  "expected_existing_helper_count": 0,
  "halt_if_insert_anchor_count_is_not": 1
}
Insert immediately before
Python
Run
    def _find_flow_prompt_box(self, page):
Add
Python
Run
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
STEP 2 — PATCH_12L2: replace _find_flow_prompt_box(...)
Dry-run expectation
JSON
{
  "patch_id": "PATCH_12L2",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
Replace entire method

From:

Python
Run
    def _find_flow_prompt_box(self, page):

Through the line immediately before:

Python
Run
    def _fill_flow_prompt_box(self, page, prompt_box, prompt: str) -> None:
Replacement
Python
Run
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
STEP 3 — PATCH_12L3: replace _fill_flow_prompt_box(...)
Dry-run expectation
JSON
{
  "patch_id": "PATCH_12L3",
  "expected_method_count": 1,
  "expected_replacement_count": 1,
  "halt_if_method_count_is_not": 1
}
Replace entire method

From:

Python
Run
    def _fill_flow_prompt_box(self, page, prompt_box, prompt: str) -> None:

Through the line immediately before:

Python
Run
    def _submit_flow_prompt(self, page, prompt: str) -> None:
Replacement
Python
Run
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
PATCH_12L validation
STEP 4 — L-Validation 1: compile
PowerShell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py

Expected:

PASS / no output
STEP 5 — L-Validation 2: static marker check
PowerShell
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

Expected:

PATCH_12L_FLOW_PROMPT_DISCOVERY_STATIC_OK
STEP 6 — L-Validation 3: no-browser method sanity
PowerShell
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

Expected:

PATCH_12L_FLOW_PROMPT_DISCOVERY_METHODS_OK
Resume STEP 7 after PATCH_12L

Use the same command:

PowerShell
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
Expected checks
JSON
{
  "expected": [
    "resume starts at step 12",
    "Image generation adapter handoff started",
    "Flow adapter reused shared browser session",
    "Flow page ready",
    "Flow reference images uploaded",
    "Flow reference images attached to composer",
    "Flow model selected",
    "Flow prompt box discovered",
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
    "FLOW_PROMPT_INPUT_MISSING",
    "FLOW_PROMPT_INPUT_NOT_FILLED",
    "Locator.click: Timeout 120000ms exceeded",
    "Playwright Sync API inside the asyncio loop",
    "FLOW_IMAGE_BACKEND_NOT_IMPLEMENTED",
    "OpenAI image generation",
    "ChatGPT browser image generation"
  ]
}
Decision rule
JSON
{
  "if_STEP_7_passes": "PATCH_12L_CONFIRMED; proceed to Validation 6 full Flow run",
  "if_STEP_7_fails_with_FLOW_PROMPT_INPUT_MISSING": "attach execution log and Flow prompt surface summary from actual field",
  "if_STEP_7_fails_after_Flow_prompt_submitted": "patch only Flow generated-image capture logic"
}
