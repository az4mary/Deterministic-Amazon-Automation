# WORKFLOW_RULES

## PART 1 - Mandatory Messenger Workflow Rules

1. These rules apply to any task assigned to Codex that involves interacting with a messenger, including Codex_Tech, PROMPTS_GEN, or any future ChatGPT messenger used as a workflow partner. They do not automatically apply to ordinary repo work that does not involve messenger interaction, and they do not override higher-priority platform, system, safety, or developer instructions. Always read this file before starting or resuming messenger workflow work. Treat this file as the live operating rule source.

2. Do not create automation-based waits for messenger workflow pauses. Waits are tracked by local time.

3. Before sending a new messenger prompt, wait at least 5 minutes from the local time when the last messenger response was detected or extracted. Record the local checkpoint time using PowerShell `Get-Date -Format o`, including fractional seconds and UTC offset, for example `2026-05-19T00:42:30.9338090-05:00`. In `Codex_Tech_Progress.md`, place it under the current step heading as:

```md
Local checkpoint time:
- `2026-05-19T00:42:30.9338090-05:00`
```

In `Codex_Tech_response.md`, place it in the checkpoint title and repeat it in the metadata block as:

```md
# Codex_Tech Messenger Checkpoint - 2026-05-19T00:41:43.7506145-05:00

- Source URL: https://chatgpt.com/c/...
- Page title: ...
- Local checkpoint time: `2026-05-19T00:41:43.7506145-05:00`
- Response detection: latest assistant response detected and stable
```

4. Messenger response handling order is mandatory:
    - Detect any new assistant response after the submitted prompt.
    - Do not wait only for a predicted PASS or FAIL phrase.
    - Extract the full new assistant response into the active messenger response file first, such as `Codex_Tech_response.md`.
    - The active messenger response file must contain only the extracted messenger response/checkpoint fields and the format requested by the messenger. Do not add unrelated local command output, browser helper notes, speculation, diagnostics, or extra activity unless the messenger explicitly requested those fields.
    - For future messengers, use `<MessengerName>_response.md` unless the user specifies a different active response file.
    - Immediately commit the response file with a task-specific commit title/message, then push it to `origin codex_branch`.
    - Only after that push, process the response into the active instruction or progress file.

Each reasonable update to each messenger workflow file must be committed and pushed separately for tracking. For now, `codex_branch` is the only available branch for this workflow. A commit title/message is the Git commit message, not a required markdown heading inside the file. Use task-specific commit messages that clearly identify the file role and step, such as `Extract Codex_Tech STEP B response`, `Translate Codex_Tech STEP B instructions`, or `Record Codex_Tech STEP B progress`.

5. Do not analyze, summarize, classify, recommend fixes, choose cleanup, or decide the next action before the messenger response has been extracted into the response file and pushed. All analysis must come after extraction.

6. Translate the extracted messenger response into the active instruction file only when it creates real executable next steps. For this messenger, use `Codex_Tech_INSTRUCTIONS.md`. For future messengers, use `<MessengerName>_INSTRUCTIONS.md` unless the user specifies a different active instruction file. Immediately commit the instruction file with a task-specific commit title/message, then push it after editing it.

7. Write executable steps clearly and separately. Each patch, validation, cleanup, diagnostic, and follow-up must be its own STEP. Use this label style: `STEP 1 - PATCH_12J1 - Allow Flow adapter to receive a shared browser adapter`.

8. Update the active progress file after each STEP or diagnostic. For this messenger, use `Codex_Tech_Progress.md`. For future messengers, use `<MessengerName>_Progress.md` unless the user specifies a different active progress file. The active `<MessengerName>_Progress.md` file must contain only what the messenger explicitly requested, in the same format the messenger requested. Do not copy STEP instructions, procedure details, expected criteria, command blocks, or other duplicated content from `<MessengerName>_INSTRUCTIONS.md` into `<MessengerName>_Progress.md`; the messenger already has the STEP details, so report only the result or requested diagnostic fields. Do not add unrelated local command output, browser helper notes, local browser notes, speculation, diagnostics, or extra local activity that may confuse the messenger unless the messenger explicitly requested those fields. Immediately commit the progress file with a task-specific commit title/message, then push it after editing it.

