A **deterministic AI production pipeline** that uses **Python** as a strict manager to control **large language models** and prevent hallucinations. By anchoring the workflow in a central **JSON ledger**, the system ensures that marketing copy and technical specs for products, such as an **Amazon dash cam**, remain grounded in verified facts. The architecture also integrates with **Google Flow** and **Nano Banana Pro** to automate high-fidelity visual and video creation with consistent styling. Advanced strategies like **reverse-engineering prompts** from reference images and **batching visual strategy** are used to maintain narrative cohesion across e-commerce listings. Additionally, the technical documentation describes using **Playwright** and the **Chrome DevTools Protocol** to automate web-based AI tools that lack official APIs. This hybrid approach combines **reliable code execution** with **creative AI generation** to transform manual digital labor into a streamlined, scriptable ecosystem.

## SCRIPT_OBJECTIVE
```json
{
  "objective": "Generate a complete Amazon listing and image-workflow state from extracted product inputs and sequentially persist each downstream prompt output for later pipeline stages.",
  "script_category": "PROCESSOR",
  "pipeline_stage": "TRANSFORMATION",
  "success_criteria": "Given valid source inputs, the script produces a schema-compliant workflow_state.json containing all required prompt outputs from the pipeline stages and final artifact references without manual intervention.",
  "constraints": [
    "Single-purpose workflow processor",
    "Must operate on structured pipeline inputs only",
    "Must preserve schema compliance across saved state",
    "Must support sequential prompt-stage outputs"
  ]
}
```
