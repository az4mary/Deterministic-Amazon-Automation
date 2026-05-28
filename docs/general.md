Proceed with concrete installation STEPS using the below format. Add cleanup STEPS if needed and verify no related artifacts are present after cleanup except they are needed for future tasks.

STEPS should be in this format:

# Diagnostic_<blocked STEP #> - <TITLE>

## STEP 1 - <TITLE>
### <Actual diagnostic, test, run etc>
### <Expected results, feedback, output etc>
## CONFIRMATION REQUIRED: YES

## STEP 2 - <TITLE>
### <Actual diagnostic, test, run etc>
### <Expected results, feedback, output etc>
## CONFIRMATION REQUIRED: YES

---

# Installation_<blocked STEP #> - <TITLE>

## STEP 1 - <TITLE>
### <Actual installation, test, run etc>
### <Expected results, feedback, output etc>
## CONFIRMATION REQUIRED: YES

## STEP 2 - <TITLE>
### <Actual installation, test, run etc>
### <Expected results, feedback, output etc>
## CONFIRMATION REQUIRED: YES

# Resume <blocked STEP #>


I read `WORKFLOW_RULES.md`. I understand the workflow rules and can follow them when we resume.

Key operating constraints I’ll treat as active:

- Extract any new messenger response into the active `*_response.md` file first.
- Commit and push that response file before analyzing it or taking action.
- Wait at least 5 minutes after the last detected/extracted messenger response before sending a new messenger prompt.
- Keep messenger-facing files minimal and in the exact requested format.
- Commit and push each meaningful update separately.
- Use only `codex_branch` for this workflow.
- Do not self-direct fixes, cleanup, or future diagnostics; those come from the messenger.
- If anything blocks the current step, write `NEXT STEP BLOCKED` and `No future-step edits/proceeding`.

I do have a few questions before resuming:

1. Which messenger are we resuming with: `Codex_Tech`, `PROMPTS_GEN`, or another one?
2. What is the active ChatGPT conversation URL I should use?
3. Which current STEP are we resuming from, and has the latest messenger response already been extracted, committed, and pushed?
4. Should I inspect the repo workflow files now to determine the last checkpoint and current state, or do you want to provide that context manually?
