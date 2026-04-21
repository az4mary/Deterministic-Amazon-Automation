# workflow_orchestrator.py
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import os
import re
import inspect
import linecache
import sys
import time
from datetime import datetime, timezone, timedelta
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI

SCRIPT_METADATA = {
    "script_id": "SCRIPT_002",
    "name": "workflow_orchestrator",
    "version": "1.0",
    "category": "PROCESSOR",
    "input_schema": "workflow inputs from local filesystem (raw text + images + prompt files)",
    "output_schema": "workflow_state.json + generated artifacts under output/",
    "dependencies": [],
    "external_libraries": ["openai"],
    "status": "ACTIVE",
}

ROOT = Path(r"C:\Users\HP\Documents\Obsidian\test\PROJECTS")
DATA_DIR = ROOT / "data"
PROMPTS_DIR = ROOT / "docs" / "prompts"
OUTPUT_DIR = ROOT / "output"
LOG_DIR = OUTPUT_DIR / "logs"
IMAGE_SOURCE_DIR = DATA_DIR / "images"
GENERATED_IMAGE_DIR = OUTPUT_DIR / "generated_images"
STATE_PATH = OUTPUT_DIR / "workflow_state.json"
RAW_TEXT_PATH = DATA_DIR / "raw_product_input.txt"

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.4")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")

TRACE_ID = ""
SPAN_COUNTER = 0
RUN_START_TIME = 0.0
TERMINAL_EVENT_EMITTED = False
LAST_PROGRESS_PERCENT = -1
LOG_SEQUENCE = 0
SYNTHETIC_DURATION_MS = 0
DETERMINISTIC_TIME_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)

TEXT_STEP_WAIT_SECONDS = 600
IMAGE_STEP_WAIT_SECONDS = 900


@dataclass(frozen=True)
class Step:
    step_id: str
    kind: str  # "text" | "image_prompt" | "image_generate"
    prompt_file: Optional[str]
    output_key: str
    schema_builder: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    image_ref_key: Optional[str] = None


def next_span_id() -> str:
    global SPAN_COUNTER
    SPAN_COUNTER += 1
    return f"{SPAN_COUNTER:06d}"


