# INSTRUCTIONS

- Identified exact failing step: `step_id=19`, `kind=text`, after successful completion through step `18`.
- Confirmed persisted state is safe and resumable from `last_completed_step=18`.

SEARCH VALIDATION RESULT:

- Full resume command failed with `SELECTOR_TIMEOUT`, field `browser_input_box`.
- Actual completed progress:
    - completed through step `18`
    - generated images present through `image_18.png`
    - missing `image_20.png`, `image_22.png`, `image_24.png`
    - `last_completed_step=18`
    - `generated_image_1` through `generated_image_4` complete
    - `generated_image_5` through `generated_image_7` not yet complete.
- `workflow_state.json` confirms outputs through step `18`, including generated image outputs for `12`, `14`, `16`, and `18`.

VALIDATED DECISION:

```json
{
  "STATE_16": "FAILED_AT_FULL_RUN_CHECKPOINT",
  "exact_failing_step": "19",
  "failure_code": "SELECTOR_TIMEOUT",
  "failure_field": "browser_input_box",
  "last_completed_step": "18",
  "STATE_17_ALLOWED": false,
  "next_patch": "PATCH_10J",
  "patch_scope": "fix browser composer recovery after image-generation steps only"
}
```

OUTPUT:

# Diagnosis

The script successfully completed the sequence:

```json
{
  "completed": ["13", "14", "15", "16", "17", "18"],
  "failed_at": "19"
}
```

Step `19` is a text/image-prompt step after step `18`, which was an actual browser image-generation step.

The likely failure mechanism is now narrow:

```json
{
  "root_cause": "After browser image generation, the ChatGPT page can remain in a generated-image/canvas/result surface where the normal composer is hidden or not immediately available. The next text step starts a new prompt, but _start_new_chat does not force a clean composer state strongly enough before send_prompt calls _input_box.",
  "failed_component": "_start_new_chat / composer recovery before text prompt submission",
  "not_failed": [
    "image generation adapter handoff",
    "reference image attachment",
    "image capture from canvas",
    "state persistence through step 18",
    "step numbering",
    "PATCH_SET_02 image context routing",
    "PATCH_SET_03 prompt wording"
  ]
}
```

---

# PATCH_10J — Force clean browser composer after generated-image steps

## Purpose

Ensure that when a text/image-prompt step starts after a browser image-generation step, the browser is reset to a clean ChatGPT composer surface before attempting `_input_box()`.

This fixes the step `19` failure without changing image generation, image context routing, prompt docs, or output schemas.

---

## PATCH_10J1 — Add new-chat composer recovery controls

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10J1",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS = float(os.getenv("BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS", "300"))
```

### REPLACE WITH

```python
BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS = float(os.getenv("BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS", "300"))
BROWSER_NEW_CHAT_READY_TIMEOUT_MS = int(os.getenv("BROWSER_NEW_CHAT_READY_TIMEOUT_MS", "30000"))
BROWSER_FORCE_ROOT_NEW_CHAT = os.getenv("BROWSER_FORCE_ROOT_NEW_CHAT", "1") == "1"
```

---

## PATCH_10J2 — Replace `_start_new_chat(...)` with force-clean composer recovery

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10J2",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

Replace the full current method:

```python
    def _start_new_chat(self, page) -> None:
```

through the line immediately before:

```python
    def _attach_images_for_state(self, page, state: Dict[str, Any]) -> None:
