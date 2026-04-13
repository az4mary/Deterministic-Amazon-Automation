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
[1]: https://en.wikipedia.org/wiki/Finite-state_machine?utm_source=chatgpt.com "Finite-state machine"
## EDGE_CASES
Boundary testing is the right framing here because edge cases are the boundary or invalid inputs most likely to fail. ([Wikipedia][1])
```json
{
  "validated_edge_cases": [
    {
      "edge_case_id": "EC_001",
      "trigger_condition": "workflow_state.json is missing, unreadable, or malformed at ingestion",
      "stage": "INGESTION",
      "expected_state": "halt before any prompt execution",
      "failure_response": {
        "error_code": "INGESTION_MALFORMED_STATE",
        "message": "workflow_state.json is invalid or unavailable.",
        "termination": true
      }
    },
    {
      "edge_case_id": "EC_002",
      "trigger_condition": "source product images are missing, empty, or not loadable",
      "stage": "INGESTION",
      "expected_state": "halt before visual extraction",
      "failure_response": {
        "error_code": "INGESTION_MISSING_IMAGES",
        "message": "No valid source images were provided for visual extraction.",
        "termination": true
      }
    },
    {
      "edge_case_id": "EC_003",
      "trigger_condition": "required schema fields are absent or extra unexpected fields appear in extracted JSON",
      "stage": "VALIDATION",
      "expected_state": "halt before transformation",
      "failure_response": {
        "error_code": "VALIDATION_SCHEMA_DRIFT",
        "message": "Extracted data does not match the required schema.",
        "termination": true
      }
    },
    {
      "edge_case_id": "EC_004",
      "trigger_condition": "text extraction and image extraction disagree on the product identity or category",
      "stage": "TRANSFORMATION",
      "expected_state": "halt before downstream prompt generation",
      "failure_response": {
        "error_code": "TRANSFORMATION_IDENTITY_CONFLICT",
        "message": "Text and image sources describe conflicting product identities.",
        "termination": true
      }
    },
    {
      "edge_case_id": "EC_005",
      "trigger_condition": "product image set is empty or exceeds the supported maximum count for the image pipeline",
      "stage": "INGESTION",
      "expected_state": "halt before image prompt generation",
      "failure_response": {
        "error_code": "INGESTION_IMAGE_BOUNDARY_VIOLATION",
        "message": "Image count is outside the supported boundary.",
        "termination": true
      }
    }
  ]
}
```
[1]: https://en.wikipedia.org/wiki/Edge_case?utm_source=chatgpt.com "Edge case"
## TEST_SCENARIO
Use a **Python-orchestrated, state-file pipeline**: Python owns ingestion, schema checks, deduplication, saving `workflow_state.json`, and all deterministic transforms; LLMs only handle the few tasks that need language or visual generation. That fits TDD’s red-green-refactor discipline and pytest’s isolation model. ([martinfowler.com][1])

### Version 1 workflow
Python: ingest inputs → validate → build `workflow_state.json` → route prompts → save outputs.

LLM calls:
PROMPT 1A, 1B, 2, 3, 4, 5, 6, 7, 9, 10, 11–24.

Python-first:
PROMPT 8 can be mostly Python-generated from `workflow_state.json`; use an LLM only if a field is missing.

### State loop
`load workflow_state.json → send current prompt input → receive JSON output → validate → append to workflow_state.json → next prompt`

### Deterministic files
`images/source`, `workflow_state`, `prompts`, `outputs`, `logs`, `scripts`.

[1]: https://martinfowler.com/articles/continuousIntegration.html?utm_source=chatgpt.com "Continuous Integration"
The next deterministic step is the **Python orchestration layer**: it will load inputs, validate schema, execute each prompt call, append outputs to `workflow_state.json`, and stop immediately on any contract violation. The script should be split into `main.py`, `orchestrator.py`, `schema.py`, `state_store.py`, and `prompts/`.