class PromptExecutionAdapter:
    def execute_text(self, step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def execute_image(self, prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
        raise NotImplementedError


class OpenAIPromptExecutionAdapter(PromptExecutionAdapter):
    def __init__(self, client: OpenAI) -> None:
        self.client = client

    def execute_text(self, step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.responses.create(
            model=TEXT_MODEL,
            input=build_text_input(state, prompt_text),
            text={"format": {"type": "json_schema", "json_schema": {"name": f"step_{step_id}", "schema": schema, "strict": True}}},
            temperature=0,
        )
        raw = getattr(response, "output_text", "") or ""
        if not raw.strip():
            fail("EMPTY_MODEL_OUTPUT", f"Step {step_id} returned empty output.")
        return parse_response_json(raw)

    def execute_image(self, prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
        response = self.client.responses.create(
            model=IMAGE_MODEL,
            input=prompt,
            tools=[{"type": "image_generation"}],
            tool_choice={"type": "image_generation"},
        )
        image_data = [
            output.result
            for output in response.output
            if getattr(output, "type", None) == "image_generation_call"
        ]
        revised_prompt = None
        for output in response.output:
            if getattr(output, "type", None) == "image_generation_call":
                revised_prompt = getattr(output, "revised_prompt", None)
                break
        if not image_data:
            fail("IMAGE_GENERATION_FAILED", "No image returned by model.")
        return {"image_base64": image_data[0], "revised_prompt": revised_prompt}


client = OpenAI()
EXECUTION_ADAPTER: PromptExecutionAdapter = OpenAIPromptExecutionAdapter(client)


def build_deterministic_trace_id(raw_text_hash: str, image_hashes: List[str]) -> str:
    payload = "|".join([raw_text_hash, *image_hashes, SCRIPT_METADATA["script_id"]])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def json_log(
    *args: Any,
    level: Optional[str] = None,
    message: Optional[str] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    progress_percent: Optional[int] = None,
    current_step: Optional[int] = None,
    total_steps: Optional[int] = None,
    **fields: Any,
) -> None:
    legacy_event: Optional[str] = None

    if len(args) == 1 and isinstance(args[0], str) and level is None and message is None and stage is None and status is None:
        legacy_event = args[0]
        legacy_map = {
            "step_start": ("INFO", "Step started", "PROCESSING", "STARTED"),
            "step_end": ("INFO", "Step completed", "PROCESSING", "COMPLETED"),
            "orchestrator_start": ("INFO", "Orchestrator started", "INIT", "STARTED"),
            "orchestrator_complete": ("INFO", "Orchestrator completed", "OUTPUT", "SUCCESS"),
            "fail_fast": ("ERROR", "Validation failed", "VALIDATION", "FAILED"),
            "unhandled_exception": ("ERROR", "Unhandled exception", "VALIDATION", "FAILED"),
        }
        level, message, stage, status = legacy_map.get(legacy_event, ("INFO", legacy_event, "PROCESSING", "IN_PROGRESS"))
    elif len(args) >= 4 and level is None and message is None and stage is None and status is None:
        level, message, stage, status = args[:4]
    elif level is None or message is None or stage is None or status is None:
        fail(
            "LOGGER_SCHEMA_INVALID",
            "json_log called without required schema fields.",
            field="json_log",
            expected="level/message/stage/status",
            actual=str(args),
        )

    global LOG_SEQUENCE
    record: Dict[str, Any] = {
        "timestamp": (DETERMINISTIC_TIME_BASE + timedelta(seconds=LOG_SEQUENCE)).isoformat().replace("+00:00", "Z"),
        "level": level,
        "message": message,
        "service": "workflow_orchestrator",
        "stage": stage,
        "status": status,
        "trace_id": TRACE_ID,
        "span_id": next_span_id(),
        "context": context or {},
    }

    if legacy_event is not None:
        record["context"] = {"legacy_event": legacy_event, **(context or {})}

    if progress_percent is not None:
        record["progress_percent"] = int(progress_percent)
        record["current_step"] = current_step
        record["total_steps"] = total_steps

    record.update(fields)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "execution.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def emit_lifecycle_event(stage: str, status: str, message: str, progress_percent: int, current_step: int, total_steps: int) -> None:
    validate_progress_percent(progress_percent, current_step, total_steps)
    json_log(
        level="INFO",
        message=message,
        stage=stage,
        status=status,
        context={"stage": stage},
        progress_percent=progress_percent,
        current_step=current_step,
        total_steps=total_steps,
    )


def emit_terminal_event(status: str, message: str, output_hash: str, context: Optional[Dict[str, Any]] = None) -> None:
    global TERMINAL_EVENT_EMITTED
    if TERMINAL_EVENT_EMITTED:
        return

    duration_ms = SYNTHETIC_DURATION_MS
    json_log(
        level="INFO" if status == "SUCCESS" else "ERROR",
        message=message,
        stage="OUTPUT",
        status=status,
        context=context or {},
        duration_ms=duration_ms,
        output_hash=output_hash,
    )
    TERMINAL_EVENT_EMITTED = True


def validate_progress_percent(progress_percent: int, current_step: int, total_steps: int) -> None:
    global LAST_PROGRESS_PERCENT

    if not isinstance(progress_percent, int):
        fail(
            "PROGRESS_TYPE_INVALID",
            "progress_percent must be an integer.",
            field="progress_percent",
            expected="int",
            actual=type(progress_percent).__name__,
            stage="PROCESSING",
        )

    if progress_percent < 0 or progress_percent > 100:
        fail(
            "PROGRESS_RANGE_INVALID",
            "progress_percent must be between 0 and 100.",
            field="progress_percent",
            expected="0..100",
            actual=str(progress_percent),
            stage="PROCESSING",
        )

    if progress_percent < LAST_PROGRESS_PERCENT:
        fail(
            "PROGRESS_NON_MONOTONIC",
            "progress_percent must be monotonic.",
            field="progress_percent",
            expected=f">= {LAST_PROGRESS_PERCENT}",
            actual=str(progress_percent),
            stage="PROCESSING",
        )

    if current_step < 0 or total_steps <= 0 or current_step > total_steps:
        fail(
            "PROGRESS_STEP_INVALID",
            "current_step/total_steps are outside valid bounds.",
            field="current_step",
            expected=f"0 <= current_step <= total_steps and total_steps > 0",
            actual=f"current_step={current_step}, total_steps={total_steps}",
            stage="PROCESSING",
        )

    LAST_PROGRESS_PERCENT = progress_percent


def fail(code: str, message: str, field: str = "", expected: str = "", actual: str = "", stage: str = "VALIDATION") -> None:
    caller = inspect.currentframe().f_back if inspect.currentframe() and inspect.currentframe().f_back else None
    file_path = str(Path(caller.f_code.co_filename)) if caller else ""
    line_no = int(caller.f_lineno) if caller else 0
    snippet = linecache.getline(file_path, line_no).strip() if file_path and line_no else ""

    error_context = {
        "error_code": code,
        "field": field,
        "expected": expected,
        "actual": actual,
        "file": file_path,
        "line": line_no,
        "snippet": snippet,
    }

    json_log(
        level="ERROR",
        message=message,
        stage=stage,
        status="FAILED",
        context=error_context,
    )
    emit_terminal_event(
        status="FAILED",
        message=message,
        output_hash="",
        context=error_context,
    )
    raise SystemExit(json.dumps({
        "error_code": code,
        "field": field,
        "expected": expected,
        "actual": actual,
        "file": file_path,
        "line": line_no,
        "snippet": snippet,
        "trace_id": TRACE_ID
    }))


def ensure_dirs() -> None:
    for p in [DATA_DIR, PROMPTS_DIR, OUTPUT_DIR, LOG_DIR, IMAGE_SOURCE_DIR, GENERATED_IMAGE_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        fail("MISSING_FILE", f"Missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        fail("INVALID_JSON", f"Invalid JSON at {path}: {e}")


def save_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def load_text(path: Path, required: bool = True) -> str:
    if not path.exists():
        if required:
            fail("MISSING_FILE", f"Missing file: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def normalize_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_response_json(response_text: str) -> Dict[str, Any]:
    try:
        return json.loads(normalize_json_text(response_text))
    except Exception as e:
        fail("MODEL_OUTPUT_NOT_JSON", f"Model output is not valid JSON: {e}")


def workflow_state_init() -> Dict[str, Any]:
    return {
        "reference_tag": "",
        "trace_id": TRACE_ID,
        "script_metadata": SCRIPT_METADATA,
        "source": {
            "raw_text_path": str(RAW_TEXT_PATH),
            "image_dir": str(IMAGE_SOURCE_DIR),
        },
        "outputs": {},
    }


def merge_output(state: Dict[str, Any], step_id: str, output: Dict[str, Any], output_key: str) -> None:
    state["outputs"][step_id] = output
    state[output_key] = output
    state["last_completed_step"] = step_id


def read_source_images() -> List[Path]:
    if not IMAGE_SOURCE_DIR.exists():
        return []
    return sorted([p for p in IMAGE_SOURCE_DIR.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}])


def encode_image_data_url(path: Path) -> str:
    mime = "image/png"
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif path.suffix.lower() == ".webp":
        mime = "image/webp"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"


def build_text_schema(output_key: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": output_key,
        "schema": schema,
        "strict": True,
        "type": "json_schema",
    }


def schema_1a() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "reference_tag",
            "product_category",
            "product_profile",
            "core_features",
            "attributes",
            "additional_attributes",
            "package_contents",
            "product_summary",
        ],
        "properties": {
            "reference_tag": {"type": "string"},
            "product_category": {"type": "string"},
            "product_profile": {
                "type": "object",
                "additionalProperties": False,
                "required": ["brand", "product_name", "model", "color"],
                "properties": {
                    "brand": {"type": "string"},
                    "product_name": {"type": "string"},
                    "model": {"type": "string"},
                    "color": {"type": "string"},
                },
            },
            "core_features": {"type": "array", "items": {"type": "string"}},
            "attributes": {"type": "object", "additionalProperties": {"type": "string"}},
            "additional_attributes": {"type": "object", "additionalProperties": {"type": "string"}},
            "package_contents": {"type": "array", "items": {"type": "string"}},
            "product_summary": {"type": "string"},
        },
    }


def schema_1b() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "image_views",
            "visual_identity",
            "object_layout_map",
            "lighting_profile",
            "camera_profile",
            "product_geometry",
        ],
        "properties": {
            "image_views": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "front_3q_left": {"type": "string"},
                    "front_3q_right": {"type": "string"},
                    "rear_3q": {"type": "string"},
                    "left_side": {"type": "string"},
                    "right_side": {"type": "string"},
                    "top_view": {"type": "string"},
                    "bottom_view": {"type": "string"},
                    "detail_closeup": {"type": "string"},
                    "accessories_layout": {"type": "string"},
                },
            },
            "visual_identity": {
                "type": "object",
                "additionalProperties": False,
                "required": ["product_type", "dominant_color", "materials", "primary_components"],
                "properties": {
                    "product_type": {"type": "string"},
                    "dominant_color": {"type": "string"},
                    "materials": {"type": "string"},
                    "primary_components": {"type": "array", "items": {"type": "string"}},
                },
            },
            "object_layout_map": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "component_positions": {"type": "object", "additionalProperties": {"type": "string"}},
                },
            },
            "lighting_profile": {
                "type": "object",
                "additionalProperties": False,
                "required": ["lighting_type", "shadow_behavior", "reflection_style"],
                "properties": {
                    "lighting_type": {"type": "string"},
                    "shadow_behavior": {"type": "string"},
                    "reflection_style": {"type": "string"},
                },
            },
            "camera_profile": {
                "type": "object",
                "additionalProperties": False,
                "required": ["camera_angle", "orientation", "lens_style"],
                "properties": {
                    "camera_angle": {"type": "string"},
                    "orientation": {"type": "string"},
                    "lens_style": {"type": "string"},
                },
            },
            "product_geometry": {
                "type": "object",
                "additionalProperties": False,
                "required": ["shape_description", "proportions", "relative_dimensions"],
                "properties": {
                    "shape_description": {"type": "string"},
                    "proportions": {"type": "string"},
                    "relative_dimensions": {"type": "string"},
                },
            },
        },
    }