9. Composer prompts to the messenger must be short, normally 1 or 2 lines. Put requested diagnostic details in the progress file, attach the progress file, allow upload to complete, then ask the messenger to review the attached progress file and confirm the next action.

10. If the messenger asks for a specific response format, follow that exact format. If the messenger asks for diagnostic fields, provide only those fields unless the messenger asks for more.

11. Every STEP in the instruction file must be completed and confirmed before the next workflow task or patch set can proceed. If a step is not confirmed, the next step is blocked.

12. If a failure, mismatch, timeout, missing confirmation, or troubleshooting request occurs, immediately state `NEXT STEP BLOCKED` and `No future-step edits/proceeding` in the report/progress file. Do not edit future steps. Focus only on the current blocked step.

13. When blocked or failed, report to the messenger with the requested artifacts/logs only, and explicitly ask: `Do you need any additional files/logs for troubleshooting?`

14. Do not recommend fixes, cleanup, next diagnostics, or future edits yourself. Recommendations, cleanup instructions, and next diagnostic actions must come from the messenger after the extracted response is processed.

15. Do not cleanup temporary files, generated artifacts, caches, logs, screenshots, or troubleshooting evidence unless the messenger or user confirms cleanup. For messenger workflows, preservation wins over generic cleanup rules until cleanup is explicitly confirmed. If the user explicitly requests cleanup, clean only the confirmed artifacts and leave unrelated dirty worktree entries untouched. Ask the messenger for cleanup instructions before a new patch set or whenever artifacts may affect later steps.

16. If local PC, browser, network, or sandbox interruption stops a workflow, resume from the last local checkpoint. Record the interruption and local resume time in the appropriate response/progress file before continuing. If a local tool, browser, sandbox, filesystem, or environment issue blocks the assigned task and is not part of the current messenger troubleshooting task, report it directly to the user. If the issue is part of the current messenger task, record it in the active progress file using the blocked-state rules and ask the messenger whether additional files or logs are needed.

## PART 2 - Messenger Interaction Best Practices

These practices are learned from the Codex_Tech messenger task and should guide future messenger work. They do not replace PART 1. If there is any conflict, PART 1 controls.

1. Treat the browser as an unreliable observation surface until each state is confirmed from the active target. A visible browser reply is not enough by itself; confirm the selected ChatGPT tab URL, page title, transcript state, composer state, and latest message state from the same active page object.

2. Prefer exact active-tab selection over convenience. Before reading, attaching, typing, or submitting, list the available ChatGPT targets and bind the automation to the intended conversation URL or the intended new temporary conversation. Avoid acting on the first ChatGPT tab when multiple tabs exist.

3. Keep test conversations separate from production messenger conversations. Use a temporary new ChatGPT conversation for isolation tests, and only migrate to a new dedicated messenger conversation when the messenger or user confirms that the old target conversation is likely the issue.

4. Confirm attachments from composer-scoped signals, not page-wide text. The strongest confirmation is the active composer form showing the expected `Remove file N: <filename>` controls, stable attachment count, no active upload indicators, no pending state, no error alerts, and no real progress bars. Do not treat the word `Progress` inside a filename as an upload progress signal.

5. Expect ChatGPT to rename repeated uploads. A displayed name like `Codex_Tech_Progress(5).md` can still represent the correct local file. Record the displayed upload name when relevant, but keep local workflow references pointed at the real active file name.

6. Before typing into a new or reused composer, verify the composer is empty and has zero unintended attachments. If a draft exists, clear it and re-check the composer text, attachment count, and send-button state before attaching or typing.

