# Codex_Tech Instructions

Source transcript: `Codex_Tech_response.md`
Source checkpoint: `2026-05-17T08:48:47-05:00`

## Current Messenger State

The Codex_Tech messenger transcript contains guidance for diagnosing browser automation readiness before resuming the Codex_Tech messenger workflow.

The latest messenger request asks to review an updated `Codex_Tech_Progress.md` tracker that contains the STEP A-0 readiness probe result, classify STEP A-0 as PASS or FAIL against the prior PASS criteria, and provide the next single validation action.

The extracted transcript does not include the actual updated STEP A-0 diagnostic block from `Codex_Tech_Progress.md`. Do not classify STEP A-0 from the transcript alone.

Do not provide PATCH_SET steps yet.
Do not upload files to messenger yet.
Do not submit a prompt to messenger yet.
Do not resume the Codex_Tech messenger workflow yet.

## Ready To Execute Steps

**STEP 1 - Validation 1 - Obtain updated Codex_Tech_Progress.md diagnostic**

Read the updated `Codex_Tech_Progress.md` tracker that contains the STEP A-0 readiness probe result.

If the file is not available locally or attached in the active messenger tab, block and ask for the exact file/path or attachment. Do not infer, search broadly, or classify STEP A-0 without the diagnostic.

Expected evidence to collect from the tracker:

- selected page URL
- selected page title
- `document.readyState`
- exact target URL matched: yes/no
- `composer_present`
- `composer_visible`
- `composer_enabled`
- `transcript_present`
- `assistant_message_count`
- `user_message_count`
- `login_or_auth_gate_present`
- `conversation_not_found_present`
- `error_banner_present`
- `captcha_or_cloudflare_present`
- visible text sample
- observed CDP pages
- actions taken: exact target tab selection, navigation, bottom scroll/re-probe, reload/re-probe

Completion condition:

- The STEP A-0 diagnostic is available and can be evaluated.

Failure condition:

- The tracker is missing, inaccessible, or does not include enough STEP A-0 diagnostic fields to classify PASS/FAIL.

**STEP 2 - Validation 2 - Classify STEP A-0 readiness probe**

Classify STEP A-0 using only the diagnostic evidence from the updated tracker.

STEP A-0 PASS requires all of the following:

- current URL starts with or equals `https://chatgpt.com/c/6a09a61f-6f94-83ea-bdc6-47089291cea0`
- `composer_present: yes`
- `composer_visible: yes`
- `composer_enabled: yes`
- `login_or_auth_gate_present: no`
- `conversation_not_found_present: no`
- `error_banner_present: no`
- `captcha_or_cloudflare_present: no`

If any required PASS criterion is missing or false, classify STEP A-0 as FAIL.

Completion condition:

- STEP A-0 is explicitly classified as PASS or FAIL.

Failure condition:

- The diagnostic is ambiguous or incomplete. Block and ask messenger for the missing diagnostic fields.

**STEP 3 - Validation 3 - Provide next single validation action**

If STEP A-0 is PASS:

- Next action is to rerun the original validation from STEP B: attach exactly one validation file, confirm the upload from the composer only, submit the validation prompt, confirm the user message appears in the transcript, wait for the assistant response, and use fallback transcript extraction if the primary wait misses the reply.

If STEP A-0 is FAIL:

- Do not resume the Codex_Tech messenger workflow.
- Do not upload files.
- Do not submit prompts.
- Report the STEP A-0 failure diagnostic exactly and ask messenger for the next concrete validation action.

Completion condition:

- One next validation action is ready to send to messenger.

Failure condition:

- More than one action would be needed or the action would require a PATCH_SET. Block and ask messenger to confirm the next single validation action.

**STEP 4 - Codex_Tech Messenger - Report classification and next action**

After STEP 1 through STEP 3 are complete, update `Codex_Tech_Progress.md` as-is, push it to origin, attach the progress file to the active Codex_Tech ChatGPT messenger tab, and prompt messenger to confirm whether to proceed.

Required confirmation phrasing:

`Codex_Tech Validation 1-3 is confirmed proceed with the next validation action`

Completion condition:

- Messenger confirmation is received.

Failure condition:

- Messenger does not confirm, asks for a correction, or the wait times out. Block future steps and extract the messenger response before continuing.
