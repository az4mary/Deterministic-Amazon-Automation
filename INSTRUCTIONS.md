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

---

---

# Before applying PATCH_10I

Stop the currently running Validation D process. The running process is using old detector logic, so it cannot be fixed in-place.

```powershell
# Use the PID if known:
Stop-Process -Id <PID> -Force

# Or stop the active terminal process with Ctrl+C.
```

Do not treat this as a failed state mutation. The current state is still at step `11`, which is correct for retrying STEP `12`.

---

# PATCH_10I — Robust browser generated-image detection/capture

## Purpose

Fix only the failed point in Validation D:

```json
{
  "failed_point": "_capture_latest_browser_generated_image_base64",
  "symptom": "generated image visible in browser but not captured/persisted",
  "fix": "scan broader generated-image candidates, skip pre-existing reference thumbnails, support img/canvas/role-img surfaces, capture by data URL or rendered screenshot"
}
```

## DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_10I",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

## FIND

Replace the entire current method:

```python
    def _capture_latest_browser_generated_image_base64(self, page, before_assistant_count: int) -> str:
```

through the end of its `fail(...)` block immediately before:

```python
    def execute_image(
```

## REPLACE WITH

```python
    def _capture_latest_browser_generated_image_base64(self, page, before_assistant_count: int) -> str:
        deadline = time.time() + BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS
        last_assistant_excerpt = ""
        last_diag_log = 0.0

        def locator_key(locator) -> str:
            try:
                src = locator.get_attribute("src") or ""
            except Exception:
                src = ""
            try:
                alt = locator.get_attribute("alt") or ""
            except Exception:
                alt = ""
            try:
                box = locator.bounding_box() or {}
            except Exception:
                box = {}

            # Do not store full data URLs in the baseline key; only a stable prefix.
            if src.startswith("data:image"):
                src_key = src[:120]
            else:
                src_key = src

            return json.dumps(
                {
                    "src": src_key,
                    "alt": alt[:120],
                    "w": int(box.get("width", 0) or 0),
                    "h": int(box.get("height", 0) or 0),
                },
                sort_keys=True,
            )

        def visible_large_enough(locator) -> bool:
            try:
                if not locator.is_visible():
                    return False
            except Exception:
                return False

            try:
                box = locator.bounding_box() or {}
            except Exception:
                return False

            width = float(box.get("width", 0) or 0)
            height = float(box.get("height", 0) or 0)

            # Skip icons, avatars, buttons, and uploaded-reference thumbnails.
            return width >= 256 and height >= 256

        def collect_candidate_locators():
            locators = []

            selectors = [
                "[data-message-author-role='assistant'] img",
                "[data-message-author-role='assistant'] picture img",
                "[data-message-author-role='assistant'] canvas",
                "[data-message-author-role='assistant'] [role='img']",
                "article img",
                "article picture img",
                "article canvas",
                "main img[src^='blob:']",
                "main img[src^='data:image']",
                "main img[src*='oaiusercontent']",
                "main img[src*='oaidalleapiprodscus']",
                "main img[src*='openai']",
                "main canvas",
                "[role='img']",
            ]

            for sel in selectors:
                try:
                    collection = page.locator(sel)
                    count = min(collection.count(), 20)
                    for idx in range(count):
                        locators.append((sel, collection.nth(idx)))
                except Exception:
                    pass

            return locators

        baseline_keys = set()
        for _sel, candidate in collect_candidate_locators():
            try:
                if visible_large_enough(candidate):
                    baseline_keys.add(locator_key(candidate))
            except Exception:
                pass

        json_log(
            level="INFO",
            message="Browser image generation wait started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_image_generation_wait_start",
                "timeout_seconds": BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS,
                "before_assistant_count": before_assistant_count,
                "baseline_large_image_count": len(baseline_keys),
            },
        )

        while time.time() < deadline:
            assistant_count = page.locator("[data-message-author-role='assistant']").count()

            if assistant_count > before_assistant_count:
                try:
                    assistant = page.locator("[data-message-author-role='assistant']").last
                    last_assistant_excerpt = assistant.inner_text(timeout=5000).strip()[:1000]
                except Exception:
                    last_assistant_excerpt = ""

            candidate_count = 0
            visible_large_count = 0
            skipped_baseline_count = 0

            for selector, candidate in collect_candidate_locators():
                candidate_count += 1

                try:
                    if not visible_large_enough(candidate):
                        continue

                    visible_large_count += 1
                    key = locator_key(candidate)

                    if key in baseline_keys:
                        skipped_baseline_count += 1
                        continue

                    # Give the rendered asset a brief moment to finish loading.
                    page.wait_for_timeout(1500)

                    src = ""
                    try:
                        src = candidate.get_attribute("src") or ""
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
                                "selector": selector,
                                "assistant_count": assistant_count,
                                "image_base64_chars": len(image_base64),
                            },
                        )
                        return image_base64

                    screenshot_bytes = candidate.screenshot(timeout=self.action_timeout_ms)
                    image_base64 = base64.b64encode(screenshot_bytes).decode("ascii")

                    json_log(
                        level="INFO",
                        message="Browser generated image captured from candidate locator",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "browser_generated_image_captured_candidate_screenshot",
                            "selector": selector,
                            "assistant_count": assistant_count,
                            "image_base64_chars": len(image_base64),
                        },
                    )
                    return image_base64

                except Exception as e:
                    json_log(
                        level="DEBUG",
                        message="Browser generated image candidate skipped",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "browser_generated_image_candidate_skipped",
                            "selector": selector,
                            "error": str(e)[:300],
                        },
                    )

            now = time.time()
            if now - last_diag_log >= 10.0:
                last_diag_log = now
                json_log(
                    level="DEBUG",
                    message="Browser image generation capture scan continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "browser_image_capture_scan_continue",
                        "assistant_count": assistant_count,
                        "candidate_count": candidate_count,
                        "visible_large_count": visible_large_count,
                        "skipped_baseline_count": skipped_baseline_count,
                        "last_assistant_excerpt": last_assistant_excerpt[:300],
                    },
                )

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
            expected="visible generated image candidate captured from assistant/main image surface",
            actual=last_assistant_excerpt[:1000],
            stage="PROCESSING",
        )
```