7. Use short messenger prompts in the composer. Put diagnostic detail, logs, and step reports in the active progress file. The composer prompt should normally ask the messenger to review the attached file and confirm the next concrete action.

8. Type and submit carefully. Multiline prompts can be split into multiple user turns if Enter is interpreted as send. Prefer a short one-line or two-line prompt. If multiline text is required, verify the full prompt remains in one composer draft before submitting.

9. Scope send-button detection to the active composer form. Page-wide button searches can click sidebar or history controls. Use the send control nearest the active composer, and confirm submission only when a new user message appears in the transcript.

10. Do not classify a step as PASS only because the expected phrase appears somewhere on the page. Confirm it appears in a new assistant transcript message after the submitted user message, then extract that assistant message into the response file before any analysis.

11. Wait for any new assistant response, not only an expected PASS or FAIL phrase. The messenger may ask for more diagnostics, correct the procedure, or provide a conditional next action. Extract the full response first and process it afterward.

12. Use fallback transcript extraction whenever the primary wait misses a visible reply. A primary wait timeout is an observation failure until a scoped transcript check proves there is no new assistant message.

13. Keep blocked reports minimal and exact. If a step fails or cannot be confirmed, write the requested fields only, include `NEXT STEP BLOCKED`, include `No future-step edits/proceeding`, and ask whether additional files or logs are needed.

14. Do not mix local helper details into messenger-facing files unless explicitly requested. Browser scripts, internal command choices, and local troubleshooting notes can confuse the messenger when it asked only for diagnostic fields or a PASS/FAIL result.

15. Preserve evidence until cleanup is confirmed. Temporary diagnostic files, screenshots, logs, and generated artifacts may be needed later; do not delete them just because the immediate step passed.

## PART 3 - Usable Messenger Scripts And Commands

These command and script patterns are approved helpers for messenger workflow work. Adapt the messenger name, paths, URL, step label, and prompt text to the active workflow. Do not paste helper output into messenger-facing files unless the messenger explicitly requests it.

This section exists to prevent the repeated workflow failures seen during PATCH_12O and PATCH_12P: progress entries inserted into old duplicate sections, stalled ChatGPT upload tiles, disabled send buttons, old assistant replies being mistaken for new confirmations, and unrelated generated files being staged.

### Standard Variables

Set these at the start of a messenger work session and adapt only the values that change:

```powershell
$Repo = 'D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch'
$MessengerName = 'PROMPTS_GEN'
$MessengerUrl = 'https://chatgpt.com/c/69b16c98-11c4-8328-8582-145ea2e5affa'
$ProgressFile = Join-Path $Repo "$MessengerName`_Progress.md"
$ResponseFile = Join-Path $Repo "$MessengerName`_response.md"
$InstructionsFile = Join-Path $Repo "$MessengerName`_INSTRUCTIONS.md"
Set-Location -LiteralPath $Repo
```

### Local Time, Waits, And Git

Capture local checkpoint time with fractional seconds and UTC offset:

```powershell
Get-Date -Format o
```

Wait at least 5 minutes from the last extracted messenger response checkpoint before sending a new messenger prompt:

```powershell
$target = Get-Date '2026-05-23T15:40:52.1468918-05:00'
$now = Get-Date
if ($now -lt $target) {
  $seconds = [int][Math]::Ceiling(($target - $now).TotalSeconds)
  Start-Sleep -Seconds $seconds
}
Get-Date -Format o
```

Inspect only relevant workflow files and leave unrelated generated files alone:

```powershell
git status -sb
git diff -- $ProgressFile $ResponseFile $InstructionsFile WORKFLOW_RULES.md
```

Stage and push only the file that was just updated:

```powershell
git add -- $ProgressFile
git commit -m 'Record PROMPTS_GEN STEP 5 validation'
git push origin codex_branch
```

```powershell
git add -- $ResponseFile
git commit -m 'Extract PROMPTS_GEN STEP 5 response'
git push origin codex_branch
```

Do not use `git add .` in messenger workflows.

### Append-To-Bottom Progress Updates

Always append progress to the bottom of the active progress file. Do not patch by matching an old step heading, because repeated step names can place the report in the wrong block.

Use this pattern for progress entries:

````powershell
$block = @"
## STEP 5 - P-Validation 2: static marker check

```text
PATCH_12P_SUBMIT_CAPTURE_STATIC_OK
```
"@
Add-Content -LiteralPath $ProgressFile -Value "`r`n$block"
Get-Content -LiteralPath $ProgressFile -Tail 60
````

Use full step names exactly as the messenger/instructions provide them. Prefer:

```md
## STEP 5 - PATCH_12O5: replace Flow `execute_image(...)` ordering
```

Do not shorten to:

```md
## STEP 5 - PATCH_12O5
```

After every progress edit, verify the true bottom of the file:

```powershell
Get-Content -LiteralPath $ProgressFile -Tail 60
```

If an entry lands anywhere except the bottom, append the corrected block to the bottom immediately. Do not delete evidence unless the user or messenger explicitly confirms cleanup.

### Response Extraction Template

After a new assistant response appears, append only the checkpoint fields and extracted response to the active response file:

```powershell
$checkpoint = Get-Date -Format o
$responseText = @"
STEP 5 - P-Validation 2: static marker check is confirmed.

