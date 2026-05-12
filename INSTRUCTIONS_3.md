# INSTRUCTIONS_3

- Reclassified `PATCH_SET_05` as **partial pass but runtime fail**.
- Confirmed `01A` still did not complete; `outputs` remains empty and there is no `prompt_01A`.

## Diagnosis

`PATCH_SET_05` fixed the prior stabilization/capture path, but the latest run failed earlier.

Last reached logs:

```
Step started: 01A
Browser text execution started
Browser page ready
Browser payload built
Browser JSON attempt started
Browser prompt send started
```

Not reached:

```
Browser input box resolved
Browser prompt submission attempted
Browser assistant response wait started
```

The browser probe after stopping the orphan process showed:

```
textareas=0
contenteditables=1
visibleContenteditables=1
```

So the page did have a usable composer, but the script did not reach it. The likely cause is `_input_box()` waiting too long on missing textarea selectors before checking `[contenteditable='true']`. With `BROWSER_ACTION_TIMEOUT_MS=120000`, each absent selector can consume a large timeout window.

## Revised status

```json
{
  "PATCH_SET_05": "PARTIAL_PASS",
  "completed": ["PATCH_05A", "PATCH_05B", "PATCH_05C", "PATCH_05D"],
  "runtime_01A": "FAIL",
  "current_failure_location": "input box selector resolution",
  "STATE_16": "NOT_CONFIRMED",
  "next_patch_set": "PATCH_SET_06"
}
```

---

# PATCH_SET_06 — Non-blocking composer selector resolution

## Purpose

Fix the current hang by making `_input_box()` fail or resolve quickly instead of spending the full browser action timeout on missing textarea selectors.

This does **not** change model behavior, prompts, JSON parsing, retry policy, or workflow outputs.

---

## PATCH_06A — Add selector timeout control

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_06A",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "20"))
```

### REPLACE WITH

```python
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
BROWSER_SELECTOR_TIMEOUT_MS = int(os.getenv("BROWSER_SELECTOR_TIMEOUT_MS", "5000"))
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "20"))
```

---

## PATCH_06B — Replace blocking `_input_box()` selector loop

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_06B",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    def _input_box(self, page):
        selectors = [
            "textarea#prompt-textarea",
            "textarea[data-testid='prompt-textarea']",
            "[contenteditable='true']",
        ]
        last_exc: Optional[Exception] = None
        for sel in selectors:
            try:
                box = page.locator(sel).first
                box.wait_for(timeout=self.action_timeout_ms)
                if box.is_visible():
                    return box
            except Exception as e:
                last_exc = e
        if last_exc is not None:
            raise last_exc
        fail("SELECTOR_TIMEOUT", "Could not find ChatGPT input box.")
```

### REPLACE WITH

```python
    def _input_box(self, page):
        selectors = [
            "[contenteditable='true']",
            "textarea#prompt-textarea",
            "textarea[data-testid='prompt-textarea']",
            "div[contenteditable='true']",
            "[role='textbox']",
        ]
        last_exc: Optional[Exception] = None

        for sel in selectors:
            try:
                box = page.locator(sel).first
                if box.count() == 0:
                    continue
                box.wait_for(state="visible", timeout=BROWSER_SELECTOR_TIMEOUT_MS)
                if box.is_visible():
                    json_log(
                        level="DEBUG",
                        message="Browser input selector matched",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={"operation": "input_selector_matched", "selector": sel},
                    )
                    return box
            except Exception as e:
                last_exc = e
                json_log(
                    level="DEBUG",
                    message="Browser input selector skipped",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "input_selector_skipped",
                        "selector": sel,
                        "error": str(e)[:300],
                    },
                )

        fail(
            "SELECTOR_TIMEOUT",
            "Could not find ChatGPT input box.",
            field="browser_input_box",
            expected="visible contenteditable or textarea composer",
            actual=f"url={getattr(page, 'url', '')}; last_error={last_exc}",
            stage="PROCESSING",
        )
```

---

# PATCH_SET_06 validation checkpoint

```json
{
  "patch_set_id": "PATCH_SET_06",
  "expected_behavior": "Composer detection checks visible contenteditable first and uses a short selector timeout so missing textarea selectors cannot stall the workflow.",
  "expected_present": {
    "BROWSER_SELECTOR_TIMEOUT_MS": true,
    "Browser input selector matched": true,
    "Browser input selector skipped": true,
    "field=\"browser_input_box\"": true
  },
  "expected_terminal_success_fields": [
    "timestamp",
    "level",
    "status",
    "trace_id",
    "span_id",
    "output_hash"
  ],
  "forbidden_changes": [
    "Do not modify prompts.md",
    "Do not change output schemas",
    "Do not change image context router behavior",
    "Do not change image step numbering",
    "Do not change JSON retry policy",
    "Do not remove fail-fast behavior"
  ]
}
```

---

# Validation commands

## 1. Compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

## 2. Focused selector test

Run with short selector timeout:

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_SELECTOR_TIMEOUT_MS="3000"
$env:BROWSER_RESPONSE_STABILIZE_SECONDS="20"
$env:BROWSER_RESPONSE_STABLE_REQUIRED="2"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

Expected acceptable outcomes:

```json
{
  "acceptable_outcomes": [
    "Browser input selector matched",
    "Browser input box resolved",
    "Browser prompt submission attempted",
    "Then either 01A completes or fails fast with structured diagnostics",
    "No hang after Browser prompt send started"
  ],
  "unacceptable_outcomes": [
    "timeout after Browser prompt send started",
    "no Browser input selector matched/skipped diagnostics",
    "orphaned Python process",
    "partial state mutation without terminal event"
  ]
}
```

## Decision

Apply `PATCH_SET_06` before any further runtime validation. The current blocker is no longer response stabilization; it is composer selector resolution.