```

### REPLACE WITH

```python
    def _composer_available(self, page) -> bool:
        selectors = [
            "[contenteditable='true']",
            "div[contenteditable='true']",
            "[role='textbox']",
            "div[role='textbox']",
            "main [contenteditable='true']",
            "form [contenteditable='true']",
            "textarea#prompt-textarea",
            "textarea[data-testid='prompt-textarea']",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    return True
            except Exception:
                pass
        return False

    def _wait_for_clean_composer(self, page, *, reason: str) -> bool:
        deadline = time.time() + (BROWSER_NEW_CHAT_READY_TIMEOUT_MS / 1000.0)
        last_log = 0.0

        while time.time() < deadline:
            if self._composer_available(page):
                json_log(
                    level="DEBUG",
                    message="Browser clean composer ready",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "browser_clean_composer_ready",
                        "reason": reason,
                        "url": getattr(page, "url", ""),
                    },
                )
                return True

            now = time.time()
            if now - last_log >= 2.0:
                last_log = now
                json_log(
                    level="DEBUG",
                    message="Browser clean composer wait continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "browser_clean_composer_wait_continue",
                        "reason": reason,
                        "url": getattr(page, "url", ""),
                    },
                )

            page.wait_for_timeout(500)

        return False

    def _start_new_chat(self, page) -> None:
        # Establish a clean ChatGPT composer surface before every prompt.
        # This is intentionally stronger than a best-effort sidebar click because
        # generated-image/canvas result surfaces can leave the composer hidden.
        old_url = ""
        try:
            old_url = page.url or ""
        except Exception:
            old_url = ""

        json_log(
            level="DEBUG",
            message="Browser new chat reset started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_new_chat_reset_start",
                "old_url": old_url,
                "force_root": BROWSER_FORCE_ROOT_NEW_CHAT,
            },
        )

        # First dismiss transient UI layers that may trap focus after image generation.
        for key in ["Escape", "Escape"]:
            try:
                page.keyboard.press(key)
                page.wait_for_timeout(250)
            except Exception:
                pass

        # Prefer hard navigation to root when enabled. This is the most reliable
        # way to exit generated-image/canvas views and recover the normal composer.
        if BROWSER_FORCE_ROOT_NEW_CHAT:
            try:
                page.goto(self.chat_url or "https://chatgpt.com/", wait_until="domcontentloaded")
                page.wait_for_timeout(1000)
            except Exception as e:
                json_log(
                    level="DEBUG",
                    message="Browser root navigation for new chat failed",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "browser_root_navigation_failed",
                        "error": str(e)[:500],
                    },
                )

        if self._wait_for_clean_composer(page, reason="after_root_navigation"):
            return

        # Fallback: try the visible New Chat affordance.
        selectors = [
            "button[data-testid='new-chat-button']",
            "a[data-testid='new-chat-button']",
            "button:has-text('New chat')",
            "a:has-text('New chat')",
            "button[aria-label*='New chat']",
            "a[aria-label*='New chat']",
            "a[href='/']",
        ]

        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.click()
                    page.wait_for_timeout(1000)
                    if self._wait_for_clean_composer(page, reason=f"after_new_chat_click:{sel}"):
                        return
            except Exception:
                pass

        # Last resort: reload root and check again.
        try:
            page.goto(self.chat_url or "https://chatgpt.com/", wait_until="domcontentloaded")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
        except Exception:
            pass

        if self._wait_for_clean_composer(page, reason="after_root_reload"):
            return

        fail(
            "SELECTOR_TIMEOUT",
            "Could not recover clean ChatGPT composer after new-chat reset.",
            field="browser_clean_composer",
            expected="visible composer after root navigation/new chat reset",
            actual=f"old_url={old_url}; current_url={getattr(page, 'url', '')}",
            stage="PROCESSING",
        )
```

---

# PATCH_10J validation

## J-Validation 1 — compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```
PASS / no output
```

## J-Validation 2 — static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "BROWSER_NEW_CHAT_READY_TIMEOUT_MS",
    "BROWSER_FORCE_ROOT_NEW_CHAT",
    "def _composer_available",
    "def _wait_for_clean_composer",
    "Browser new chat reset started",
    "Browser clean composer ready",
    "Could not recover clean ChatGPT composer after new-chat reset",
]

for marker in required:
    assert marker in text, marker

print("PATCH_10J_COMPOSER_RECOVERY_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_10J_COMPOSER_RECOVERY_STATIC_OK
```

---

CONFIRMATION REQUIRED
YES

# Resume full-run validation

Do **not** rerun steps `01A–18`. Current state is valid and resumable from `18`.

Run only the remaining execution:

```powershell
$env:SKIP_IMAGES="0"
$env:IMAGE_REFERENCE_STRICT="1"
$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"
$env:BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS="900"
$env:BROWSER_FORCE_ROOT_NEW_CHAT="1"
$env:BROWSER_NEW_CHAT_READY_TIMEOUT_MS="30000"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --resume --enable-image-generation
```

Expected:

```json
{
  "expected_resume_start": "19",
  "expected_remaining_steps": ["19", "20", "21", "22", "23", "24"],
  "expected_new_image_prompts": ["19", "21", "23"],
  "expected_new_generated_images": ["20", "22", "24"],
  "expected_terminal": "OUTPUT/SUCCESS",
  "expected_last_completed_step": "24",
  "expected_generated_images_present": [
    "generated_image_1",
    "generated_image_2",
    "generated_image_3",
    "generated_image_4",
    "generated_image_5",
    "generated_image_6",
    "generated_image_7"
  ],
  "expected_generated_files_present": [
    "output/generated_images/image_12.png",
    "output/generated_images/image_14.png",
    "output/generated_images/image_16.png",
    "output/generated_images/image_18.png",
    "output/generated_images/image_20.png",
    "output/generated_images/image_22.png",
    "output/generated_images/image_24.png"
  ]
}
```

```markdown
## What happens if the full run fails?

Do **not** proceed to STATE 17.

Fix only the exact failed step, preserving the rest of the sequence.
```

```json
{
  "if_failure": {
    "step": "identify exact failing step",
    "action": "STOP and send report",
    "do_not": [
      "renumber validations",
      "rewrite prior patch sequence",
      "reopen PATCH_SET_02",
      "reopen PATCH_SET_03",
      "skip to bug logging"
    ]
  }
}
```

```json
{
  "required_files_after_run": [
    "output/logs/execution.jsonl",
    "output/workflow_state.json",
    "output/image_prompts.json",
    "output/generated_images directory listing"
  ]
}
```