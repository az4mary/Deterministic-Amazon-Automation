# Codex_Tech Instructions

Source response file: `Codex_Tech_response.md`
Source checkpoint: `2026-05-18T17:15:34-05:00`

## Current State

STEP B-4 passed.

No-file send path works.

Submit failure is attachment-state-specific.

Codex_Tech provided the next action: test a small fresh `.txt` file instead of `Codex_Tech_Progress.md`.

## Ready To Execute Steps

**STEP B-5 - Small fresh txt attachment test**

Test a small fresh `.txt` file instead of `Codex_Tech_Progress.md`.

Procedure:

- Select the exact Codex_Tech tab.
- Clear the composer.
- Ensure there are zero existing attachments in the composer.
- Create a small fresh `.txt` diagnostic file.
- Attach exactly one file using the validated attachment path.
- Confirm upload from composer-scoped signals:
  - composer attachment count == `1`
  - `Remove file 1:` signal is present for the `.txt` file
  - uploading=false
  - pending=false
  - error=false
  - progress=false
- Type a short diagnostic prompt using real keyboard input into `DIV#prompt-textarea`.
- Check whether the send path becomes available.
- Submit only if the send path becomes available.
- Confirm the user message appears in the transcript.
- Detect any new assistant response after submission.

If the small fresh `.txt` attachment succeeds, extract the messenger response before processing the next action.

If the small fresh `.txt` attachment does not expose a submit path, report that failure to Codex_Tech and ask whether any additional files/logs are needed.