def schema_title() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "amazon_product_title"],
        "properties": {
            "reference_tag": {"type": "string"},
            "amazon_product_title": {"type": "string"},
        },
    }


def schema_bullets() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "amazon_bullet_points"],
        "properties": {
            "reference_tag": {"type": "string"},
            "amazon_bullet_points": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": {"type": "string"},
            },
        },
    }


def schema_description() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "amazon_product_description"],
        "properties": {
            "reference_tag": {"type": "string"},
            "amazon_product_description": {"type": "string"},
        },
    }


def schema_backend() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "amazon_backend_search_terms"],
        "properties": {
            "reference_tag": {"type": "string"},
            "amazon_backend_search_terms": {"type": "string"},
        },
    }


def schema_search_intent() -> Dict[str, Any]:
    arr = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "customer_search_intent_keywords"],
        "properties": {
            "reference_tag": {"type": "string"},
            "customer_search_intent_keywords": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "generic_searches",
                    "feature_searches",
                    "problem_solution_searches",
                    "use_case_searches",
                    "long_tail_buyer_searches",
                ],
                "properties": {
                    "generic_searches": arr,
                    "feature_searches": arr,
                    "problem_solution_searches": arr,
                    "use_case_searches": arr,
                    "long_tail_buyer_searches": arr,
                },
            },
        },
    }