Core flow:
```text
ingest → validate → prompt step → validate output → persist state → next step
```
The first implementation target should be:
1. load source images and raw text
2. run PROMPT 1A and 1B
3. build `workflow_state.json`
4. run PROMPT 2 onward in order
5. validate every JSON response before saving
### TEST_CASES
```json
[
  {
    "test_id": "T1",
    "name": "Valid raw inputs produce schema-compliant workflow state",
    "category": "VALID",
    "objective": "Validate that clean source images and unstructured product text are transformed into a complete workflow_state.json.",
    "preconditions": {
      "environment": "Windows 11, local filesystem available",
      "dependencies": ["python", "json schema validator"]
    },
    "input": {
      "data": "valid product images + valid unstructured product data",
      "schema_version": "1.0"
    },
    "steps": [
      "load source artifacts",
      "run PROMPT 1A",
      "run PROMPT 1B",
      "merge outputs into workflow_state.json"
    ],
    "expected_result": {
      "type": "SUCCESS",
      "output": "schema-compliant workflow_state.json",
      "error_code": null
    },
    "assertions": [
      "required core fields exist",
      "visual grounding fields exist",
      "JSON is valid and parseable"
    ],
    "traceability": {
      "script_id": "workflow_orchestrator_v1",
      "algorithm_step": "S1-S4",
      "edge_case_id": null
    },
    "execution": {
      "status": "PENDING",
      "actual_result": null
    },
    "version": "1.0"
  },
  {
    "test_id": "T2",
    "name": "Missing image input fails ingestion",
    "category": "INVALID",
    "objective": "Validate that the pipeline halts when no source images are provided.",
    "preconditions": {
      "environment": "Windows 11, local filesystem available",
      "dependencies": ["python"]
    },
    "input": {
      "data": "unstructured text only, no product images",
      "schema_version": "1.0"
    },
    "steps": [
      "load source artifacts",
      "validate image presence"
    ],
    "expected_result": {
      "type": "ERROR",
      "output": null,
      "error_code": "INGESTION_MISSING_IMAGES"
    },
    "assertions": [
      "pipeline halts before PROMPT 1B",
      "no workflow_state.json is saved"
    ],
    "traceability": {
      "script_id": "workflow_orchestrator_v1",
      "algorithm_step": "S1",
      "edge_case_id": "EC_002"
    },
    "execution": {
      "status": "PENDING",
      "actual_result": null
    },
    "version": "1.0"
  },
  {
    "test_id": "T3",
    "name": "Schema drift in extracted JSON fails validation",
    "category": "EDGE",
    "objective": "Validate that unexpected or missing fields in PROMPT 1 output halt the pipeline immediately.",
    "preconditions": {
      "environment": "Windows 11, local filesystem available",
      "dependencies": ["python", "json schema validator"]
    },
    "input": {
      "data": "PROMPT 1A output with extra or missing required keys",
      "schema_version": "1.0"
    },
    "steps": [
      "run PROMPT 1A",
      "validate JSON against schema"
    ],
    "expected_result": {
      "type": "ERROR",
      "output": null,
      "error_code": "VALIDATION_SCHEMA_DRIFT"
    },
    "assertions": [
      "validation fails before downstream prompts",
      "no invalid state is persisted"
    ],
    "traceability": {
      "script_id": "workflow_orchestrator_v1",
      "algorithm_step": "S2",
      "edge_case_id": "EC_003"
    },
    "execution": {
      "status": "PENDING",
      "actual_result": null
    },
    "version": "1.0"
  }
]
```
## PROJECT_ARCHITECTURE
```json
  "project_architecture": {
    "system_model": "Deterministic File Processing Pipeline (Python)",
    "pipeline_stages": [
      "INGESTION",
      "EXTRACTION",
      "TRANSFORMATION",
      "OUTPUT"
    ],
    "architecture_constraints": [
      "each stage is atomic and single-responsibility",
      "data flows linearly with no implicit branching",
      "interfaces between stages are explicitly defined",
      "full traceability from input to output is required"
    ]
  },
```
## SCRIPT_CATEGORIES
```json
  "script_categories": {
    "SCRIPT_001": {
      "script_id": "SCRIPT_001",
      "name": "extract_parser",
      "version": "4.0",
      "category": "PARSER",
      "input_schema": "markdown-like file with '# TITLE' followed by '**TASK:** text'",
      "output_schema": "clean TITLE-TASK pairs with single spacing",
      "dependencies": [],
      "required_external_libraries": [],
      "deterministic": true,
      "pipeline_stage": "EXTRACTION",
      "execution_model": "single-pass FSM parser",
      "observability": {
        "logging": "structured JSON",
        "trace_fields": ["trace_id", "span_id"],
        "lifecycle": ["INIT", "VALIDATED", "PROCESSING", "COMPLETED"]
      }
    }
```
```
    "SCRIPT_002": {
      "script_id": "SCRIPT_002",
      "name": "workflow_state_manager",
      "version": "1.0",
      "category": "PROCESSOR",
      "input_schema": "validated structured prompt outputs",
      "output_schema": "updated workflow_state.json",
      "dependencies": ["SCRIPT_001"],
      "required_external_libraries": [],
      "deterministic": true,
      "pipeline_stage": "TRANSFORMATION",
      "execution_model": "schema-validated state persistence",
      "observability": {
        "logging": "structured JSON",
        "trace_fields": ["trace_id", "span_id"],
        "lifecycle": ["INIT", "VALIDATED", "PROCESSING", "COMPLETED"]
      }
    }
```
