# NEXT CHAT

ACTION:

- Generated `PATCH_SET_04 — Runtime stop controls + focused 01A diagnostics`.
- Scope: `workflow_orchestrator.py` only.
- No prompt changes.
- No schema changes.
- No image-context-router changes.

The current file confirms the root issue: `--stop-after` is checked **before** `run_step(...)`, so `--stop-after 01A` exits before executing `01A`.

---

# PATCH_SET_04 — Runtime stop controls + focused 01A diagnostics

## PATCH_04A — Add explicit `-stop-before`

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04A",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    parser.add_argument("--stop-after", default=None, help="Optional step id to stop after (e.g. 10)")
```

### REPLACE WITH

```python
    parser.add_argument("--stop-after", default=None, help="Run through the matching step id, then stop before the next step (e.g. 01A, 11)")
    parser.add_argument("--stop-before", default=None, help="Stop before the matching step id without executing it (e.g. 01A, 11)")
```

---

## PATCH_04B — Reject conflicting stop controls

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04B",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    ensure_dirs()
    if not args.resume:
```

### REPLACE WITH

```python
    ensure_dirs()

    if args.stop_after and args.stop_before:
        fail(
            "INVALID_ARGS",
            "--stop-after and --stop-before cannot be used together.",
            field="stop_controls",
            expected="only one of --stop-after or --stop-before",
            actual=f"stop_after={args.stop_after}, stop_before={args.stop_before}",
        )

    if not args.resume:
```

---

## PATCH_04C — Correct `-stop-after` semantics

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04C",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    for i in range(start_from, len(plan)):
        step = plan[i]
        current_step_number = i + 1
        if args.stop_after and step.step_id == args.stop_after:
            break
        run_step(step, state)
        progress_percent = min(100, int((current_step_number / len(plan)) * 100))
        validate_progress_percent(progress_percent, current_step_number, len(plan))
        json_log(
            level="INFO",
            message=f"Completed step {step.step_id}",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"step_id": step.step_id},
            progress_percent=progress_percent,
            current_step=current_step_number,
            total_steps=len(plan),
        )
```

### REPLACE WITH

```python
    for i in range(start_from, len(plan)):
        step = plan[i]
        current_step_number = i + 1

        if args.stop_before and step.step_id == args.stop_before:
            json_log(
                level="INFO",
                message=f"Stopped before step {step.step_id}",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={"step_id": step.step_id, "control": "stop_before"},
            )
            break

        run_step(step, state)
        progress_percent = min(100, int((current_step_number / len(plan)) * 100))
        validate_progress_percent(progress_percent, current_step_number, len(plan))
        json_log(
            level="INFO",
            message=f"Completed step {step.step_id}",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"step_id": step.step_id},
            progress_percent=progress_percent,
            current_step=current_step_number,
            total_steps=len(plan),
        )

        if args.stop_after and step.step_id == args.stop_after:
            json_log(
                level="INFO",
                message=f"Stopped after step {step.step_id}",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={"step_id": step.step_id, "control": "stop_after"},
            )
            break
```

---

# Focused browser diagnostics

These patches do **not** change behavior. They only add structured logs so the next `01A` runtime failure tells us where it hung.

---

## PATCH_04D — Log browser text execution start/page readiness

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04D",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    def execute_text(self, step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        page = self._page()
```

### REPLACE WITH

```python
    def execute_text(self, step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        json_log(
            level="DEBUG",
            message="Browser text execution started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"step_id": step_id, "operation": "execute_text_start"},
        )
        page = self._page()
        json_log(
            level="DEBUG",
            message="Browser page ready",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"step_id": step_id, "operation": "browser_page_ready", "url": getattr(page, "url", "")},
        )
```

---

## PATCH_04E — Log prompt payload build

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04E",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        payload = build_text_input(state, prompt_text)

        last_response = ""
