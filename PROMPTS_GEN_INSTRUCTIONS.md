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
