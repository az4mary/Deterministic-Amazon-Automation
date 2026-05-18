# WORKFLOW_RULES

1. Always read this file before starting or resuming messenger workflow work. Treat this file as the live operating rule source.

2. Do not create automation-based waits for messenger workflow pauses. Waits are tracked by local time.

3. Before sending a new messenger prompt, wait at least 5 minutes from the local time when the last messenger response was detected or extracted. Record the local checkpoint time in the appropriate response/progress file.

4. Messenger response handling order is mandatory:
    - Detect any new assistant response after the submitted prompt.
    - Do not wait only for a predicted PASS or FAIL phrase.
    - Extract the full new assistant response into the active messenger response file first, such as `Codex_Tech_response.md`.
    - Immediately push the response file to origin.
    - Only after that push, process the response into the active instruction or progress file.

5. Do not analyze, summarize, classify, recommend fixes, choose cleanup, or decide the next action before the messenger response has been extracted into the response file and pushed. All analysis must come after extraction.

6. Translate the extracted messenger response into the active instruction file only when it creates real executable next steps. For this messenger, use `Codex_Tech_INSTRUCTIONS.md`. Immediately push the instruction file after editing it.

7. Write executable steps clearly and separately. Each patch, validation, cleanup, diagnostic, and follow-up must be its own STEP. Use this label style: `STEP 1 - PATCH_12J1 - Allow Flow adapter to receive a shared browser adapter`.

8. Update the active progress file after each STEP or diagnostic. For this messenger, use `Codex_Tech_Progress.md`. The progress file must contain only what the messenger explicitly requested, in the same format the messenger requested. Do not add unrelated local browser notes, helper-command notes, speculation, or extra local activity that may confuse the messenger.

9. Composer prompts to the messenger must be short, normally 1 or 2 lines. Put requested diagnostic details in the progress file, attach the progress file, allow upload to complete, then ask the messenger to review the attached progress file and confirm the next action.

10. If the messenger asks for a specific response format, follow that exact format. If the messenger asks for diagnostic fields, provide only those fields unless the messenger asks for more.

11. Every STEP in the instruction file must be completed and confirmed before the next workflow task or patch set can proceed. If a step is not confirmed, the next step is blocked.

12. If a failure, mismatch, timeout, missing confirmation, or troubleshooting request occurs, immediately state `NEXT STEP BLOCKED` and `No future-step edits/proceeding` in the report/progress file. Do not edit future steps. Focus only on the current blocked step.

13. When blocked or failed, report to the messenger with the requested artifacts/logs only, and explicitly ask: `Do you need any additional files/logs for troubleshooting?`

14. Do not recommend fixes, cleanup, next diagnostics, or future edits yourself. Recommendations, cleanup instructions, and next diagnostic actions must come from the messenger after the extracted response is processed.

15. Do not cleanup temporary files, generated artifacts, caches, logs, or troubleshooting evidence unless the messenger or user confirms cleanup. Ask the messenger for cleanup instructions before a new patch set or whenever artifacts may affect later steps.

16. If local PC, browser, network, or sandbox interruption stops a workflow, resume from the last local checkpoint. Record the interruption and local resume time in the appropriate response/progress file before continuing.