```

### REPLACE WITH

```python
        payload = build_text_input(state, prompt_text)
        json_log(
            level="DEBUG",
            message="Browser payload built",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "step_id": step_id,
                "operation": "payload_built",
                "payload_chars": len(payload),
                "context_type": state.get("context_type", "WORKFLOW_STATE_JSON"),
            },
        )

        last_response = ""
```

---

## PATCH_04F — Log JSON retry attempts

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04F",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        last_response = ""
        for attempt in range(max_retries + 1):
            response_text = self.send_prompt(page, payload if attempt == 0 else _json_only_retry_prompt(step_id, schema, last_response))
            last_response = response_text
            if not response_text:
                fail("EMPTY_MODEL_OUTPUT", f"Step {step_id} returned empty browser output.")
            parsed, err, excerpt = try_parse_response_json(response_text)
            if parsed is not None:
                return parsed
            if attempt >= max_retries:
                fail(
                    "MODEL_OUTPUT_NOT_JSON",
                    f"Model output is not valid JSON: {err}",
                    actual=excerpt[:2000],
                )
```

### REPLACE WITH

```python
        last_response = ""
        for attempt in range(max_retries + 1):
            json_log(
                level="DEBUG",
                message="Browser JSON attempt started",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "step_id": step_id,
                    "operation": "json_attempt_start",
                    "attempt": attempt,
                    "max_retries": max_retries,
                },
            )
            response_text = self.send_prompt(page, payload if attempt == 0 else _json_only_retry_prompt(step_id, schema, last_response))
            last_response = response_text
            json_log(
                level="DEBUG",
                message="Browser response received",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "step_id": step_id,
                    "operation": "browser_response_received",
                    "attempt": attempt,
                    "response_chars": len(response_text or ""),
                },
            )
            if not response_text:
                fail("EMPTY_MODEL_OUTPUT", f"Step {step_id} returned empty browser output.")
            parsed, err, excerpt = try_parse_response_json(response_text)
            if parsed is not None:
                json_log(
                    level="DEBUG",
                    message="Browser response parsed as JSON",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "step_id": step_id,
                        "operation": "json_parse_success",
                        "attempt": attempt,
                        "output_keys": list(parsed.keys()),
                    },
                )
                return parsed
            json_log(
                level="DEBUG",
                message="Browser response JSON parse failed",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "step_id": step_id,
                    "operation": "json_parse_failed",
                    "attempt": attempt,
                    "error": err,
                    "excerpt_chars": len(excerpt or ""),
                },
            )
            if attempt >= max_retries:
                fail(
                    "MODEL_OUTPUT_NOT_JSON",
                    f"Model output is not valid JSON: {err}",
                    actual=excerpt[:2000],
                )
```

---

## PATCH_04G — Log prompt-send start

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04G",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
    def send_prompt(self, page, payload: str) -> str:
        before_assistant_count = page.locator("[data-message-author-role='assistant']").count()
```

### REPLACE WITH

```python
    def send_prompt(self, page, payload: str) -> str:
        json_log(
            level="DEBUG",
            message="Browser prompt send started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"operation": "send_prompt_start", "payload_chars": len(payload)},
        )
        before_assistant_count = page.locator("[data-message-author-role='assistant']").count()
```

---

## PATCH_04H — Log input-box resolution

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04H",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        box = self._input_box(page)

        box.click()
```

### REPLACE WITH

```python
        box = self._input_box(page)
        json_log(
            level="DEBUG",
            message="Browser input box resolved",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"operation": "input_box_resolved"},
        )

        box.click()
```

---

## PATCH_04I — Log prompt submission attempt

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04I",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        # Ensure the prompt is actually submitted (some UI states require clicking send
        # or using Ctrl+Enter).
        page.keyboard.press("Enter")
```

### REPLACE WITH

```python
        # Ensure the prompt is actually submitted (some UI states require clicking send
        # or using Ctrl+Enter).
        json_log(
            level="DEBUG",
            message="Browser prompt submission attempted",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"operation": "prompt_submit_attempt"},
        )
        page.keyboard.press("Enter")
