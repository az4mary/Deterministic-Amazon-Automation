# Codex_Tech Instructions

Source response file: `Codex_Tech_response.md`
Source checkpoint: `2026-05-18T17:32:49-05:00`

## Current State

STEP B validation remains FAIL.

Failed signal: confirmed attachment plus prompt cannot be submitted by button or Enter; attachment submit path is blocked in this browser session.

Codex_Tech provided one next validation action.

## Ready To Execute Steps

**STEP B-7 - Reset ChatGPT tab/session state and retest attachment submit path**

Run this before resuming the first messenger workflow.

Procedure:

- Close the current Codex_Tech ChatGPT tab.
- Open a fresh ChatGPT tab directly to:

```text
https://chatgpt.com/c/6a09a61f-6f94-83ea-bdc6-47089291cea0
```

- Wait for STEP A-0 readiness conditions:
  - exact target URL selected
  - transcript present
  - composer present
  - composer visible
  - composer enabled
  - no login/auth gate
  - no active error banner
  - no active captcha/Cloudflare gate
- Clear composer.
- Attach a small fresh `.txt` file.
- Confirm attachment from composer-scoped signals:
  - attachment count `1`
  - `Remove file 1: <filename>.txt`
  - uploading=false
  - pending=false
  - error=false
  - progress=false
- Type prompt using real keyboard input.
- Test submit by:
  - enabled send button if available;
  - otherwise Enter once.
- Confirm submission only from the transcript.

PASS criteria:

`STEP B-7 PASS - fresh tab restored attachment submit path`

Then continue the original STEP B response-wait/fallback validation.

If STEP B-7 fails, report:

`STEP B-7 FAILED - attachment submit path remains blocked after fresh target tab reload`

Then stop. Do not resume the first messenger workflow.
