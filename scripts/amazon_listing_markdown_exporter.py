#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
amazon_listing_markdown_exporter.py

SCRIPT_METADATA:
{
  "script_id": "SCRIPT_003",
  "name": "amazon_listing_markdown_exporter",
  "version": "1.0",
  "category": "PROCESSOR",
  "input_schema": "workflow_state_v1",
  "output_schema": "amazon_listing_copy_paste_markdown_v1",
  "dependencies": ["SCRIPT_002"],
  "external_libraries": [],
  "status": "ACTIVE"
}

Purpose:
    Read output/workflow_state.json and export Amazon listing data into a
    Markdown-only copy/paste file for manual Amazon listing entry.

Default input:
    output/workflow_state.json

Default output:
    output/amazon_listing_copy_paste.md
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SCRIPT_METADATA: Dict[str, Any] = {
    "script_id": "SCRIPT_003",
    "name": "amazon_listing_markdown_exporter",
    "version": "1.0",
    "category": "PROCESSOR",
    "input_schema": "workflow_state_v1",
    "output_schema": "amazon_listing_copy_paste_markdown_v1",
    "dependencies": ["SCRIPT_002"],
    "external_libraries": [],
    "status": "ACTIVE",
}

DEFAULT_INPUT_PATH = Path("output") / "workflow_state.json"
DEFAULT_OUTPUT_PATH = Path("output") / "amazon_listing_copy_paste.md"


class ExporterError(Exception):
    """Controlled fail-fast exception for deterministic script termination."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_event(
    *,
    trace_id: str,
    span_id: str,
    event: str,
    stage: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Emit structured JSON logs to stderr.

    Logging is separated from the Markdown artifact so the output file remains
    clean and copy/paste-friendly.
    """
    payload = {
        "timestamp": utc_now_iso(),
        "trace_id": trace_id,
        "span_id": span_id,
        "script_id": SCRIPT_METADATA["script_id"],
        "script_name": SCRIPT_METADATA["name"],
        "category": SCRIPT_METADATA["category"],
        "event": event,
        "stage": stage,
        "status": status,
        "details": details or {},
    }
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)


def fail_fast(error_code: str, message: str) -> None:
    raise ExporterError(error_code, message)


def load_workflow_state(input_path: Path) -> Dict[str, Any]:
    if not input_path.exists():
        fail_fast(
            "INPUT_FILE_NOT_FOUND",
            f"Required workflow_state.json does not exist: {input_path}",
        )

    if not input_path.is_file():
        fail_fast(
            "INPUT_PATH_NOT_FILE",
            f"Input path exists but is not a file: {input_path}",
        )

    if input_path.stat().st_size == 0:
        fail_fast(
            "INVALID_WORKFLOW_JSON",
            f"Input JSON file is empty: {input_path}",
        )

    try:
        with input_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        fail_fast(
            "INVALID_WORKFLOW_JSON",
            f"Input JSON is malformed at line {exc.lineno}, column {exc.colno}: {exc.msg}",
        )

    if not isinstance(data, dict):
        fail_fast(
            "INVALID_WORKFLOW_JSON",
            "workflow_state.json root must be a JSON object.",
        )

    if not data:
        fail_fast(
            "INVALID_WORKFLOW_JSON",
            "workflow_state.json root object is empty.",
        )

    return data


def normalize_label(raw_key: str) -> str:
    return raw_key.replace("_", " ").replace("-", " ").strip().title()


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def unwrap_section(section: Any, preferred_key: str) -> Any:
    """
    Many workflow sections are shaped as:
        {"reference_tag": "", "amazon_product_title": "..."}
    This returns the real payload when the preferred key exists.
    """
    if isinstance(section, dict) and preferred_key in section:
        return section[preferred_key]
    return section


def get_output_section(state: Dict[str, Any], output_key: str) -> Any:
    outputs = state.get("outputs", {})
    if not isinstance(outputs, dict):
        return None
    return outputs.get(output_key)


def get_section_payload(
    state: Dict[str, Any],
    *,
    top_level_key: str,
    output_key: str,
    payload_key: str,
) -> Any:
    """
    Prefer top-level normalized sections when available, then fall back to the
    outputs map generated by the workflow orchestrator.
    """
    top_level = state.get(top_level_key)
    if not is_blank(top_level):
        return unwrap_section(top_level, payload_key)

    output_section = get_output_section(state, output_key)
    if not is_blank(output_section):
        return unwrap_section(output_section, payload_key)

    return None


def sort_output_keys(keys: Iterable[str]) -> List[str]:
    def sort_key(value: str) -> Tuple[int, str]:
        try:
            return int(value), value
        except ValueError:
            return 10_000, value

    return sorted(keys, key=sort_key)


