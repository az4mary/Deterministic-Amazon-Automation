# WORKFLOW_RULES

1. Always check this file for new rules as it will be updated constantly.
2. Always setup `heartbeat` with required automation settings for each WAIT time.
3. WAIT Time between messenger last response and new input PROMPT - atleast 5 minutes. Use the time when your Python script saved the messenger response as the local checkpoint.
4. Always use python script to extract messenger response and add to `chatGPT_messenger_response.md` file so not to crowd the [`INSTRUCTIONS.md`](http://INSTRUCTIONS.md)  and immediately push `chatGPT_messenger_response.md`to origin.
5. Read the current `chatGPT_messenger_response.md`  map and write them into the [`INSTRUCTIONS.md`](http://INSTRUCTIONS.md) file with sequence of next STEP(s) and immediately push [`INSTRUCTIONS.md`](http://INSTRUCTIONS.md)to origin. Ensure they are clearly labelled ready to execute STEPS for each sub-patch (eg. PATCH_12J1, PATCH_12J2 etc are separate - dry-run + apply + commit + push to origin), sub-validation (e.g. Validation 1, Validation 2 etc are separate), Clean-up etc must be individual STEPS. 
6. STEPS should be labelled in this format - **STEP 1 -** **PATCH_12J1 - Allow Flow adapter to receive a shared browser adapter**
7. Update the `PATCH_SET_12_Progress.md` file after each STEP as-is, no polish, no fix, push to origin, attached file to the CHAT in the current tab, allow time for file upload and prompt the messenger to confirm that you can proceed to the next STEP. Specify that messenger should just reply "xx is confirmed proceed with yy".
8. All and every single STEPS in the [`INSTRUCTIONS.md`](http://INSTRUCTIONS.md)MUST be completed otherwise the next `PATCH_SET` or Task will be blocked.
9. If there is a failure, immediately BLOCK proceed or edit to future STEPS (explicit in your report) then report directly to the messenger and attach necessary artifacts/logs needed to troubleshoot and specifically ask messenger for any questions or additional files  - don't recommend any fix - all recommendations must come from the messenger.
10. If messenger wants to fix a STEP, then there next STEP has to be blocked until the current STEP has been confirmed - no changes can be made to future STEPS, focus has to only be on the current STEP to unblock the next STEP.
11. Always ask the messenger to provide the necessary clean-up before the beginning of a new `PATCH_SET`or whenever you feel current artifacts may pollute next STEPS. Don't cleanup without confirmation from the messenger in case of there needs to be troubleshooting.
12. Setup at least 10 minutes WAIT time and resume wherever you stopped if your sandbox is timed out or interrupted due to local PC technical/network issues during a workflow - I don't know if this is feasible or not.
13. Coming soon
14. Coming soon