```

---

## PATCH_04J — Log assistant-response wait start

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04J",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        # Wait for a new assistant message to appear (response started).
        response_deadline = time.time() + (self.action_timeout_ms / 1000.0)
```

### REPLACE WITH

```python
        # Wait for a new assistant message to appear (response started).
        json_log(
            level="DEBUG",
            message="Browser assistant response wait started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "assistant_response_wait_start",
                "before_assistant_count": before_assistant_count,
                "before_user_count": before_user_count,
            },
        )
        response_deadline = time.time() + (self.action_timeout_ms / 1000.0)
```

---

## PATCH_04K — Log assistant response detection

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04K",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        assistant = page.locator("[data-message-author-role='assistant']").last
        assistant.wait_for(timeout=self.action_timeout_ms)
        # Wait for streaming to settle to avoid capturing partial (invalid) JSON.
```

### REPLACE WITH

```python
        assistant = page.locator("[data-message-author-role='assistant']").last
        assistant.wait_for(timeout=self.action_timeout_ms)
        json_log(
            level="DEBUG",
            message="Browser assistant response detected",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "assistant_response_detected",
                "assistant_count": page.locator("[data-message-author-role='assistant']").count(),
            },
        )
        # Wait for streaming to settle to avoid capturing partial (invalid) JSON.
```

---

## PATCH_04L — Log response stabilization success

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04L",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
                if stable_count >= stable_required:
                    return current
```

### REPLACE WITH

```python
                if stable_count >= stable_required:
                    json_log(
                        level="DEBUG",
                        message="Browser assistant response stabilized",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "assistant_response_stabilized",
                            "response_chars": len(current),
                            "stable_count": stable_count,
                        },
                    )
                    return current
```

---

## PATCH_04M — Log response stabilization timeout fallback

### DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_04M",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

### FIND

```python
        return last_text.strip()
```

### REPLACE WITH

```python
        json_log(
            level="DEBUG",
            message="Browser assistant response stabilization ended by deadline",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "assistant_response_stabilization_deadline",
                "response_chars": len(last_text or ""),
            },
        )
        return last_text.strip()
```

---

# PATCH_SET_04 VALIDATION CHECKPOINT

```json
{
  "patch_set_id": "PATCH_SET_04",
  "expected_behavior": "--stop-after executes the matching step before stopping; --stop-before preserves old pre-step stop behavior; browser execution emits focused diagnostics for 01A timeout localization.",
  "expected_present": {
    "--stop-before": true,
    "Stopped before step": true,
    "Stopped after step": true,
    "Browser text execution started": true,
    "Browser page ready": true,
    "Browser payload built": true,
    "Browser JSON attempt started": true,
    "Browser prompt send started": true,
    "Browser input box resolved": true,
    "Browser prompt submission attempted": true,
    "Browser assistant response wait started": true,
    "Browser assistant response detected": true,
    "Browser assistant response stabilized": true
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
    "Do not add retry or recovery logic",
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

## 2. Verify old behavior is now explicit

```powershell
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-before 01A
```

Expected:

```json
{
  "expected": [
    "lifecycle logs emitted",
    "no step_start for 01A",
    "terminal OUTPUT/SUCCESS emitted"
  ]
}
```

## 3. Verify corrected `-stop-after`

```powershell
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

Expected:

```json
{
  "expected": [
    "step_start for 01A appears",
    "01A either completes or fails with structured diagnostics",
    "if it times out, last DEBUG log identifies the active phase"
  ]
}
```

## Important runtime note

Your prior 3-minute outer timeout may still be too short. The script currently has:

```python
BROWSER_ACTION_TIMEOUT_MS = 120000
BROWSER_JSON_RETRIES = 2
```

That means one text step can take roughly **up to 3 browser attempts**, each with its own browser wait window. For diagnosing `01A`, either use a longer outer timeout or temporarily run:

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_ACTION_TIMEOUT_MS="120000"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

That will localize the first failure faster without changing the script.

CONFIRMATION REQUIRED:

YES