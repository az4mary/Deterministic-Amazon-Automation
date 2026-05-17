# SECOND MESSENGER INSTRUCTIONS

Messenger chat:

```text
https://chatgpt.com/c/6a09a61f-6f94-83ea-bdc6-47089291cea0
```

Purpose:

```text
Use this second messenger only to troubleshoot Codex browser automation, file upload, prompt submission, response detection, and ChatGPT tab/connectivity issues.
```

Do not use this file for PATCH_SET_12 implementation instructions.

Do not send `INSTRUCTIONS.md` or this file to the PATCH_SET_12 messenger unless explicitly requested.

Current issue to resolve:

```text
Codex can attach files, but sometimes submit confirmation and assistant response detection fail, or the browser navigates away from the intended ChatGPT conversation.
```

## Concrete STEPS from second messenger

## **STEP 1 -** **Select the active target ChatGPT tab**

Use the exact target chat URL first:

```text
https://chatgpt.com/c/6a09a61f-6f94-83ea-bdc6-47089291cea0
```

If that tab is not open, reuse the current ChatGPT tab and navigate it to the target URL.

Do not assume the human-visible tab is the same Page object being polled. Always list CDP pages and choose the page whose URL matches the target chat.

## **STEP 2 -** **Attach files one at a time**

Use `#upload-files` for regular files.

After each attachment, inspect only the current composer form, not the full transcript.

Treat ChatGPT-renamed files such as `PATCH_SET_12_Progress(11).md` as normal.

Upload is confirmed only when:

```text
file chip appears in the composer form
no "uploading" / "pending upload" text is present
no upload error text is present
no progress bar is present
```

## **STEP 3 -** **Enter prompt only after uploads are stable**

Type or fill the prompt after file upload stability is confirmed.

Before clicking send, verify the composer form contains:

```text
the prompt prefix
the intended attached file chip(s)
no unintended files such as INSTRUCTIONS.md
```

## **STEP 4 -** **Submit and verify from transcript, not button state**

After clicking send, confirm submission by checking the transcript for a new user message containing the prompt prefix.

If the send button click returns but no user message appears, do not assume submission succeeded.

Inspect:

```text
last visible transcript messages
composer form text
whether the prompt is still in the composer
whether upload is still pending
```

## **STEP 5 -** **Wait for messenger response with fallback extraction**

Primary wait:

```text
count assistant messages before submit
wait for assistant count to increase
poll the latest assistant message text
wait until text is non-empty and stable
```

Do not use `networkidle` as the primary response completion signal.

Do not rely on long-lived element handles; use fresh DOM queries each poll.

Fallback:

```text
if primary wait times out, inspect the transcript once
if a newer assistant reply exists, extract it and treat the timeout as an observation miss
if no newer assistant reply exists, report a real timeout/failure
```

## **STEP 6 -** **Save second messenger response**

Always save extracted second messenger replies into:

```text
SECOND_MESSENGER_RESPONSE.md
```

Do not crowd `INSTRUCTIONS.md` or `chatGPT_messenger_response.md` with second-messenger troubleshooting content.

## **STEP 7 -** **Failure handling**

If the target chat disappears or navigation switches to another conversation:

```text
stop
report the observed URL/title
do not submit into the wrong chat
```

If upload or submit cannot be confirmed:

```text
stop
report composer form text and last transcript messages
do not retry blindly
```

## Validation from second messenger

## **STEP A -** **Select the correct active ChatGPT tab**

Target URL:

```text
https://chatgpt.com/c/6a09a61f-6f94-83ea-bdc6-47089291cea0
```

PASS only if the selected automation Page object URL exactly matches the target chat URL.

If no exact tab exists, select an existing ChatGPT tab, navigate it to the target URL, and wait until the loaded URL matches.

## **STEP B -** **Attach exactly one file**

Create and attach only:

```text
SECOND_MESSENGER_VALIDATION_UPLOAD.txt
```

File contents:

```text
SECOND_MESSENGER_VALIDATION_UPLOAD_OK
```

PASS only if the composer form shows the file chip and no pending/uploading/error/progress state.

Do not attach:

```text
INSTRUCTIONS.md
SECOND_MESSENGER_INSTRUCTIONS.md
PATCH_SET_12 files
```

## **STEP C -** **Enter prompt only after upload stability**

Prompt prefix:

```text
SECOND_MESSENGER_VALIDATION_TEST
```

Exact prompt:

```text
SECOND_MESSENGER_VALIDATION_TEST

This is a validation test for browser automation. Please confirm that you received the attached file and reply with exactly:

SECOND_MESSENGER_VALIDATION_RESPONSE_OK
```

PASS only if the composer contains the prompt prefix, the intended file chip, and no unintended files.

## **STEP D -** **Submit prompt and confirm from transcript**

Before clicking send, record:

```text
assistant_message_count_before
user_message_count_before
latest_user_message_before
```

After clicking send, PASS only if a newer user message appears in the transcript and contains:

```text
SECOND_MESSENGER_VALIDATION_TEST
```

Also confirm the composer no longer contains the submitted prompt.

## **STEP E -** **Primary response wait**

Use:

```text
count assistant messages before submit
wait for assistant count to increase
poll latest assistant message text using fresh DOM queries
wait until text is non-empty and stable
```

Do not use:

```text
networkidle
long-lived element handles
button state
```

PASS if latest assistant text becomes stable and preferably contains:

```text
SECOND_MESSENGER_VALIDATION_RESPONSE_OK
```

If primary wait fails, proceed to fallback extraction.

## **STEP F -** **Fallback extraction validation**

Preferred controlled test:

```text
After STEP D submission, intentionally force the primary wait to miss by using primary_wait_timeout_ms = 1, then run fallback transcript extraction once.
```

PASS if fallback extraction finds a newer assistant reply containing:

```text
SECOND_MESSENGER_VALIDATION_RESPONSE_OK
```

Save extracted response to:

```text
SECOND_MESSENGER_RESPONSE.md
```

## **STEP G -** **Save and verify response file**

PASS only if `SECOND_MESSENGER_RESPONSE.md` exists and contains:

```text
SECOND_MESSENGER_VALIDATION_RESPONSE_OK
```

Final PASS format:

```text
SECOND_MESSENGER_VALIDATION PASSED

Target tab selected: PASS
File attached: PASS
Composer-only upload confirmation: PASS
Prompt entered after stable upload: PASS
Transcript submit confirmation: PASS
Primary response wait: PASS / intentionally missed for fallback test
Fallback transcript extraction: PASS
Response saved to SECOND_MESSENGER_RESPONSE.md: PASS
```