---

# PATCH_10I validation

## I-Validation 1 — compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

Expected:

```
PASS / no output
```

## I-Validation 2 — static marker check

```powershell
@'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "baseline_large_image_count",
    "Browser image generation capture scan continuing",
    "browser_generated_image_captured_candidate_screenshot",
    "Browser generated image candidate skipped",
    "visible_large_enough",
    "collect_candidate_locators",
]

for marker in required:
    assert marker in text, marker

print("PATCH_10I_CAPTURE_DETECTOR_STATIC_OK")
'@ | D:\TOOLS\Python314\python.exe -
```

Expected:

```
PATCH_10I_CAPTURE_DETECTOR_STATIC_OK
```

---

CONFIRMATION REQUIRED:
YES.

# Re-run Validation D only

```powershell
$env:SKIP_IMAGES="0"
$env:IMAGE_REFERENCE_STRICT="1"
$env:EXECUTION_BACKEND="browser"
$env:BROWSER_CDP_URL="http://127.0.0.1:9222"
$env:BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS="900"

D:\TOOLS\Python314\python.exe workflow_orchestrator.py --resume --enable-image-generation --stop-after 12
```

Expected:

```json
{
  "expected": [
    "resume starts at 12",
    "Image generation adapter handoff started",
    "Browser image generation started",
    "source_image_count=2 or greater",
    "Browser image generation reference images attached",
    "Browser image generation prompt submission attempted",
    "Browser image generation capture scan continuing appears if image is not immediately captured",
    "Browser generated image captured from candidate locator OR data URL",
    "output/generated_images/image_12.png exists",
    "generated_image_1 exists in workflow_state.json",
    "generated_image_1.generated_image.source_images_used is non-empty",
    "last_completed_step=12",
    "OUTPUT/SUCCESS"
  ]
}
```

## Current sequence status

```json
{
  "Validation_B": "PASS",
  "Validation_C": "PASS",
  "PATCH_10H": "PASS",
  "Validation_D": "FAILED_AT_IMAGE_CAPTURE_DETECTOR",
  "PATCH_10I": "READY_TO_APPLY",
  "STATE_17": "BLOCKED_UNTIL_VALIDATION_D_PASS"
}
```