def collect_image_strategies(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Collect image strategies from both:
      - outputs sections such as 11, 13, 15, 17, 19, 21, 23
      - top-level keys such as image_strategy_1, image_strategy_13, etc.

    Deduplication is based on image_number + image_type + headline_text.
    """
    strategies: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str, str]] = set()

    def add_strategy(candidate: Any) -> None:
        if not isinstance(candidate, dict):
            return

        payload = candidate.get("image_strategy") if isinstance(candidate.get("image_strategy"), dict) else candidate

        if not isinstance(payload, dict):
            return

        if "image_number" not in payload and "image_type" not in payload:
            return

        identity = (
            str(payload.get("image_number", "")),
            str(payload.get("image_type", "")),
            str(payload.get("headline_text", "")),
        )

        if identity in seen:
            return

        seen.add(identity)
        strategies.append(payload)

    outputs = state.get("outputs", {})
    if isinstance(outputs, dict):
        for output_key in sort_output_keys(outputs.keys()):
            add_strategy(outputs.get(output_key))

    for key in sorted(state.keys()):
        if key.startswith("image_strategy"):
            add_strategy(state.get(key))

    def image_sort_key(item: Dict[str, Any]) -> Tuple[int, str]:
        value = item.get("image_number")
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = 10_000
        return number, str(item.get("image_type", ""))

    return sorted(strategies, key=image_sort_key)


def collect_core_sections(state: Dict[str, Any]) -> List[Tuple[str, Any]]:
    """
    Extract the confirmed Amazon listing fields in a stable order.
    """
    sections: List[Tuple[str, Any]] = []

    sections.append(
        (
            "Source Product Profile",
            get_output_section(state, "01A"),
        )
    )

    sections.append(
        (
            "Visual Product Identity",
            get_output_section(state, "01B"),
        )
    )

    sections.append(
        (
            "Amazon Product Title",
            get_section_payload(
                state,
                top_level_key="amazon_product_title",
                output_key="02",
                payload_key="amazon_product_title",
            ),
        )
    )

    sections.append(
        (
            "Amazon Bullet Points",
            get_section_payload(
                state,
                top_level_key="amazon_bullet_points",
                output_key="03",
                payload_key="amazon_bullet_points",
            ),
        )
    )

    sections.append(
        (
            "Amazon Product Description",
            get_section_payload(
                state,
                top_level_key="amazon_product_description",
                output_key="04",
                payload_key="amazon_product_description",
            ),
        )
    )

    sections.append(
        (
            "Amazon Backend Search Terms",
            get_section_payload(
                state,
                top_level_key="amazon_backend_search_terms",
                output_key="05",
                payload_key="amazon_backend_search_terms",
            ),
        )
    )

    sections.append(
        (
            "Customer Search Intent Keywords",
            get_section_payload(
                state,
                top_level_key="customer_search_intent_keywords",
                output_key="06",
                payload_key="customer_search_intent_keywords",
            ),
        )
    )

    sections.append(
        (
            "Amazon A+ Content",
            get_section_payload(
                state,
                top_level_key="amazon_aplus_content",
                output_key="07",
                payload_key="amazon_aplus_content",
            ),
        )
    )

    sections.append(
        (
            "Technical Specifications",
            get_section_payload(
                state,
                top_level_key="technical_specifications",
                output_key="08",
                payload_key="technical_specifications",
            ),
        )
    )

    package_contents = None
    specs_top_level = state.get("technical_specifications")
    specs_output = get_output_section(state, "08")

    if isinstance(specs_top_level, dict):
        package_contents = specs_top_level.get("package_contents")

    if is_blank(package_contents) and isinstance(specs_output, dict):
        package_contents = specs_output.get("package_contents")

    sections.append(("Package Contents", package_contents))

    sections.append(
        (
            "Customer FAQ",
            get_section_payload(
                state,
                top_level_key="customer_faq",
                output_key="09",
                payload_key="customer_faq",
            ),
        )
    )

    sections.append(
        (
            "Social Media Posts",
            get_output_section(state, "10"),
        )
    )

    image_strategies = collect_image_strategies(state)
    sections.append(("Amazon Image Strategy", image_strategies))

    return [(title, payload) for title, payload in sections if not is_blank(payload)]


def render_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def render_markdown_value(value: Any, heading_level: int = 3) -> List[str]:
    """
    Render arbitrary JSON-compatible values into readable Markdown.
    This intentionally avoids Markdown tables because long Amazon copy fields,
    prompts, and descriptions are easier to copy from labeled blocks.
    """
    lines: List[str] = []

    if isinstance(value, dict):
        for key, item in value.items():
            if key == "reference_tag" and is_blank(item):
                continue

            label = normalize_label(str(key))

            if isinstance(item, (dict, list)):
                lines.append(f"{'#' * heading_level} {label}")
                lines.extend(render_markdown_value(item, heading_level + 1))
            else:
                lines.append(f"**{label}:**")
                lines.append("")
                lines.append(render_scalar(item))
                lines.append("")
        return lines

    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            for index, item in enumerate(value, start=1):
                lines.append(f"{index}. {render_scalar(item)}")
            lines.append("")
            return lines

        for index, item in enumerate(value, start=1):
            lines.append(f"{'#' * heading_level} Item {index}")
            lines.extend(render_markdown_value(item, heading_level + 1))
        return lines

    lines.append(render_scalar(value))
    lines.append("")
    return lines


def render_copy_block(label: str, value: Any) -> List[str]:
    """
    Render primary copy fields with a clear label and copyable body.
    """
    lines: List[str] = [f"## {label}", ""]

    if isinstance(value, str):
        lines.append(value.strip())
        lines.append("")
        return lines

    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        for index, item in enumerate(value, start=1):
            lines.append(f"**Bullet {index}:**")
            lines.append(item.strip())
            lines.append("")
        return lines

    lines.extend(render_markdown_value(value, heading_level=3))
    lines.append("")
    return lines


def render_markdown_document(
    *,
    state: Dict[str, Any],
    input_path: Path,
    sections: List[Tuple[str, Any]],
) -> str:
    trace_id = str(state.get("trace_id", "")) or "UNAVAILABLE"
    source_script = state.get("script_metadata", {})
    source_script_name = ""

    if isinstance(source_script, dict):
        source_script_name = str(source_script.get("name", ""))

    lines: List[str] = [
        "# Amazon Listing Copy/Paste Export",
        "",
        "## Export Metadata",
        "",
        f"**Generated At UTC:** {utc_now_iso()}",
        "",
        f"**Source File:** `{input_path.as_posix()}`",
        "",
        f"**Workflow Trace ID:** `{trace_id}`",
        "",
        f"**Source Workflow Script:** `{source_script_name or 'UNAVAILABLE'}`",
        "",
        f"**Exporter Script:** `{SCRIPT_METADATA['name']} v{SCRIPT_METADATA['version']}`",
        "",
        "---",
        "",
    ]

    primary_copy_fields = {
        "Amazon Product Title",
        "Amazon Bullet Points",
        "Amazon Product Description",
        "Amazon Backend Search Terms",
    }

    for title, payload in sections:
        if title in primary_copy_fields:
            lines.extend(render_copy_block(title, payload))
        else:
            lines.append(f"## {title}")
            lines.append("")
            lines.extend(render_markdown_value(payload, heading_level=3))
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def validate_extracted_sections(sections: List[Tuple[str, Any]]) -> None:
    if not sections:
        fail_fast(
            "AMAZON_FIELDS_MISSING",
            "No extractable Amazon listing fields found.",
        )

    required_titles = {
        "Amazon Product Title",
        "Amazon Bullet Points",
        "Amazon Product Description",
        "Amazon Backend Search Terms",
    }

    present_titles = {title for title, payload in sections if not is_blank(payload)}
    missing = sorted(required_titles - present_titles)

    if missing:
        fail_fast(
            "AMAZON_REQUIRED_FIELDS_MISSING",
            "Required Amazon listing fields missing: " + ", ".join(missing),
        )


def write_markdown_output(output_path: Path, markdown: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        fail_fast(
            "OUTPUT_WRITE_FAILED",
            f"Failed to write Markdown output file: {output_path} ({exc})",
        )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract Amazon listing fields from output/workflow_state.json "
            "and write a Markdown copy/paste export."
        )
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to workflow_state.json. Default: output/workflow_state.json",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Path to Markdown export file. Default: output/amazon_listing_copy_paste.md",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        log_event(
            trace_id=trace_id,
            span_id=span_id,
            event="INIT",
            stage="INGESTION",
            status="STARTED",
            details={
                "input_path": str(input_path),
                "output_path": str(output_path),
            },
        )

        state = load_workflow_state(input_path)

        log_event(
            trace_id=trace_id,
            span_id=span_id,
            event="VALIDATED",
            stage="VALIDATION",
            status="SUCCESS",
            details={"input_path": str(input_path)},
        )

        sections = collect_core_sections(state)
        validate_extracted_sections(sections)

        log_event(
            trace_id=trace_id,
            span_id=span_id,
            event="PROCESSING",
            stage="TRANSFORMATION",
            status="SUCCESS",
            details={"section_count": len(sections)},
        )

        markdown = render_markdown_document(
            state=state,
            input_path=input_path,
            sections=sections,
        )

        write_markdown_output(output_path, markdown)

        log_event(
            trace_id=trace_id,
            span_id=span_id,
            event="COMPLETED",
            stage="OUTPUT",
            status="SUCCESS",
            details={
                "output_path": str(output_path),
                "bytes_written": output_path.stat().st_size,
            },
        )

        print(f"Markdown export written to: {output_path}")
        return 0

    except ExporterError as exc:
        log_event(
            trace_id=trace_id,
            span_id=span_id,
            event="FAILED",
            stage="FAIL_FAST",
            status="ERROR",
            details={
                "error_code": exc.error_code,
                "message": exc.message,
            },
        )
        print(f"{exc.error_code}: {exc.message}", file=sys.stderr)
        return 1

    except Exception as exc:
        log_event(
            trace_id=trace_id,
            span_id=span_id,
            event="FAILED",
            stage="UNHANDLED_EXCEPTION",
            status="ERROR",
            details={
                "error_code": "UNHANDLED_EXCEPTION",
                "message": str(exc),
            },
        )
        print(f"UNHANDLED_EXCEPTION: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
