# INSTRUCTIONS_3

The runtime failure moved backward again, but the report is useful: `_input_box()` is now too eager. It checks once, sees no matching composer at that instant, and fails before the ChatGPT composer finishes becoming available.

- Reclassified `PATCH_SET_07` as **static/helper pass, runtime not yet validated**.
- Confirmed the new runtime blocker is composer readiness timing, not the final-content gate itself.

## Current diagnosis

`PATCH_07A–07C` applied correctly:

```json
{
  "PATCH_07A": "PASS",
  "PATCH_07B": "PASS",
  "PATCH_07C": "PASS",
  "helper_test": "PASS",
  "runtime_gate_reached": false
}
```

The focused runtime failed before the final-content gate:

```
SELECTOR_TIMEOUT
field: browser_input_box
actual: url=https://chatgpt.com/; last_error=None
```

Logs reached only:

```
Browser text execution started
Browser page ready
Browser payload built
Browser JSON attempt started
Browser prompt send started
```

The browser probe then showed the composer **did exist** after failure:

```
contenteditables=1
visibleContenteditables=1
roleTextboxes=1
visibleRoleTextboxes=1
loginLinks=0
```

So `_input_box()` is failing too early. It performs a single selector pass; when selector count is `0`, it silently continues and can fail before the ChatGPT composer becomes ready.

`workflow_state.json` correctly still has empty `outputs`, so no false step completion was persisted.

---

# Revised status

```json
{
  "PATCH_SET_07": "PARTIAL_PASS",
  "static_helpers": "PASS",
  "runtime_validation": "BLOCKED_BEFORE_FINAL_CONTENT_GATE",
  "current_failure_location": "composer readiness timing",
  "STATE_16": "NOT_CONFIRMED",
  "next_patch_set": "PATCH_SET_08"
}
```

Do **not** roll back `PATCH_SET_07`. Keep it. The final-content gate is still needed once the composer path is stable.

---

# PATCH_SET_08 — Composer readiness wait loop

## Purpose

Make `_input_box()` wait/poll for the ChatGPT composer to become available instead of checking selectors once and failing immediately.

This patch does **not** change:

- prompts
- schemas
- JSON retry policy
- final-content gate
- image context routing
- output persistence
- fail-fast behavior

---

## PATCH_08A — Add composer readiness controls

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_08A",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
BROWSER_SELECTOR_TIMEOUT_MS = int(os.getenv("BROWSER_SELECTOR_TIMEOUT_MS", "5000"))
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "60"))
BROWSER_REQUIRE_JSON_CANDIDATE = os.getenv("BROWSER_REQUIRE_JSON_CANDIDATE", "1") == "1"
```

### REPLACE WITH

```python
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
BROWSER_SELECTOR_TIMEOUT_MS = int(os.getenv("BROWSER_SELECTOR_TIMEOUT_MS", "5000"))
BROWSER_COMPOSER_READY_TIMEOUT_MS = int(os.getenv("BROWSER_COMPOSER_READY_TIMEOUT_MS", "30000"))
BROWSER_SELECTOR_POLL_MS = int(os.getenv("BROWSER_SELECTOR_POLL_MS", "500"))
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "60"))
BROWSER_REQUIRE_JSON_CANDIDATE = os.getenv("BROWSER_REQUIRE_JSON_CANDIDATE", "1") == "1"
```

---

## PATCH_08B — Replace single-pass `_input_box()` with readiness polling

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_08B",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

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

### REPLACE WITH

```python
    def _input_box(self, page):
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
        last_exc: Optional[Exception] = None
        deadline = time.time() + (BROWSER_COMPOSER_READY_TIMEOUT_MS / 1000.0)
        last_wait_log = 0.0

        json_log(
            level="DEBUG",
            message="Browser input composer wait started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "input_composer_wait_start",
                "url": getattr(page, "url", ""),
                "timeout_ms": BROWSER_COMPOSER_READY_TIMEOUT_MS,
            },
        )

        while time.time() < deadline:
            saw_candidate = False

            for sel in selectors:
                try:
                    box = page.locator(sel).first
                    count = box.count()
                    if count == 0:
                        continue

                    saw_candidate = True
                    remaining_ms = max(250, int((deadline - time.time()) * 1000))
                    wait_ms = min(BROWSER_SELECTOR_TIMEOUT_MS, remaining_ms)

                    box.wait_for(state="visible", timeout=wait_ms)
                    if box.is_visible():
                        json_log(
                            level="DEBUG",
                            message="Browser input selector matched",
                            stage="PROCESSING",
                            status="IN_PROGRESS",
                            context={
                                "operation": "input_selector_matched",
                                "selector": sel,
                                "url": getattr(page, "url", ""),
                            },
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

            now = time.time()
            if now - last_wait_log >= 2.0:
                last_wait_log = now
                json_log(
                    level="DEBUG",
                    message="Browser input composer wait continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "input_composer_wait_continue",
                        "url": getattr(page, "url", ""),
                        "saw_candidate": saw_candidate,
                    },
                )

            page.wait_for_timeout(BROWSER_SELECTOR_POLL_MS)

        fail(
            "SELECTOR_TIMEOUT",
            "Could not find ChatGPT input box.",
            field="browser_input_box",
            expected="visible contenteditable, role textbox, or textarea composer before composer readiness timeout",
            actual=f"url={getattr(page, 'url', '')}; last_error={last_exc}",
            stage="PROCESSING",
        )