def schema_aplus() -> Dict[str, Any]:
    section = {
        "type": "object",
        "additionalProperties": False,
        "required": ["headline", "supporting_text"],
        "properties": {
            "headline": {"type": "string"},
            "supporting_text": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "amazon_aplus_content"],
        "properties": {
            "reference_tag": {"type": "string"},
            "amazon_aplus_content": {
                "type": "object",
                "additionalProperties": False,
                "required": ["brand_story", "feature_section_1", "feature_section_2", "feature_section_3", "feature_section_4"],
                "properties": {
                    "brand_story": {"type": "string"},
                    "feature_section_1": section,
                    "feature_section_2": section,
                    "feature_section_3": section,
                    "feature_section_4": section,
                },
            },
        },
    }


def schema_specs() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "technical_specifications"],
        "properties": {
            "reference_tag": {"type": "string"},
            "technical_specifications": {
                "type": "object",
                "additionalProperties": False,
                "required": ["Brand", "Product Name", "Model", "Color", "Attributes"],
                "properties": {
                    "Brand": {"type": "string"},
                    "Product Name": {"type": "string"},
                    "Model": {"type": "string"},
                    "Color": {"type": "string"},
                    "Attributes": {"type": "object", "additionalProperties": {"type": "string"}},
                },
            },
        },
    }