Next action:

Proceed with STEP 6 - P-Validation 3: method sanity.
"@
$block = @"
---

# PROMPTS_GEN Messenger Checkpoint - $checkpoint

- Source URL: $MessengerUrl
- Page title: PROMPTS_GEN
- Local checkpoint time: ``$checkpoint``
- Response detection: latest assistant response detected and stable

## Extracted response

$responseText
"@
Add-Content -LiteralPath $ResponseFile -Value "`r`n$block"
Get-Content -LiteralPath $ResponseFile -Tail 40
```

Commit and push the response file before analyzing or acting on the response.

### Remote Browser Checks

Before browser work, confirm the remote-debugging endpoint and the intended ChatGPT tab:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/version' -TimeoutSec 5 | ConvertTo-Json -Depth 4
Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/list' -TimeoutSec 5 | ConvertTo-Json -Depth 4
```

Bind automation to the tab whose URL matches `$MessengerUrl`. Do not act on the first ChatGPT tab by convenience.

### Preferred Send-With-Attachment Helper

Use Playwright over the existing Chrome DevTools session when available. This helper clears stale attachments, clears the composer, types a short prompt, attaches the progress file, waits for a real ready state, sends, and verifies that the latest user message is the one just submitted.

Save or run this as a Python helper after setting the constants at the top:

