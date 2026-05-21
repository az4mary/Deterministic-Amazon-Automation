# INSTRUCTIONS

Source response: `PROMPTS_GEN_response.md`

Current messenger decision:

```text
STEP 6 - L-Validation 3 is confirmed proceed with Resume STEP 7 after PATCH_12L.
```

Scope:

```text
Flow prompt-composer discovery/activation only.
Do not change reference upload, image capture, metadata persistence, prompt docs, cooldowns, or step numbering.
```

Active steps:

```text
STEP 1 - PATCH_12L1 - Add Flow prompt surface activation helper.
STEP 2 - PATCH_12L2 - Replace _find_flow_prompt_box(...).
STEP 3 - PATCH_12L3 - Replace _fill_flow_prompt_box(...).
STEP 4 - L-Validation 1 - Compile.
STEP 5 - L-Validation 2 - Static marker check.
STEP 6 - L-Validation 3 - No-browser method sanity.
STEP 7 - Resume STEP 7 after PATCH_12L.
```

Patch payloads, dry-run expectations, validation commands, expected checks, and decision rules are in `PROMPTS_GEN_response.md`.