```

---

# PATCH_SET_08 validation checkpoint

```json
{
  "patch_set_id": "PATCH_SET_08",
  "expected_behavior": "Composer detection waits for ChatGPT's composer to become visible before failing, and emits wait diagnostics if the composer is not immediately available.",
  "expected_present": {
    "BROWSER_COMPOSER_READY_TIMEOUT_MS": true,
    "BROWSER_SELECTOR_POLL_MS": true,
    "Browser input composer wait started": true,
    "Browser input composer wait continuing": true,
    "Browser input selector matched": true
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
    "Do not remove PATCH_SET_07 final-content gate",
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

## 2. Static marker validation

```powershell
D:\TOOLS\Python314\python.exe - <<'PY'
from pathlib import Path

text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")

required = [
    "BROWSER_COMPOSER_READY_TIMEOUT_MS",
    "BROWSER_SELECTOR_POLL_MS",
    "Browser input composer wait started",
    "Browser input composer wait continuing",
    "Browser input selector matched",
    "assistant_response_ready(current)",
]

for marker in required:
    assert marker in text, marker

print("PATCH_SET_08_STATIC_VALIDATION_OK")
PY
```

## 3. Focused runtime test

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_SELECTOR_TIMEOUT_MS="3000"
$env:BROWSER_COMPOSER_READY_TIMEOUT_MS="30000"
$env:BROWSER_SELECTOR_POLL_MS="500"
$env:BROWSER_RESPONSE_STABILIZE_SECONDS="60"
$env:BROWSER_RESPONSE_STABLE_REQUIRED="2"
$env:BROWSER_REQUIRE_JSON_CANDIDATE="1"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

Acceptable outcomes:

```json
{
  "acceptable_outcomes": [
    "Browser input composer wait started appears",
    "Browser input selector matched appears",
    "Browser input box resolved appears",
    "Browser prompt submission attempted appears",
    "If Thinking appears, Browser assistant response not ready appears",
    "Browser response received appears with final JSON-like content",
    "Then either 01A completes or fails fast on final malformed JSON",
    "No SELECTOR_TIMEOUT when browser probe shows visible composer",
    "No orphaned Python process"
  ],
  "unacceptable_outcomes": [
    "SELECTOR_TIMEOUT while probe shows visible composer",
    "timeout after Browser prompt send started",
    "actual: Thinking",
    "orphaned Python process",
    "partial completed state without prompt_01A"
  ]
}
```

## Decision

Apply `PATCH_SET_08` next. After it passes, rerun the same focused `--stop-after 01A` test.