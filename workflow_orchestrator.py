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
from playwright.sync_api import sync_playwright

SCRIPT_METADATA = {
    "script_id": "SCRIPT_002",
    "name": "workflow_orchestrator",
    "version": "1.0",
    "category": "PROCESSOR",
    "input_schema": "workflow inputs from local filesystem (raw text + images + prompt files)",
    "output_schema": "workflow_state.json + generated artifacts under output/",
    "dependencies": [],
    "external_libraries": ["openai", "playwright"],
    "status": "ACTIVE",
}

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PROMPTS_DIR = ROOT / "docs" / "prompts"
PROMPTS_MD_PATH = ROOT / "docs" / "prompts.md"
OUTPUT_DIR = ROOT / "output"
LOG_DIR = OUTPUT_DIR / "logs"
IMAGE_SOURCE_DIR = DATA_DIR / "images"
GENERATED_IMAGE_DIR = OUTPUT_DIR / "generated_images"
STATE_PATH = OUTPUT_DIR / "workflow_state.json"
IMAGE_PROMPTS_PATH = OUTPUT_DIR / "image_prompts.json"
RAW_TEXT_PATH = DATA_DIR / "raw_product_input.txt"
RAW_TEXT_PATH_MD = DATA_DIR / "raw_product_input.md"

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.4")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
EXECUTION_BACKEND = os.getenv("EXECUTION_BACKEND", "browser").lower()
BROWSER_CDP_URL = os.getenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
BROWSER_CHAT_URL = os.getenv("BROWSER_CHAT_URL", "https://chatgpt.com/")
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))

TRACE_ID = ""
SPAN_COUNTER = 0
RUN_START_TIME = 0.0
TERMINAL_EVENT_EMITTED = False
LAST_PROGRESS_PERCENT = -1
LOG_SEQUENCE = 0
SYNTHETIC_DURATION_MS = 0
DETERMINISTIC_TIME_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)

TEXT_STEP_WAIT_SECONDS = int(os.getenv("TEXT_STEP_WAIT_SECONDS", "0"))
IMAGE_STEP_WAIT_SECONDS = int(os.getenv("IMAGE_STEP_WAIT_SECONDS", "0"))


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