```python
import json
import time
from playwright.sync_api import sync_playwright

URL = "https://chatgpt.com/c/69b16c98-11c4-8328-8582-145ea2e5affa"
PROGRESS = r"D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\PROMPTS_GEN_Progress.md"
PROMPT = "Please review attached PROMPTS_GEN_Progress.md and confirm STEP 5 - P-Validation 2: static marker check."
REQUIRED_USER_MARKER = "STEP 5"
COMPOSER = "#prompt-textarea, div.ProseMirror[contenteditable='true'], [contenteditable='true'][data-lexical-editor='true']"


def transcript(page):
    return page.evaluate("""() => {
      const articles = [...document.querySelectorAll('article,[data-message-author-role]')]
        .map((element, index) => ({
          index,
          role: element.getAttribute('data-message-author-role') || '',
          text: (element.innerText || '').trim(),
        }));
      const users = articles.filter((message) => message.role === 'user');
      const assistants = articles.filter((message) => message.role === 'assistant' && message.text && message.text !== 'Thinking');
      const thinking = (document.body.innerText || '').includes('Thinking') || !!document.querySelector('[aria-label*="Stop"], button[aria-label*="Stop"]');
      return { url: location.href, title: document.title, user_count: users.length, assistant_count: assistants.length, latest_user: users.at(-1) || null, latest_assistant: assistants.at(-1) || null, thinking };
    }""")


def composer_state(page):
    return page.evaluate("""() => {
      const composer = document.querySelector('#prompt-textarea, div.ProseMirror[contenteditable="true"], [contenteditable="true"][data-lexical-editor="true"]');
      const form = composer?.closest('form') || document;
      const send = form.querySelector('[data-testid="send-button"], button[aria-label*="Send" i]');
      const remove = [...form.querySelectorAll('button,[aria-label]')]
        .map((element) => element.getAttribute('aria-label') || element.innerText || '')
        .filter((text) => /^Remove file/i.test(text));
      const cursorWait = [...form.querySelectorAll('*')].filter((element) => String(element.className || '').includes('cursor-wait')).length;
      const progressBars = [...form.querySelectorAll('[role="progressbar"], progress')].length;
      const alerts = [...document.querySelectorAll('[role="alert"], [data-testid*="error" i]')].map((element) => element.innerText).filter(Boolean);
      return { composer_present: !!composer, composer_text: composer ? composer.innerText : null, attachment_count: remove.length, remove_file_signals: remove, send_present: !!send, send_disabled: send ? !!send.disabled : null, cursor_wait_count: cursorWait, progress_bars: progressBars, active_error_alerts: alerts };
    }""")


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    pages = [pg for ctx in browser.contexts for pg in ctx.pages]
    page = next((pg for pg in pages if pg.url.startswith(URL)), None)
    if page is None:
        raise RuntimeError(f"messenger tab not found: {URL}")

    page.bring_to_front()
    before = transcript(page)

    for _ in range(5):
        clicked = page.evaluate("""() => {
          const composer = document.querySelector('#prompt-textarea, div.ProseMirror[contenteditable="true"], [contenteditable="true"][data-lexical-editor="true"]');
          const form = composer?.closest('form') || document;
          const button = [...form.querySelectorAll('button')].find((item) => /^Remove file/i.test(item.getAttribute('aria-label') || item.innerText || ''));
          if (!button) return false;
          button.click();
          return true;
        }""")
        if not clicked:
            break
        page.wait_for_timeout(1000)

    composer = page.locator(COMPOSER).last
    composer.wait_for(state="visible", timeout=30000)
    composer.click(timeout=10000)
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.type(PROMPT, delay=5)

    ready = None
    for _attempt in range(3):
        page.locator("input#upload-files").set_input_files(PROGRESS)
        deadline = time.time() + 120
        while time.time() < deadline:
            ready = composer_state(page)
            if ready["attachment_count"] >= 1 and ready["send_present"] and not ready["send_disabled"] and ready["cursor_wait_count"] == 0 and ready["progress_bars"] == 0 and not ready["active_error_alerts"]:
                break
            page.wait_for_timeout(1000)
        if ready and ready["attachment_count"] >= 1 and not ready["send_disabled"] and ready["cursor_wait_count"] == 0:
            break
    else:
        raise RuntimeError("attachment/send not ready: " + json.dumps(ready, indent=2))

    page.locator("[data-testid='send-button']").last.click(timeout=30000)

    sent = None
    deadline = time.time() + 90
    while time.time() < deadline:
        sent = transcript(page)
        latest_user = sent.get("latest_user") or {}
        if sent["user_count"] > before["user_count"] and REQUIRED_USER_MARKER in latest_user.get("text", ""):
            break
        page.wait_for_timeout(1000)
    else:
        raise RuntimeError("sent user message not detected: " + json.dumps(sent, indent=2))

    print(json.dumps({"attachment": ready, "after_send": sent}, indent=2))
```

If upload stalls with a visible tile but `send_disabled` remains true, remove the stalled attachment and retry upload. Do not click send until `send_disabled` is false and `cursor_wait_count` is zero.

