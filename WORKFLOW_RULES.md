# WORKFLOW RULES

1. Always check this file for new rules as it will be updated constantly
2. WAIT Time between messenger response and new input PROMPT - atleast 5 minutes.
3. Always use python script to extract messenger response and add to `chatGPT_messenger_response.md` file so not to crowd the [`INSTRUCTIONS.md`](http://INSTRUCTIONS.md)  and immediately push `chatGPT_messenger_response.md`to origin.
4. Read the current `chatGPT_messenger_response.md`  map and write them into the [`INSTRUCTIONS.md`](http://INSTRUCTIONS.md) file with sequence of next STEP(s) and immediately push [`INSTRUCTIONS.md`](http://INSTRUCTIONS.md)to origin. Ensure they are clearly labelled ready to execute STEPS for each sub-patch (eg. PATCH_12J1, PATCH_12J2 etc are separate - dry-run + apply + commit + push to origin), sub-validation (e.g. Validation 1, Validation 2 etc are separate), Clean-up etc must be individual STEPS. 
5. Update the `PATCH_SET_12_Progress.md` file after each STEP as-is, no polish, no fix, push to origin, attached file to the CHAT in the current tab, allow time for file upload and prompt the messenger to confirm that you can proceed to the next STEP. Specify that messenger should just reply “xx is confirmed proceed with yy”.
6. All and every single STEPS in the [`INSTRUCTIONS.md`](http://INSTRUCTIONS.md)MUST be completed otherwise the next `PATCH_SET` or Task will be blocked.
7. If messenger wants to fix a STEP, then there next STEP has to be blocked until the current STEP has been confirmed - no changes can be made to future STEPS, focus has to only be on the current STEP to unblock the next STEP.
8. Always ask the messenger to provide the necessary clean-up before the beginning of a new `PATCH_SET`or whenever you feel current artifacts may pollute next STEPS. Don’t cleanup without confirmation from the messenger in case of there needs to be troubleshooting.
9. Coming soon
10. Coming soon

I read `WORKFLOW_RULES.md` and understand the workflow as:

1. Re-read `WORKFLOW_RULES.md` before each new workflow move. `YES`
2. After any messenger response, wait at least 5 minutes before sending a new prompt to the messenger. `YES`
3. Always extract messenger replies with a Python script into `chatGPT_messenger_response.md`, not into `INSTRUCTIONS.md`. `YES and push chatGPT_messenger_response.md to origin`
4. Then read `chatGPT_messenger_response.md`, update `INSTRUCTIONS.md` with clearly labeled next STEPs, and push to origin. `YES`
5. Each Patch, Validation, and Cleanup must be its own individual STEP. `YES for clarity, each sub-validation is separate STEP`
6. After each STEP, update `PATCH_SET_12_Progress.md`, attach it to the current ChatGPT tab, wait for upload completion, then prompt the messenger to confirm whether to proceed. `YES`
7. Before a new PATCH_SET, ask the messenger whether cleanup is needed. `YES`

Questions before PATCH_12J:

1. For PATCH_12J, should I split it as:
    - STEP 1: update `INSTRUCTIONS.md` from messenger response and push `YES update the INSTRUCTIONS with all clear STEPS derived from the CHAT`
    - STEP 2: apply PATCH_12J only `PATCH_12J1 only`
    - STEP 3: commit PATCH_12J `PATCH_12J1 only`
    - STEP 4: push PATCH_12J `PATCH_12J1 only`
    - STEP 5+: validations one by one? `each sub-validation one-by-one`
2. Rule 3 says extract messenger response into `chatGPT_messenger_response.md` “and push to origin.” Do you want `chatGPT_messenger_response.md` pushed every time it is updated, or only after `INSTRUCTIONS.md` is updated too? `immediately push chatGPT_messenger_response.md to origin after every new change`