def schema_faq() -> Dict[str, Any]:
    faq_item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["question", "answer"],
        "properties": {
            "question": {"type": "string"},
            "answer": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "customer_faq"],
        "properties": {
            "reference_tag": {"type": "string"},
            "customer_faq": {"type": "array", "minItems": 5, "maxItems": 5, "items": faq_item},
        },
    }


def schema_social() -> Dict[str, Any]:
    post = {
        "type": "object",
        "additionalProperties": False,
        "required": ["post_number", "caption_title", "caption_text", "tags", "hashtags"],
        "properties": {
            "post_number": {"type": "integer"},
            "caption_title": {"type": "string"},
            "caption_text": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "hashtags": {"type": "array", "items": {"type": "string"}},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "social_media_posts"],
        "properties": {
            "reference_tag": {"type": "string"},
            "social_media_posts": {"type": "array", "minItems": 3, "maxItems": 3, "items": post},
        },
    }


def schema_image_prompt(image_number: int, buyer_question: str, image_type: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reference_tag", "image_strategy"],
        "properties": {
            "reference_tag": {"type": "string"},
            "image_strategy": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "image_number",
                    "image_type",
                    "buyer_question",
                    "layout_description",
                    "headline_text",
                    "supporting_text",
                    "visual_design_direction",
                    "image_generation_prompt",
                ],
                "properties": {
                    "image_number": {"const": image_number},
                    "image_type": {"const": image_type},
                    "buyer_question": {"const": buyer_question},
                    "layout_description": {"type": "string"},
                    "headline_text": {"type": "string"},
                    "supporting_text": {"type": "string"},
                    "visual_design_direction": {"type": "string"},
                    "image_generation_prompt": {"type": "string"},
                },
            },
        },
    }


def read_prompt_file(step_id: str) -> str:
    candidates = [
        PROMPTS_DIR / f"prompt_{step_id}.txt",
        PROMPTS_DIR / f"{step_id}.txt",
        PROMPTS_DIR / f"{step_id}.md",
    ]
    for c in candidates:
        if c.exists():
            return c.read_text(encoding="utf-8")
    fail("MISSING_PROMPT", f"No prompt file found for step {step_id} in {PROMPTS_DIR}")


