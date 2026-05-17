Validation Procedure for SECOND_MESSENGER_INSTRUCTIONS

This validates the confirmed workflow: exact target-tab selection, one-file upload, composer-only upload confirmation, transcript-based submit confirmation, primary response wait, fallback transcript extraction, and failure reporting. The target chat and required handling rules are taken from the attached instructions. 

SECOND_MESSENGER_INSTRUCTIONS

Test setup

Create a harmless one-line test file:

SECOND_MESSENGER_VALIDATION_UPLOAD.txt

Contents:

SECOND_MESSENGER_VALIDATION_UPLOAD_OK

Use this prompt prefix:

SECOND_MESSENGER_VALIDATION_TEST

Use this exact prompt:

SECOND_MESSENGER_VALIDATION_TEST

This is a validation test for browser automation. Please confirm that you received the attached file and reply with exactly:

SECOND_MESSENGER_VALIDATION_RESPONSE_OK

Do not attach:

INSTRUCTIONS.md
SECOND_MESSENGER_INSTRUCTIONS.md
PATCH_SET_12 files
Validation steps and PASS criteria
STEP A — Select the correct active ChatGPT tab
Action

List all CDP pages/tabs.

Select the page whose URL exactly matches:

https://chatgpt.com/c/6a09a61f-6f94-83ea-bdc6-47089291cea0

If no such page exists:

select an existing ChatGPT tab;

navigate it to the exact target URL;

wait until the loaded page URL matches the target URL.

PASS criteria

PASS only if the selected automation Page object has:

url == https://chatgpt.com/c/6a09a61f-6f94-83ea-bdc6-47089291cea0

and the page title/URL confirm it is the intended ChatGPT conversation.

If FAIL, report
STEP A FAILED - target ChatGPT tab not selected
Observed pages:
- URL:
- title:

Selected page URL:
Selected page title:
Action taken:
Reason stopped:

Stop. Do not submit anything.

STEP B — Attach exactly one file
Action

Use #upload-files.

Attach only:

SECOND_MESSENGER_VALIDATION_UPLOAD.txt

After upload starts, inspect only the current composer form.

PASS criteria

PASS only if the composer form shows:

file chip: SECOND_MESSENGER_VALIDATION_UPLOAD.txt

and the composer form does not show:

uploading
pending upload
upload error
progress bar
INSTRUCTIONS.md
SECOND_MESSENGER_INSTRUCTIONS.md
any PATCH_SET_12 file
If FAIL, report
STEP B FAILED - upload not confirmed from composer only
Composer form text:
Composer file chips:
Upload status text:
Progress bar present: yes/no
Upload error text:
Unintended files present:
Current page URL:

Stop. Do not submit.

STEP C — Enter prompt only after upload stability
Action

Type/fill the exact validation prompt into the composer.

Before sending, inspect only the composer form.

PASS criteria

PASS only if the composer form contains:

SECOND_MESSENGER_VALIDATION_TEST

and shows the intended file chip:

SECOND_MESSENGER_VALIDATION_UPLOAD.txt

and does not show unintended files.

If FAIL, report
STEP C FAILED - composer pre-submit validation failed
Composer form text:
Composer file chips:
Expected prompt prefix present: yes/no
Expected file chip present: yes/no
Unintended files present:
Current page URL:

Stop. Do not submit.

STEP D — Submit prompt and confirm from transcript
Action

Before clicking send, record:

assistant_message_count_before
user_message_count_before
latest_user_message_before

Click send.

Do not treat button state as confirmation.

Inspect the transcript for a new user message containing:

SECOND_MESSENGER_VALIDATION_TEST
PASS criteria

PASS only if a newer user message appears in the transcript and contains:

SECOND_MESSENGER_VALIDATION_TEST

Also confirm the composer no longer contains the submitted prompt.

If FAIL, report
STEP D FAILED - submission not confirmed from transcript
Current page URL:
Last visible transcript messages:
Composer form text:
Prompt still in composer: yes/no
Upload still pending: yes/no
assistant_message_count_before:
user_message_count_before:
user_message_count_after:

Stop. Do not retry blindly.

STEP E — Primary response wait
Action

Use the primary wait logic:

count assistant messages before submit
wait for assistant count to increase
poll latest assistant message text using fresh DOM queries
wait until text is non-empty and stable

Do not use:

networkidle
long-lived element handles
button state
PASS criteria

PASS if:

assistant_message_count_after > assistant_message_count_before

and the latest assistant message becomes non-empty and stable, preferably containing:

SECOND_MESSENGER_VALIDATION_RESPONSE_OK
If FAIL, do not immediately report failure

Proceed to STEP F fallback extraction.

STEP F — Forced fallback extraction validation

This step proves the fallback works even when the primary wait misses a visible reply.

Action

Run fallback extraction in one of these two ways:

Preferred controlled test

After STEP D submission, intentionally force the primary wait to miss by setting an unrealistically short primary timeout, for example:

primary_wait_timeout_ms = 1

Then run fallback transcript extraction once.

Acceptable natural test

If the real primary wait times out naturally, immediately run fallback extraction once.

Fallback must inspect the transcript and extract the newest assistant reply that appeared after the submitted user message.

PASS criteria

PASS if fallback extraction finds a newer assistant reply and extracts text containing:

SECOND_MESSENGER_VALIDATION_RESPONSE_OK

Then save the extracted response to:

SECOND_MESSENGER_RESPONSE.md

The validation should record:

primary_wait_status: missed intentionally / timed out
fallback_status: recovered
saved_response_path: SECOND_MESSENGER_RESPONSE.md
If FAIL, report
STEP F FAILED - fallback transcript extraction did not recover reply
Current page URL:
Last visible transcript messages:
Submitted user prompt found: yes/no
Newer assistant reply found: yes/no
Extracted fallback text:
assistant_message_count_before:
assistant_message_count_after:
primary_wait_error:

Stop.

STEP G — Save and verify response file
Action

Save the extracted second messenger response into:

SECOND_MESSENGER_RESPONSE.md

Then read the file back.

PASS criteria

PASS only if the file exists and contains:

SECOND_MESSENGER_VALIDATION_RESPONSE_OK
If FAIL, report
STEP G FAILED - response file save/readback failed
Expected path:
File exists: yes/no
File contents:
Extracted response text:
Write error:
Final validation PASS report

Only report full success if every required capability passed.

Use this format:

SECOND_MESSENGER_VALIDATION PASSED

Target tab selected: PASS
File attached: PASS
Composer-only upload confirmation: PASS
Prompt entered after stable upload: PASS
Transcript submit confirmation: PASS
Primary response wait: PASS / intentionally missed for fallback test
Fallback transcript extraction: PASS
Response saved to SECOND_MESSENGER_RESPONSE.md: PASS

Selected URL:
Uploaded file chip:
Prompt prefix:
Transcript user message found: yes
Assistant response extracted:
Fallback exercised: yes
Saved response path:
Overall FAIL rule

If any step fails, report only the failed step block using the matching failure template above, plus:

SECOND_MESSENGER_VALIDATION FAILED
Stopped before unsafe retry: yes
Submitted into wrong chat: no
