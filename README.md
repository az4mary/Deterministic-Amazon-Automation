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
## INPUT_OUTPUT
Machine-readable contracts are the right fit here: JSON Schema defines the structure and validation of JSON data, and OpenAPI documents the expected inputs/outputs as a contract that machines can parse.
```json
{
  "input": {
    "format": "json",
    "schema": "workflow_state.json (schema-compliant pipeline state)",
    "source": "local filesystem",
    "path": "C:\\Users\\HP\\PROJECTS\\Automate_product_image_generation\\workflow_state\\workflow_state.json"
  },
  "output": {
    "format": "json",
    "schema": "validated pipeline state with appended PROMPT output",
    "destination": "local filesystem",
    "path": "C:\\Users\\HP\\PROJECTS\\Automate_product_image_generation\\workflow_state\\workflow_state.json"
  },
  "version": "1.0"
}
```
## ALGORITHM
A deterministic algorithm is an explicit sequence of states and transitions with defined inputs and outputs. ([Wikipedia][1])
```json
{
  "steps": [
    {
      "step_id": "S1",
      "input": "source product images and unstructured product data",
      "operation": "ingest and normalize input artifacts",
      "output": "validated raw input bundle",
      "next_step": "S2",
      "pipeline_stage": "INGESTION",
      "preconditions": [
        "source files exist",
        "input paths are explicit",
        "raw inputs are non-empty"
      ]
    },
    {
      "step_id": "S2",
      "input": "validated raw input bundle",
      "operation": "extract structured product dataset from text-based inputs",
      "output": "dataset JSON",
      "next_step": "S3",
      "pipeline_stage": "EXTRACTION",
      "preconditions": [
        "text inputs available",
        "schema contract loaded"
      ]
    },
    {
      "step_id": "S3",
      "input": "validated raw input bundle",
      "operation": "extract visual identity and geometry from product images",
      "output": "visual grounding JSON",
      "next_step": "S4",
      "pipeline_stage": "EXTRACTION",
      "preconditions": [
        "product images available",
        "image schema contract loaded"
      ]
    },
    {
      "step_id": "S4",
      "input": "dataset JSON and visual grounding JSON",
      "operation": "merge extracted artifacts into workflow_state.json",
      "output": "schema-compliant workflow_state.json",
      "next_step": "S5",
      "pipeline_stage": "TRANSFORMATION",
      "preconditions": [
        "both extraction outputs valid",
        "merge rules defined"
      ]
    },
    {
      "step_id": "S5",
      "input": "schema-compliant workflow_state.json",
      "operation": "validate state completeness and hand off for downstream prompt stages",
      "output": "ready state for PROMPT 2 onward",
      "next_step": "END",
      "pipeline_stage": "VALIDATION",
      "preconditions": [
        "required core fields present",
        "JSON schema passes"
      ]
    }
  ]
}
```

`CONFIRMATION REQUIRED: YES`

Reply with **CONFIRM STATE 06** to continue.

[1]: https://en.wikipedia.org/wiki/Finite-state_machine?utm_source=chatgpt.com "Finite-state machine"


```json

```
