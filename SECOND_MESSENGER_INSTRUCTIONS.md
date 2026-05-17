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