def build_text_input(state: Dict[str, Any], prompt_text: str) -> str:
    compact_state = json.dumps(state, ensure_ascii=False, indent=2)
    return (
        f"WORKFLOW_STATE_JSON:\n{compact_state}\n\n"
        f"INSTRUCTIONS:\n{prompt_text}\n\n"
        f"OUTPUT RULES:\nReturn only valid JSON."
    )


def call_text_step(step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    json_log("step_start", step_id=step_id, kind="text")
    parsed = EXECUTION_ADAPTER.execute_text(step_id, prompt_text, schema, state)
    json_log("step_end", step_id=step_id, kind="text", output_keys=list(parsed.keys()))
    return parsed


def call_image_generation(prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
    json_log("step_start", kind="image_generation", size=size)
    response = client.responses.create(
        model=IMAGE_MODEL,
        input=prompt,
        tools=[{"type": "image_generation"}],
        tool_choice={"type": "image_generation"},
    )
    image_data = [
        output.result
        for output in response.output
        if getattr(output, "type", None) == "image_generation_call"
    ]
    revised_prompt = None
    for output in response.output:
        if getattr(output, "type", None) == "image_generation_call":
            revised_prompt = getattr(output, "revised_prompt", None)
            break
    if not image_data:
        fail("IMAGE_GENERATION_FAILED", "No image returned by model.")
    return {"image_base64": image_data[0], "revised_prompt": revised_prompt}


def save_image(image_base64: str, name: str) -> str:
    GENERATED_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = GENERATED_IMAGE_DIR / name
    out_path.write_bytes(base64.b64decode(image_base64))
    return str(out_path)


def update_state_with_prompt(state: Dict[str, Any], step_id: str, output: Dict[str, Any], output_key: str) -> None:
    merge_output(state, step_id, output, output_key)
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def deterministic_style_lock() -> Dict[str, str]:
    return {
        "lighting": "studio product photography",
        "camera_lens": "50mm product photography",
        "shadow_style": "soft studio shadow",
        "product_scale": "centered filling frame",
        "background": "pure white",
        "color_profile": "commercial product photography",
    }


def apply_step_wait(step_kind: str) -> None:
    global SYNTHETIC_DURATION_MS

    if step_kind == "text":
        time.sleep(TEXT_STEP_WAIT_SECONDS)
        SYNTHETIC_DURATION_MS += TEXT_STEP_WAIT_SECONDS * 1000
    elif step_kind == "image_generate":
        time.sleep(IMAGE_STEP_WAIT_SECONDS)
        SYNTHETIC_DURATION_MS += IMAGE_STEP_WAIT_SECONDS * 1000


STEP_PLAN: List[Step] = [
    Step("01A", "text", "prompt_01A.txt", "prompt_01A", schema_1a),
    Step("01B", "text", "prompt_01B.txt", "prompt_01B", schema_1b),
    Step("02", "text", "prompt_02.txt", "amazon_product_title", schema_title),
    Step("03", "text", "prompt_03.txt", "amazon_bullet_points", schema_bullets),
    Step("04", "text", "prompt_04.txt", "amazon_product_description", schema_description),
    Step("05", "text", "prompt_05.txt", "amazon_backend_search_terms", schema_backend),
    Step("06", "text", "prompt_06.txt", "customer_search_intent_keywords", schema_search_intent),
    Step("07", "text", "prompt_07.txt", "amazon_aplus_content", schema_aplus),
    Step("08", "text", "prompt_08.txt", "technical_specifications", schema_specs),
    Step("09", "text", "prompt_09.txt", "customer_faq", schema_faq),
    Step("10", "text", "prompt_10.txt", "social_media_posts", schema_social),
    Step("11", "text", "prompt_11.txt", "image_strategy_1", lambda s: schema_image_prompt(1, "What is this product?", "Hero Product Image")),
    Step("12", "image_generate", None, "generated_image_1", None),
    Step("13", "text", "prompt_13.txt", "image_strategy_2", lambda s: schema_image_prompt(2, "Why do I need it?", "Core Benefit Image")),
    Step("14", "image_generate", None, "generated_image_2", None),
    Step("15", "text", "prompt_15.txt", "image_strategy_3", lambda s: schema_image_prompt(3, "What problem does this product solve?", "Problem Solution Image")),
    Step("16", "image_generate", None, "generated_image_3", None),
    Step("17", "text", "prompt_17.txt", "image_strategy_4", lambda s: schema_image_prompt(4, "When would I use it?", "Lifestyle Use Image")),
    Step("18", "image_generate", None, "generated_image_4", None),
    Step("19", "text", "prompt_19.txt", "image_strategy_5", lambda s: schema_image_prompt(5, "What technology makes it better?", "Technology Feature Image")),
    Step("20", "image_generate", None, "generated_image_5", None),
    Step("21", "text", "prompt_21.txt", "image_strategy_6", lambda s: schema_image_prompt(6, "How easy is it to install or use?", "Ease of Use / Installation Image")),
    Step("22", "image_generate", None, "generated_image_6", None),
    Step("23", "text", "prompt_23.txt", "image_strategy_7", lambda s: schema_image_prompt(7, "What specifications matter?", "Specifications Infographic")),
    Step("24", "image_generate", None, "generated_image_7", None),
]


def run_step(step: Step, state: Dict[str, Any]) -> None:
    if step.kind == "text":
        prompt_text = read_prompt_file(step.step_id)
        schema = step.schema_builder(state) if step.schema_builder else {}
        output = call_text_step(step.step_id, prompt_text, schema, state)
        update_state_with_prompt(state, step.step_id, output, step.output_key)

        # Promote key outputs for downstream prompts.
        if step.step_id == "01A":
            state["dataset"] = output
        elif step.step_id == "01B":
            state["visual_grounding"] = output
        elif step.step_id == "11":
            state["image_strategy"] = output["image_strategy"]
        elif step.step_id in {"13", "15", "17", "19", "21", "23"}:
            key = f"image_strategy_{step.step_id}"
            state[key] = output["image_strategy"]

    elif step.kind == "image_generate":
        # Use the immediately preceding image strategy prompt stored in state.
        prev_strategy_key = f"image_strategy_{int(step.step_id) - 1}"
        strategy = state.get(prev_strategy_key) or state.get("image_strategy")
        if not strategy:
            fail("MISSING_IMAGE_STRATEGY", f"No image strategy found for image generation step {step.step_id}")
        prompt = strategy["image_generation_prompt"]

        result = call_image_generation(prompt)
        image_filename = f"image_{step.step_id}.png"
        saved_path = save_image(result["image_base64"], image_filename)

        output = {
            "reference_tag": state["reference_tag"],
            "generated_image": {
                "image_number": int(step.step_id) // 2,
                "image_type": strategy["image_type"],
                "image_generation_prompt": prompt,
                "saved_path": saved_path,
                "revised_prompt": result.get("revised_prompt"),
            },
            "image_style_lock": deterministic_style_lock(),
        }
        update_state_with_prompt(state, step.step_id, output, step.output_key)

        # keep a canonical style lock for later prompts
        state["image_style_lock"] = output["image_style_lock"]

    else:
        fail("UNKNOWN_STEP_KIND", f"Unknown step kind: {step.kind}")

    save_json_atomic(STATE_PATH, state)
    apply_step_wait(step.kind)

def validate_initial_inputs() -> None:
    if not RAW_TEXT_PATH.exists():
        fail("MISSING_INPUT", f"Missing raw text input: {RAW_TEXT_PATH}")
    if not IMAGE_SOURCE_DIR.exists():
        fail("MISSING_INPUT", f"Missing image source directory: {IMAGE_SOURCE_DIR}")
    if len(read_source_images()) == 0:
        fail("MISSING_IMAGES", "No source images found in data/images/")
    if not PROMPTS_DIR.exists():
        fail("MISSING_PROMPTS", f"Missing prompts directory: {PROMPTS_DIR}")


def main() -> None:
    global RUN_START_TIME, LOG_SEQUENCE, SYNTHETIC_DURATION_MS, TERMINAL_EVENT_EMITTED, LAST_PROGRESS_PERCENT, SPAN_COUNTER
    RUN_START_TIME = time.time()
    LOG_SEQUENCE = 0
    SYNTHETIC_DURATION_MS = 0
    TERMINAL_EVENT_EMITTED = False
    LAST_PROGRESS_PERCENT = -1
    SPAN_COUNTER = 0

    parser = argparse.ArgumentParser(description="Deterministic workflow orchestrator")
    parser.add_argument("--resume", action="store_true", help="Resume from existing workflow_state.json")
    parser.add_argument("--stop-after", default=None, help="Optional step id to stop after (e.g. 10)")
    args = parser.parse_args()

    ensure_dirs()

    state = load_json(STATE_PATH) if args.resume and STATE_PATH.exists() else workflow_state_init()
    state.setdefault("reference_tag", "")
    state.setdefault("outputs", {})

    validate_initial_inputs()

    raw_text_hash = hashlib.sha256(RAW_TEXT_PATH.read_bytes()).hexdigest()
    image_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in read_source_images()]

    global TRACE_ID
    TRACE_ID = build_deterministic_trace_id(raw_text_hash, image_hashes)

    emit_lifecycle_event(
        stage="INIT",
        status="STARTED",
        message="Orchestrator initialization started",
        progress_percent=0,
        current_step=0,
        total_steps=len(STEP_PLAN),
    )

    emit_lifecycle_event(
        stage="VALIDATED",
        status="COMPLETED",
        message="Input validation completed",
        progress_percent=0,
        current_step=0,
        total_steps=len(STEP_PLAN),
    )

    state["input_fingerprint"] = {
        "raw_text_sha256": raw_text_hash,
        "image_sha256": image_hashes,
    }

    state["source_payload"] = {
        "raw_text": load_text(RAW_TEXT_PATH),
        "source_images": [str(p) for p in read_source_images()],
    }

    save_json_atomic(STATE_PATH, state)

    emit_lifecycle_event(
        stage="PROCESSING",
        status="STARTED",
        message="Workflow processing started",
        progress_percent=0,
        current_step=0,
        total_steps=len(STEP_PLAN),
    )

    for idx, step in enumerate(STEP_PLAN, start=1):
        if args.stop_after and step.step_id == args.stop_after:
            break
        run_step(step, state)
        progress_percent = min(100, int((idx / len(STEP_PLAN)) * 100))
        validate_progress_percent(progress_percent, idx, len(STEP_PLAN))
        json_log(
            level="INFO",
            message=f"Completed step {step.step_id}",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"step_id": step.step_id},
            progress_percent=progress_percent,
            current_step=idx,
            total_steps=len(STEP_PLAN),
        )

    save_json_atomic(STATE_PATH, state)

    output_hash = hashlib.sha256(STATE_PATH.read_bytes()).hexdigest()
    emit_lifecycle_event(
        stage="COMPLETED",
        status="SUCCESS",
        message="Workflow completed successfully",
        progress_percent=100,
        current_step=len(STEP_PLAN),
        total_steps=len(STEP_PLAN),
    )
    emit_terminal_event(
        status="SUCCESS",
        message="Workflow completed successfully",
        output_hash=output_hash,
        context={"completed_step": state.get("last_completed_step")},
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        json_log("unhandled_exception", error=str(e))
        raise