### Transcript Wait And Extraction Helper

After sending, wait for a new assistant response whose article index is greater than the submitted user message index. This prevents reading the previous assistant reply.

```python
import json
import time
from playwright.sync_api import sync_playwright

URL = "https://chatgpt.com/c/69b16c98-11c4-8328-8582-145ea2e5affa"
USER_MARKER = "STEP 5"
ASSISTANT_MARKER = "STEP 5"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = next(pg for ctx in browser.contexts for pg in ctx.pages if pg.url.startswith(URL))
    page.bring_to_front()

    stable_text = None
    stable_count = 0
    last = None
    deadline = time.time() + 420
    while time.time() < deadline:
        state = page.evaluate("""() => {
          const articles = [...document.querySelectorAll('article,[data-message-author-role]')]
            .map((element, index) => ({ index, role: element.getAttribute('data-message-author-role') || '', text: (element.innerText || '').trim() }));
          const users = articles.filter((message) => message.role === 'user');
          const assistants = articles.filter((message) => message.role === 'assistant' && message.text && message.text !== 'Thinking');
          const thinking = (document.body.innerText || '').includes('Thinking') || !!document.querySelector('[aria-label*="Stop"], button[aria-label*="Stop"]');
          return { url: location.href, title: document.title, user_count: users.length, assistant_count: assistants.length, latest_user: users.at(-1) || null, latest_assistant: assistants.at(-1) || null, thinking };
        }""")
        last = state
        latest_user = state.get("latest_user") or {}
        latest_assistant = state.get("latest_assistant") or {}
        user_text = latest_user.get("text") or ""
        assistant_text = latest_assistant.get("text") or ""
        user_index = latest_user.get("index", -1)
        assistant_index = latest_assistant.get("index", -1)

        if USER_MARKER in user_text and ASSISTANT_MARKER in assistant_text and assistant_index > user_index and not state["thinking"]:
            if assistant_text == stable_text:
                stable_count += 1
            else:
                stable_text = assistant_text
                stable_count = 1
            if stable_count >= 3:
                break
        else:
            stable_text = None
            stable_count = 0
        page.wait_for_timeout(2000)
    else:
        raise RuntimeError("assistant reply not stable: " + json.dumps(last, indent=2))

    print(json.dumps(last, indent=2))
```

Extract the full latest assistant response into the response file before doing any analysis or next-step work.

### Read-Only Composer Probe

Use this probe when diagnosing a stuck composer. Do not paste its output into messenger-facing files unless requested.

```javascript
(() => {
  const composer = document.querySelector('#prompt-textarea, div.ProseMirror[contenteditable="true"], [contenteditable="true"][data-lexical-editor="true"]');
  const form = composer?.closest('form') || document;
  const send = form.querySelector('[data-testid="send-button"], button[aria-label*="Send" i]');
  const remove = [...form.querySelectorAll('button,[aria-label]')]
    .map((element) => element.getAttribute('aria-label') || element.innerText || '')
    .filter((text) => /^Remove file/i.test(text));
  const cursorWait = [...form.querySelectorAll('*')]
    .filter((element) => String(element.className || '').includes('cursor-wait')).length;
  return {
    url: location.href,
    title: document.title,
    composer_present: !!composer,
    composer_text: composer ? composer.innerText : null,
    attachment_count: remove.length,
    remove_file_signals: remove,
    send_present: !!send,
    send_disabled: send ? !!send.disabled : null,
    cursor_wait_count: cursorWait,
    progress_bars: [...form.querySelectorAll('[role="progressbar"], progress')].length,
  };
})()
```

### Blocked Report Template

If the current step fails or cannot be confirmed, append only the requested diagnostic fields plus these exact blocker lines to the active progress file:

```md
NEXT STEP BLOCKED
No future-step edits/proceeding
Do you need any additional files/logs for troubleshooting?
```

Do not edit future steps while blocked.