class BrowserPromptExecutionAdapter(PromptExecutionAdapter):
    def __init__(
        self,
        cdp_url: str,
        chat_url: str,
        action_timeout_ms: int,
        image_fallback: Optional[PromptExecutionAdapter] = None,
    ) -> None:
        self.cdp_url = cdp_url
        self.chat_url = chat_url
        self.action_timeout_ms = action_timeout_ms
        self.image_fallback = image_fallback
        self._playwright = None
        self._browser = None
        self._context = None
        self._page_obj = None
        self._prepared_chat = False

    def _page(self):
        reuse_page = os.getenv("BROWSER_REUSE_PAGE", "1") == "1"

        if self._browser is None:
            self._playwright = sync_playwright().start()
            try:
                self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
            except Exception:
                if "localhost" in self.cdp_url:
                    alt = self.cdp_url.replace("localhost", "127.0.0.1")
                    self._browser = self._playwright.chromium.connect_over_cdp(alt)
                    self.cdp_url = alt
                else:
                    raise

            # Prefer an existing (already-authenticated) context/page that is already on ChatGPT.
            chosen_context = None
            chosen_page = None
            for ctx in self._browser.contexts:
                for p in ctx.pages:
                    if self.chat_url and self.chat_url in (p.url or ""):
                        chosen_context = ctx
                        chosen_page = p
                        break
                if chosen_context is not None:
                    break

            self._context = chosen_context or (self._browser.contexts[0] if self._browser.contexts else self._browser.new_context())
            if reuse_page:
                self._page_obj = chosen_page or (self._context.pages[0] if self._context.pages else self._context.new_page())

        if reuse_page:
            if self._page_obj is None:
                self._page_obj = self._context.pages[0] if self._context.pages else self._context.new_page()
            page = self._page_obj
        else:
            page = self._context.new_page()

        page.bring_to_front()
        if self.chat_url and self.chat_url not in (page.url or ""):
            page.goto(self.chat_url, wait_until="domcontentloaded")
        return page

    def _start_new_chat(self, page) -> None:
        # Best-effort "new chat" without opening more tabs.
        old_url = ""
        try:
            old_url = page.url or ""
        except Exception:
            old_url = ""

        selectors = [
            "button[data-testid='new-chat-button']",
            "a[data-testid='new-chat-button']",
            "button:has-text('New chat')",
            "a:has-text('New chat')",
            "button[aria-label*='New chat']",
            "a[aria-label*='New chat']",
        ]
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.click()
                    break
            except Exception:
                pass

        # Fallback: navigate to the root (often lands in a fresh composer state).
        # Also: if the click didn't work (or there's no sidebar), force-navigation helps.
        deadline = time.time() + 5.0
        while time.time() < deadline:
            try:
                if old_url and page.url and page.url != old_url:
                    break
            except Exception:
                pass
            try:
                box = page.locator("textarea#prompt-textarea, [contenteditable='true']").first
                if box.count() and box.is_visible():
                    break
            except Exception:
                pass
            page.wait_for_timeout(200)

        try:
            # If we're still on a conversation URL, force to home to ensure a clean chat.
            if "/c/" in (page.url or ""):
                page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        except Exception:
            pass
        page.wait_for_timeout(500)

    def _input_box(self, page):
        selectors = [
            "textarea#prompt-textarea",
            "textarea[data-testid='prompt-textarea']",
            "[contenteditable='true']",
        ]
        last_exc: Optional[Exception] = None
        for sel in selectors:
            try:
                box = page.locator(sel).first
                box.wait_for(timeout=self.action_timeout_ms)
                if box.is_visible():
                    return box
            except Exception as e:
                last_exc = e
        if last_exc is not None:
            raise last_exc
        fail("SELECTOR_TIMEOUT", "Could not find ChatGPT input box.")

    def send_prompt(self, page, payload: str) -> str:
        before_assistant_count = page.locator("[data-message-author-role='assistant']").count()
        before_user_count = page.locator("[data-message-author-role='user']").count()
        before_last_assistant_text = ""
        try:
            if before_assistant_count > 0:
                before_last_assistant_text = page.locator("[data-message-author-role='assistant']").last.inner_text(timeout=5000).strip()
        except Exception:
            before_last_assistant_text = ""
        box = self._input_box(page)

        box.click()
        try:
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass
        try:
            box.fill(payload, timeout=self.action_timeout_ms)
        except Exception:
            try:
                page.keyboard.insert_text(payload)
            except Exception:
                box.type(payload, delay=0, timeout=self.action_timeout_ms)

        def try_click_send() -> bool:
            selectors = [
                "button[data-testid='send-button']",
                "button[aria-label*='Send']",
                "button[aria-label*='send']",
                "button:has-text('Send')",
            ]
            for sel in selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() and btn.is_visible() and btn.is_enabled():
                        btn.click()
                        return True
                except Exception:
                    pass
            try:
                btn = page.get_by_role("button", name=re.compile(r"send", re.I)).first
                if btn.count() and btn.is_visible() and btn.is_enabled():
                    btn.click()
                    return True
            except Exception:
                pass
            return False

        # Ensure the prompt is actually submitted (some UI states require clicking send
        # or using Ctrl+Enter).
        page.keyboard.press("Enter")
        send_deadline = time.time() + 15.0
        ctrl_enter_tried = False
        while time.time() < send_deadline:
            if page.locator("[data-message-author-role='user']").count() > before_user_count:
                break
            try:
                if not ctrl_enter_tried:
                    page.keyboard.press("Control+Enter")
                    ctrl_enter_tried = True
            except Exception:
                pass
            try_click_send()
            page.wait_for_timeout(250)

        # Wait for a new assistant message to appear (response started).
        response_deadline = time.time() + (self.action_timeout_ms / 1000.0)
        while time.time() < response_deadline:
            assistant_count = page.locator("[data-message-author-role='assistant']").count()
            if assistant_count > before_assistant_count:
                break
            try:
                if assistant_count > 0:
                    current_last = page.locator("[data-message-author-role='assistant']").last.inner_text(timeout=5000).strip()
                    if before_last_assistant_text and current_last and current_last != before_last_assistant_text:
                        break
            except Exception:
                pass
            try:
                stop_btn = page.get_by_role("button", name=re.compile(r"stop generating", re.I)).first
                if stop_btn.count() and stop_btn.is_visible():
                    break
            except Exception:
                pass
            page.wait_for_timeout(250)

        if page.locator("[data-message-author-role='assistant']").count() <= before_assistant_count:
            fail(
                "SELECTOR_TIMEOUT",
                "Timed out waiting for assistant response in browser.",
                field="browser",
                expected="new assistant message",
                actual=f"assistant_count={before_assistant_count} url={page.url}",
            )

        assistant = page.locator("[data-message-author-role='assistant']").last
        assistant.wait_for(timeout=self.action_timeout_ms)
        # Wait for streaming to settle to avoid capturing partial (invalid) JSON.
        stable_required = 3
        stable_count = 0
        last_text = ""
        deadline = time.time() + (self.action_timeout_ms / 1000.0)
        while time.time() < deadline:
            # Expand collapsed assistant content if present.
            try:
                show_more = assistant.get_by_role("button", name=re.compile(r"show more", re.I)).first
                if show_more.count() and show_more.is_visible():
                    show_more.click()
                    stable_count = 0
                    page.wait_for_timeout(250)
            except Exception:
                pass

            # If the model stopped early, ask it to continue.
            try:
                cont = page.get_by_role("button", name=re.compile(r"continue generating", re.I)).first
                if cont.count() and cont.is_visible():
                    cont.click()
                    stable_count = 0
                    page.wait_for_timeout(500)
            except Exception:
                pass

            current = assistant.inner_text(timeout=self.action_timeout_ms).strip()
            if current and current == last_text:
                stable_count += 1
                if stable_count >= stable_required:
                    return current
            else:
                stable_count = 0
                last_text = current
            page.wait_for_timeout(500)
        return last_text.strip()

    def execute_text(self, step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        page = self._page()
        # By default: start a fresh chat for every prompt (same tab) to avoid context bleed.
        if os.getenv("BROWSER_NEW_CHAT_EACH_PROMPT", "1") == "1":
            self._start_new_chat(page)
        elif not self._prepared_chat and os.getenv("BROWSER_NEW_CHAT", "1") == "1":
            self._start_new_chat(page)
            self._prepared_chat = True
        payload = build_text_input(state, prompt_text)
        response_text = self.send_prompt(page, payload)
        if not response_text:
            fail("EMPTY_MODEL_OUTPUT", f"Step {step_id} returned empty browser output.")
        return parse_response_json(response_text)

    def execute_image(self, prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
        if self.image_fallback is None:
            # Delay OpenAI client initialization until image generation is requested so
            # browser-backed text steps don't require OPENAI_API_KEY.
            self.image_fallback = OpenAIPromptExecutionAdapter(OpenAI())
        return self.image_fallback.execute_image(prompt, size=size)


client: Optional[OpenAI] = None
EXECUTION_ADAPTER: Optional[PromptExecutionAdapter] = None


def get_execution_adapter() -> PromptExecutionAdapter:
    global client, EXECUTION_ADAPTER
    if EXECUTION_ADAPTER is None:
        if EXECUTION_BACKEND == "browser":
            EXECUTION_ADAPTER = BrowserPromptExecutionAdapter(
                BROWSER_CDP_URL,
                BROWSER_CHAT_URL,
                BROWSER_ACTION_TIMEOUT_MS,
            )
        else:
            if client is None:
                client = OpenAI()
            EXECUTION_ADAPTER = OpenAIPromptExecutionAdapter(client)
    return EXECUTION_ADAPTER


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

    LOG_SEQUENCE += 1


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
    text = re.sub(r"^(?:JSON|json)\s*[:\-]?\s*\n", "", text)
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def repair_unescaped_quotes(json_text: str) -> str:
    """
    Best-effort repair for common browser-LLM failures where a quote character
    appears inside a JSON string value (e.g. inch marks like 2.4") without being escaped.
    This is a heuristic: treat a quote inside a string as a terminator only if
    the next non-whitespace character is a valid JSON delimiter.
    """
    out: List[str] = []
    in_string = False
    escape = False

    for idx, ch in enumerate(json_text):
        if not in_string:
            out.append(ch)
            if ch == '"':
                in_string = True
            continue

        # in_string
        if escape:
            out.append(ch)
            escape = False
            continue

        if ch == "\\":
            out.append(ch)
            escape = True
            continue

        if ch == '"':
            j = idx + 1
            while j < len(json_text) and json_text[j] in " \t\r\n":
                j += 1
            if j >= len(json_text) or json_text[j] in [",", ":", "}", "]"]:
                out.append(ch)
                in_string = False
            else:
                out.append('\\"')
            continue

        out.append(ch)

    return "".join(out)


def repair_common_json_glitches(json_text: str) -> str:
    # Fix the common inch-mark issue that breaks JSON strings, e.g.:
    # "sensor": "SONY Exmor IMX323 (1/2.9", 2.8µ pixel)"
    # becomes:
    # "sensor": "SONY Exmor IMX323 (1/2.9 inches, 2.8µ pixel)"
    json_text = re.sub(r'(\d)"\s*,\s*(\d)', r"\1 inches, \2", json_text)
    return json_text


def parse_response_json(response_text: str) -> Dict[str, Any]:
    excerpt = normalize_json_text(response_text)
    try:
        return json.loads(excerpt)
    except Exception:
        repaired = repair_common_json_glitches(excerpt)
        repaired = repair_unescaped_quotes(repaired)
        try:
            return json.loads(repaired)
        except Exception as e:
            fail(
                "MODEL_OUTPUT_NOT_JSON",
                f"Model output is not valid JSON: {e}",
                actual=excerpt[:2000],
            )


def workflow_state_init() -> Dict[str, Any]:
    raw_text_path = resolve_raw_text_path()
    return {
        "reference_tag": "",
        "trace_id": TRACE_ID,
        "script_metadata": SCRIPT_METADATA,
        "source": {
            "raw_text_path": str(raw_text_path),
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

    prompt_from_md = read_prompt_from_prompts_md(step_id)
    if prompt_from_md is not None:
        return prompt_from_md

    fail("MISSING_PROMPT", f"No prompt file found for step {step_id} in {PROMPTS_DIR}")


def _normalize_prompt_key(step_id: str) -> str:
    """
    Normalize internal step ids (e.g. '01A') to prompts.md keys (e.g. '1A').
    prompts.md uses headings like '# PROMPT 1A', '# PROMPT 2', ... '# PROMPT 24'.
    """
    m = re.match(r"^0*(\d+)([A-Za-z]?)$", step_id.strip())
    if not m:
        stripped = step_id.strip().lstrip("0")
        return (stripped or step_id.strip()).upper()
    number = str(int(m.group(1)))
    suffix = m.group(2).upper()
    return f"{number}{suffix}"


_PROMPT_HEADING_RE = re.compile(r"(?m)^#\s+PROMPT\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)
_PROMPTS_MD_CACHE: Optional[Dict[str, str]] = None


def _load_prompts_md_sections() -> Dict[str, str]:
    if not PROMPTS_MD_PATH.exists():
        return {}
    text = PROMPTS_MD_PATH.read_text(encoding="utf-8")
    matches = list(_PROMPT_HEADING_RE.finditer(text))
    if not matches:
        return {}
    sections: Dict[str, str] = {}
    for idx, m in enumerate(matches):
        key = m.group(1).strip().replace(" ", "").upper()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[key] = text[start:end].strip()
    return sections


def read_prompt_from_prompts_md(step_id: str) -> Optional[str]:
    """
    Fallback prompt loader for repos that store prompt content in docs/prompts.md
    instead of individual files under docs/prompts/.
    """
    global _PROMPTS_MD_CACHE
    if _PROMPTS_MD_CACHE is None:
        _PROMPTS_MD_CACHE = _load_prompts_md_sections()

    if not _PROMPTS_MD_CACHE:
        return None

    key = _normalize_prompt_key(step_id).replace(" ", "").upper()
    body = _PROMPTS_MD_CACHE.get(key)
    if body is None:
        return None

    fence = _FENCE_RE.search(body)
    if fence:
        return fence.group(1).strip()
    return body.strip()


def build_text_input(state: Dict[str, Any], prompt_text: str) -> str:
    compact_state = json.dumps(state, ensure_ascii=False, indent=2)
    return (
        f"WORKFLOW_STATE_JSON:\n{compact_state}\n\n"
        f"INSTRUCTIONS:\n{prompt_text}\n\n"
        f"OUTPUT RULES:\nReturn only valid JSON."
    )


def call_text_step(step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    json_log("step_start", step_id=step_id, kind="text")
    parsed = get_execution_adapter().execute_text(step_id, prompt_text, schema, state)
    json_log("step_end", step_id=step_id, kind="text", output_keys=list(parsed.keys()))
    return parsed


def call_image_generation(prompt: str, size: str = "1024x1536") -> Dict[str, Any]:
    json_log("step_start", kind="image_generation", size=size)
    return get_execution_adapter().execute_image(prompt, size=size)


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

def build_step_plan(*, enable_image_generation: bool) -> List[Step]:
    if enable_image_generation:
        return list(STEP_PLAN)
    return [s for s in STEP_PLAN if s.kind != "image_generate"]


def write_image_prompts(state: Dict[str, Any]) -> None:
    prompts: List[Dict[str, Any]] = []
    for n in range(1, 8):
        key = f"image_strategy_{n}"
        container = state.get(key)
        if isinstance(container, dict) and isinstance(container.get("image_strategy"), dict):
            prompts.append(container["image_strategy"])
    if prompts:
        IMAGE_PROMPTS_PATH.write_text(json.dumps(prompts, indent=2, ensure_ascii=False), encoding="utf-8")


def run_step(step: Step, state: Dict[str, Any]) -> None:
    def build_schema() -> Dict[str, Any]:
        if not step.schema_builder:
            return {}
        try:
            if len(inspect.signature(step.schema_builder).parameters) == 0:
                return step.schema_builder()  # type: ignore[misc]
        except Exception:
            pass
        return step.schema_builder(state)  # type: ignore[misc]

    if step.kind == "text":
        prompt_text = read_prompt_file(step.step_id)
        schema = build_schema()
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
        if not os.getenv("OPENAI_API_KEY") and os.getenv("SKIP_IMAGES", "0") != "0":
            fail(
                "IMAGE_GENERATION_DISABLED",
                "Image generation is disabled. Use prompt-only mode (default) or pass --enable-image-generation with OPENAI_API_KEY.",
            )
        if os.getenv("SKIP_IMAGES", "0") == "1":
            output = {
                "reference_tag": state["reference_tag"],
                "generated_image": {"skipped": True, "reason": "SKIP_IMAGES=1"},
                "image_style_lock": deterministic_style_lock(),
            }
            update_state_with_prompt(state, step.step_id, output, step.output_key)
            state["image_style_lock"] = output["image_style_lock"]
            save_json_atomic(STATE_PATH, state)
            apply_step_wait(step.kind)
            return

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
    raw_text_path = resolve_raw_text_path()
    if not raw_text_path.exists():
        fail("MISSING_INPUT", f"Missing raw text input: {RAW_TEXT_PATH} (or {RAW_TEXT_PATH_MD})")
    if not IMAGE_SOURCE_DIR.exists():
        fail("MISSING_INPUT", f"Missing image source directory: {IMAGE_SOURCE_DIR}")
    if len(read_source_images()) == 0:
        fail("MISSING_IMAGES", "No source images found in data/images/")
    if not PROMPTS_DIR.exists():
        fail("MISSING_PROMPTS", f"Missing prompts directory: {PROMPTS_DIR}")


def resolve_raw_text_path() -> Path:
    if RAW_TEXT_PATH.exists():
        return RAW_TEXT_PATH
    if RAW_TEXT_PATH_MD.exists():
        return RAW_TEXT_PATH_MD
    return RAW_TEXT_PATH


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
    parser.add_argument(
        "--enable-image-generation",
        action="store_true",
        help="Enable image generation steps (requires OPENAI_API_KEY). Default is prompt-only.",
    )
    args = parser.parse_args()

    ensure_dirs()
    if not args.resume:
        (LOG_DIR / "execution.jsonl").write_text("", encoding="utf-8")

    state = load_json(STATE_PATH) if args.resume and STATE_PATH.exists() else workflow_state_init()
    state.setdefault("reference_tag", "")
    state.setdefault("outputs", {})

    validate_initial_inputs()

    raw_text_path = resolve_raw_text_path()
    raw_text_hash = hashlib.sha256(raw_text_path.read_bytes()).hexdigest()
    image_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in read_source_images()]

    global TRACE_ID
    TRACE_ID = build_deterministic_trace_id(raw_text_hash, image_hashes)
    state["trace_id"] = TRACE_ID

    plan = build_step_plan(enable_image_generation=bool(args.enable_image_generation))
    total_steps = len(plan)

    emit_lifecycle_event(
        stage="INIT",
        status="STARTED",
        message="Orchestrator initialization started",
        progress_percent=0,
        current_step=0,
        total_steps=total_steps,
    )

    emit_lifecycle_event(
        stage="VALIDATED",
        status="COMPLETED",
        message="Input validation completed",
        progress_percent=0,
        current_step=0,
        total_steps=total_steps,
    )

    state["input_fingerprint"] = {
        "raw_text_sha256": raw_text_hash,
        "image_sha256": image_hashes,
    }

    state["source_payload"] = {
        "raw_text": load_text(raw_text_path),
        "source_images": [str(p) for p in read_source_images()],
    }

    save_json_atomic(STATE_PATH, state)

    emit_lifecycle_event(
        stage="PROCESSING",
        status="STARTED",
        message="Workflow processing started",
        progress_percent=0,
        current_step=0,
        total_steps=total_steps,
    )

    start_from = 0
    if args.resume and state.get("last_completed_step"):
        last_step = str(state["last_completed_step"])
        for i, step in enumerate(plan):
            if step.step_id == last_step:
                start_from = i + 1
                break

    for i in range(start_from, len(plan)):
        step = plan[i]
        current_step_number = i + 1
        if args.stop_after and step.step_id == args.stop_after:
            break
        run_step(step, state)
        progress_percent = min(100, int((current_step_number / len(plan)) * 100))
        validate_progress_percent(progress_percent, current_step_number, len(plan))
        json_log(
            level="INFO",
            message=f"Completed step {step.step_id}",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"step_id": step.step_id},
            progress_percent=progress_percent,
            current_step=current_step_number,
            total_steps=len(plan),
        )

    save_json_atomic(STATE_PATH, state)
    write_image_prompts(state)

    output_hash = hashlib.sha256(STATE_PATH.read_bytes()).hexdigest()
    emit_lifecycle_event(
        stage="COMPLETED",
        status="SUCCESS",
        message="Workflow completed successfully",
        progress_percent=100,
        current_step=len(plan),
        total_steps=len(plan),
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
