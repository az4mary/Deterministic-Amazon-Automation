# PATCH_SET_12 - TITLE

Proceed with:

```text
PATCH_12R — enforce pasted-reference readiness before submit + recover from Flow page closure during capture
```

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
