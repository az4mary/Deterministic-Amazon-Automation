# NEXT CHAT

Launch the browser with remote debugging and wait for authentication before proceed.

CONFIRMATION REQUIRED:

YES

ACTION:

- Revalidated `EXECUTION_INSTRUCTIONS_RULES` after confirmed `PATCH_SET_02` and `PATCH_SET_03`.
- Confirmed runtime instructions remain explicit and valid after the image-context-router and prompt-contract changes.
- Confirmed execution modes still map cleanly to the updated payload contract:
    - normal text steps → `WORKFLOW_STATE_JSON`
    - image prompt steps → `IMAGE_CONTEXT_JSON`
    - image generation steps → context-derived `image_generation_prompt`
    - reference images → attached separately through browser/model workflow

SEARCH VALIDATION RESULT:

- Python’s `argparse` is the standard-library module for defining command-line interfaces, parsing flags, generating help/usage output, and reporting invalid arguments, which supports the script’s explicit CLI surface. ([Python documentation](https://docs.python.org/3/library/argparse.html?utm_source=chatgpt.com))
- Playwright’s Python API documents `connect_over_cdp()` as the method for attaching to an existing Chromium browser through Chrome DevTools Protocol, with the default browser context available via `browser.contexts`; this remains aligned with the browser-backed execution path. ([Playwright](https://playwright.dev/python/docs/api/class-browsertype?utm_source=chatgpt.com))

VALIDATED DECISION:

- `STATE_16_REVALIDATION = PASS`
- Execution instructions remain valid.
- No execution-command drift introduced by `PATCH_SET_02` or `PATCH_SET_03`.
- No additional rollback required.

OUTPUT:

```json
{
  "state": "16",
  "execution_instructions_validation": "PASS",
  "patch_sets_validated": [
    "PATCH_SET_02",
    "PATCH_SET_03"
  ],
  "execution_commands": [
    "python workflow_orchestrator.py --stop-after 01A",
    "python workflow_orchestrator.py --stop-after 11",
    "python workflow_orchestrator.py",
    "python workflow_orchestrator.py --resume",
    "python workflow_orchestrator.py --restart-from 11",
    "python workflow_orchestrator.py --enable-image-generation"
  ],
  "execution_modes": {
    "prompt_only_default": "Image generation steps are excluded unless --enable-image-generation is passed.",
    "browser_text_backend": "Uses Playwright CDP browser session for text/image-prompt steps.",
    "image_generation_enabled": "Uses image_generation_prompt from build_image_generation_context and separately attached reference images where supported.",
    "resume_mode": "Continues after last_completed_step from output/workflow_state.json.",
    "restart_mode": "Clears restarted step and downstream promoted outputs before re-execution."
  },
  "required_inputs": {
    "raw_product_input": [
      "data/raw_product_input.txt",
      "data/raw_product_input.md"
    ],
    "source_images": "data/images/",
    "prompts": [
      "docs/prompts/*.txt",
      "docs/prompts/*.md",
      "docs/prompts.md"
    ]
  },
  "outputs": {
    "workflow_state": "output/workflow_state.json",
    "logs": "output/logs/execution.jsonl",
    "image_prompts": "output/image_prompts.json",
    "generated_images": "output/generated_images/"
  },
  "checkpoints": [
    "INIT/STARTED lifecycle log emitted",
    "VALIDATED/COMPLETED lifecycle log emitted",
    "PROCESSING/STARTED lifecycle log emitted",
    "per-step PROCESSING/IN_PROGRESS logs emitted",
    "COMPLETED/SUCCESS lifecycle log emitted",
    "OUTPUT/SUCCESS terminal log emitted exactly once"
  ],
  "failure_contract_status": "PASS",
  "blocking_findings": []
}
```

CONFIRMATION REQUIRED:

YES