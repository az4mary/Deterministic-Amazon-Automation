# workflow_orchestrator.py
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import logging
import os
import subprocess
import re
import inspect
import linecache
import sys
import time
from datetime import datetime, timezone, timedelta
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from openai import OpenAI  # type: ignore
except ModuleNotFoundError:
    OpenAI = None  # type: ignore
from playwright.sync_api import sync_playwright

SCRIPT_METADATA = {
    "script_id": "SCRIPT_002",
    "name": "workflow_orchestrator",
    "version": "1.1",
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
IMAGE_CONTENT_PATH = OUTPUT_DIR / "image_content.json"
RAW_TEXT_PATH = DATA_DIR / "raw_product_input.txt"
RAW_TEXT_PATH_MD = DATA_DIR / "raw_product_input.md"

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.4")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1.5")
IMAGE_REFERENCE_STRICT = os.getenv("IMAGE_REFERENCE_STRICT", "1") == "1"
EXECUTION_BACKEND = os.getenv("EXECUTION_BACKEND", "browser").lower()
BROWSER_CDP_URL = os.getenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
BROWSER_CHAT_URL = os.getenv("BROWSER_CHAT_URL", "https://chatgpt.com/")
BROWSER_ACTION_TIMEOUT_MS = int(os.getenv("BROWSER_ACTION_TIMEOUT_MS", "120000"))
BROWSER_SELECTOR_TIMEOUT_MS = int(os.getenv("BROWSER_SELECTOR_TIMEOUT_MS", "5000"))
BROWSER_COMPOSER_READY_TIMEOUT_MS = int(os.getenv("BROWSER_COMPOSER_READY_TIMEOUT_MS", "30000"))
BROWSER_SELECTOR_POLL_MS = int(os.getenv("BROWSER_SELECTOR_POLL_MS", "500"))
BROWSER_RESPONSE_STABLE_REQUIRED = int(os.getenv("BROWSER_RESPONSE_STABLE_REQUIRED", "2"))
BROWSER_RESPONSE_STABILIZE_SECONDS = float(os.getenv("BROWSER_RESPONSE_STABILIZE_SECONDS", "180"))
BROWSER_REQUIRE_JSON_CANDIDATE = os.getenv("BROWSER_REQUIRE_JSON_CANDIDATE", "1") == "1"
BROWSER_REQUIRE_PARSEABLE_JSON = os.getenv("BROWSER_REQUIRE_PARSEABLE_JSON", "1") == "1"
BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS = float(os.getenv("BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS", "300"))
BROWSER_NEW_CHAT_READY_TIMEOUT_MS = int(os.getenv("BROWSER_NEW_CHAT_READY_TIMEOUT_MS", "30000"))
BROWSER_FORCE_ROOT_NEW_CHAT = os.getenv("BROWSER_FORCE_ROOT_NEW_CHAT", "1") == "1"
IMAGE_EXECUTION_BACKEND = os.getenv("IMAGE_EXECUTION_BACKEND", "chatgpt_browser").lower()
FLOW_URL = os.getenv("FLOW_URL", "https://labs.google/fx/tools/flow")
FLOW_IMAGE_MODEL = os.getenv("FLOW_IMAGE_MODEL", "Nano Banana 2")
FLOW_MODEL_STRICT = os.getenv("FLOW_MODEL_STRICT", "1") == "1"
FLOW_IMAGE_TIMEOUT_SECONDS = float(os.getenv("FLOW_IMAGE_TIMEOUT_SECONDS", "1200"))
FLOW_REFERENCE_STRICT = os.getenv("FLOW_REFERENCE_STRICT", "1") == "1"
FLOW_ASPECT_RATIO = os.getenv("FLOW_ASPECT_RATIO", "9:16")
FLOW_OUTPUT_COUNT = int(os.getenv("FLOW_OUTPUT_COUNT", "1"))
FLOW_UI_CLICK_TIMEOUT_MS = int(os.getenv("FLOW_UI_CLICK_TIMEOUT_MS", "10000"))
FLOW_REFERENCE_COMPOSER_TIMEOUT_SECONDS = float(os.getenv("FLOW_REFERENCE_COMPOSER_TIMEOUT_SECONDS", "90"))
FLOW_PROMPT_READY_TIMEOUT_SECONDS = float(os.getenv("FLOW_PROMPT_READY_TIMEOUT_SECONDS", "90"))
FLOW_GALLERY_ATTACH_TIMEOUT_SECONDS = float(os.getenv("FLOW_GALLERY_ATTACH_TIMEOUT_SECONDS", "120"))
FLOW_SUBMIT_CONFIRM_TIMEOUT_SECONDS = float(os.getenv("FLOW_SUBMIT_CONFIRM_TIMEOUT_SECONDS", "45"))
FLOW_REFERENCE_ATTACH_STRICT = os.getenv("FLOW_REFERENCE_ATTACH_STRICT", "1") == "1"
FLOW_CLIPBOARD_PASTE_WAIT_SECONDS = float(os.getenv("FLOW_CLIPBOARD_PASTE_WAIT_SECONDS", "6"))
FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS = float(os.getenv("FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS", "3"))
FLOW_REFERENCE_ATTACH_METHOD = os.getenv("FLOW_REFERENCE_ATTACH_METHOD", "clipboard").lower()

TRACE_ID = ""
SPAN_COUNTER = 0
RUN_START_TIME = 0.0
TERMINAL_EVENT_EMITTED = False
LAST_PROGRESS_PERCENT = -1
LOG_SEQUENCE = 0
SYNTHETIC_DURATION_MS = 0
DETERMINISTIC_TIME_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)

TEXT_STEP_WAIT_SECONDS = int(os.getenv("TEXT_STEP_WAIT_SECONDS", "300"))
IMAGE_STEP_WAIT_SECONDS = int(os.getenv("IMAGE_STEP_WAIT_SECONDS", "600"))

IMAGE_PROMPT_STEP_IDS = {"11", "13", "15", "17", "19", "21", "23"}
IMAGE_GENERATION_STEP_IDS = {"12", "14", "16", "18", "20", "22", "24"}

PATCH_SET_12_REQUIRED_MARKERS = [
    "FlowBrowserImageGenerationAdapter",
    "FLOW_IMAGE_MODEL",
    "FLOW_MODEL_STRICT",
    "Flow model selection started",
    "FLOW_MODEL_NOT_AVAILABLE",
    "generation_model",
    "IMAGE_EXECUTION_BACKEND",
    "get_image_execution_adapter",
    "FLOW_URL",
    "FLOW_REFERENCE_STRICT",
    "generation_backend",
]

PATCH_SET_12_FORBIDDEN_CHANGE_DESCRIPTIONS = [
    "renumbered image steps",
    "removed spatial_scene_brief",
    "changed prompt docs",
    "changed cooldown defaults",
    "routed image_prompt steps to Flow",
]


def build_patch_set_12_static_diagnostics() -> Dict[str, Any]:
    return {
        "patch_set_id": "PATCH_SET_12",
        "required_markers": PATCH_SET_12_REQUIRED_MARKERS,
        "forbidden_change_descriptions": PATCH_SET_12_FORBIDDEN_CHANGE_DESCRIPTIONS,
        "image_prompt_steps": sorted(IMAGE_PROMPT_STEP_IDS),
        "actual_image_generation_steps": sorted(IMAGE_GENERATION_STEP_IDS),
        "image_execution_backend": IMAGE_EXECUTION_BACKEND,
        "flow_url": FLOW_URL,
        "flow_reference_strict": FLOW_REFERENCE_STRICT,
    }

IMAGE_TASKS: Dict[str, Dict[str, Any]] = {
    "11": {
        "image_number": 1,
        "image_type": "Hero Product Image",
        "buyer_question": "What is this product?",
        "focus": "product identity, visual accuracy, included accessories, Amazon hero image compliance",
    },
    "13": {
        "image_number": 2,
        "image_type": "Core Benefit Image",
        "buyer_question": "Why do I need it?",
        "focus": "top customer-facing benefits and product value",
    },
    "15": {
        "image_number": 3,
        "image_type": "Problem Solution Image",
        "buyer_question": "What problem does this product solve?",
        "focus": "problem-to-solution mapping using verified features only",
    },
    "17": {
        "image_number": 4,
        "image_type": "Lifestyle Use Image",
        "buyer_question": "When would I use it?",
        "focus": "realistic use cases and safe lifestyle context",
    },
    "19": {
        "image_number": 5,
        "image_type": "Technology Feature Image",
        "buyer_question": "What technology makes it better?",
        "focus": "verified technical capabilities only",
    },
    "21": {
        "image_number": 6,
        "image_type": "Ease of Use / Installation Image",
        "buyer_question": "How easy is it to install or use?",
        "focus": "setup steps, included setup accessories, user workflow",
    },
    "23": {
        "image_number": 7,
        "image_type": "Specifications Infographic",
        "buyer_question": "What specifications matter?",
        "focus": "most relevant verified specifications for purchase decision",
    },
}


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

    def execute_image(
        self,
        prompt: str,
        size: str = "1024x1536",
        generation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
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

    def execute_image(
        self,
        prompt: str,
        size: str = "1024x1536",
        generation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        source_images: List[str] = []
        missing_images: List[str] = []

        if isinstance(generation_context, dict):
            raw_source_images = generation_context.get("source_images") or []
            if isinstance(raw_source_images, list):
                for item in raw_source_images:
                    if not isinstance(item, str):
                        continue
                    path = Path(item)
                    if path.exists() and path.is_file():
                        source_images.append(str(path))
                    else:
                        missing_images.append(item)

        if missing_images and IMAGE_REFERENCE_STRICT:
            fail(
                "IMAGE_REFERENCE_IMAGE_MISSING",
                "One or more reference images listed in generation_context.source_images do not exist.",
                field="generation_context.source_images",
                expected="all listed reference image paths exist",
                actual=json.dumps(missing_images, ensure_ascii=False),
                stage="PROCESSING",
            )

        if isinstance(generation_context, dict) and IMAGE_REFERENCE_STRICT and not source_images:
            fail(
                "IMAGE_REFERENCE_IMAGES_NOT_AVAILABLE",
                "Strict image generation requires source_images at the adapter boundary.",
                field="generation_context.source_images",
                expected="at least one existing reference image path",
                actual=str(generation_context.get("source_images")),
                stage="PROCESSING",
            )

        if source_images:
            json_log(
                level="INFO",
                message="OpenAI image edit requested with reference images",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "openai_image_edit",
                    "source_image_count": len(source_images),
                    "image_model": IMAGE_MODEL,
                    "size": size,
                },
            )

            files = []
            try:
                for image_path in source_images:
                    files.append(open(image_path, "rb"))

                response = self.client.images.edit(
                    model=IMAGE_MODEL,
                    image=files,
                    prompt=prompt,
                    size=size,
                    n=1,
                )
            finally:
                for f in files:
                    try:
                        f.close()
                    except Exception:
                        pass

            data = getattr(response, "data", None) or []
            if not data:
                fail("IMAGE_GENERATION_FAILED", "No image returned by image edit model.", stage="PROCESSING")

            first = data[0]
            image_base64 = getattr(first, "b64_json", None)
            revised_prompt = getattr(first, "revised_prompt", None)

            if isinstance(first, dict):
                image_base64 = image_base64 or first.get("b64_json")
                revised_prompt = revised_prompt or first.get("revised_prompt")

            if not image_base64:
                fail(
                    "IMAGE_GENERATION_FAILED",
                    "Image edit model returned no base64 image payload.",
                    field="image_base64",
                    expected="b64_json",
                    actual=str(first)[:1000],
                    stage="PROCESSING",
                )

            return {
                "image_base64": image_base64,
                "revised_prompt": revised_prompt,
                "source_images_used": source_images,
            }

        json_log(
            level="WARNING",
            message="OpenAI image generation requested without reference images",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "openai_image_generate_without_references",
                "image_model": IMAGE_MODEL,
                "size": size,
                "strict": IMAGE_REFERENCE_STRICT,
            },
        )

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
            fail("IMAGE_GENERATION_FAILED", "No image returned by model.", stage="PROCESSING")
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

    def _composer_available(self, page) -> bool:
        selectors = [
            "[contenteditable='true']",
            "div[contenteditable='true']",
            "[role='textbox']",
            "div[role='textbox']",
            "main [contenteditable='true']",
            "form [contenteditable='true']",
            "textarea#prompt-textarea",
            "textarea[data-testid='prompt-textarea']",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    return True
            except Exception:
                pass
        return False

    def _wait_for_clean_composer(self, page, *, reason: str) -> bool:
        deadline = time.time() + (BROWSER_NEW_CHAT_READY_TIMEOUT_MS / 1000.0)
        last_log = 0.0

        while time.time() < deadline:
            if self._composer_available(page):
                json_log(
                    level="DEBUG",
                    message="Browser clean composer ready",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "browser_clean_composer_ready",
                        "reason": reason,
                        "url": getattr(page, "url", ""),
                    },
                )
                return True

            now = time.time()
            if now - last_log >= 2.0:
                last_log = now
                json_log(
                    level="DEBUG",
                    message="Browser clean composer wait continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "browser_clean_composer_wait_continue",
                        "reason": reason,
                        "url": getattr(page, "url", ""),
                    },
                )

            page.wait_for_timeout(500)

        return False

    def _start_new_chat(self, page) -> None:
        # Establish a clean ChatGPT composer surface before every prompt.
        # This is intentionally stronger than a best-effort sidebar click because
        # generated-image/canvas result surfaces can leave the composer hidden.
        old_url = ""
        try:
            old_url = page.url or ""
        except Exception:
            old_url = ""

        json_log(
            level="DEBUG",
            message="Browser new chat reset started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_new_chat_reset_start",
                "old_url": old_url,
                "force_root": BROWSER_FORCE_ROOT_NEW_CHAT,
            },
        )

        # First dismiss transient UI layers that may trap focus after image generation.
        for key in ["Escape", "Escape"]:
            try:
                page.keyboard.press(key)
                page.wait_for_timeout(250)
            except Exception:
                pass

        # Prefer hard navigation to root when enabled. This is the most reliable
        # way to exit generated-image/canvas views and recover the normal composer.
        if BROWSER_FORCE_ROOT_NEW_CHAT:
            try:
                page.goto(self.chat_url or "https://chatgpt.com/", wait_until="domcontentloaded")
                page.wait_for_timeout(1000)
            except Exception as e:
                json_log(
                    level="DEBUG",
                    message="Browser root navigation for new chat failed",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "browser_root_navigation_failed",
                        "error": str(e)[:500],
                    },
                )

        if self._wait_for_clean_composer(page, reason="after_root_navigation"):
            return

        # Fallback: try the visible New Chat affordance.
        selectors = [
            "button[data-testid='new-chat-button']",
            "a[data-testid='new-chat-button']",
            "button:has-text('New chat')",
            "a:has-text('New chat')",
            "button[aria-label*='New chat']",
            "a[aria-label*='New chat']",
            "a[href='/']",
        ]

        for sel in selectors:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.click()
                    page.wait_for_timeout(1000)
                    if self._wait_for_clean_composer(page, reason=f"after_new_chat_click:{sel}"):
                        return
            except Exception:
                pass

        # Last resort: reload root and check again.
        try:
            page.goto(self.chat_url or "https://chatgpt.com/", wait_until="domcontentloaded")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
        except Exception:
            pass

        if self._wait_for_clean_composer(page, reason="after_root_reload"):
            return

        fail(
            "SELECTOR_TIMEOUT",
            "Could not recover clean ChatGPT composer after new-chat reset.",
            field="browser_clean_composer",
            expected="visible composer after root navigation/new chat reset",
            actual=f"old_url={old_url}; current_url={getattr(page, 'url', '')}",
            stage="PROCESSING",
        )

    def _attach_images_for_state(self, page, state: Dict[str, Any]) -> None:
        if os.getenv("BROWSER_ATTACH_IMAGES", "1") != "1":
            return
        payload = state.get("source_payload") or {}
        paths = payload.get("source_images") or []
        if not isinstance(paths, list) or not paths:
            return
        file_paths: List[str] = []
        for p in paths:
            if isinstance(p, str) and Path(p).exists():
                file_paths.append(p)
        if not file_paths:
            return

        max_files = int(os.getenv("BROWSER_ATTACH_MAX_FILES", "4"))
        file_paths = file_paths[:max_files]

        # Best-effort: set files on any file input.
        # Some ChatGPT builds hide the input behind an "Attach" button; try to reveal it.
        attach_selectors = [
            "button[aria-label*='Attach']",
            "button[aria-label*='attach']",
            "button:has-text('Attach')",
            "button[data-testid*='attach']",
        ]
        try:
            if page.locator("input[type=file]").count() == 0:
                for sel in attach_selectors:
                    btn = page.locator(sel).first
                    if btn.count() and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(250)
                        break
        except Exception:
            pass

        try:
            inp = page.locator("input[type=file]").first
            if inp.count():
                inp.set_input_files(file_paths, timeout=self.action_timeout_ms)
                page.wait_for_timeout(500)
        except Exception:
            # Non-fatal: the step can still proceed without attachments.
            pass

    def _input_box(self, page):
        selectors = [
            "[contenteditable='true']",
            "div[contenteditable='true']",
            "[role='textbox']",
            "div[role='textbox']",
            "main [contenteditable='true']",
            "form [contenteditable='true']",
            "textarea#prompt-textarea",
            "textarea[data-testid='prompt-textarea']",
        ]
        last_exc: Optional[Exception] = None
        deadline = time.time() + (BROWSER_COMPOSER_READY_TIMEOUT_MS / 1000.0)
        last_wait_log = 0.0

        json_log(
            level="DEBUG",
            message="Browser input composer wait started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "input_composer_wait_start",
                "url": getattr(page, "url", ""),
                "timeout_ms": BROWSER_COMPOSER_READY_TIMEOUT_MS,
            },
        )

        while time.time() < deadline:
            saw_candidate = False

            for sel in selectors:
                try:
                    box = page.locator(sel).first
                    count = box.count()
                    if count == 0:
                        continue

                    saw_candidate = True
                    remaining_ms = max(250, int((deadline - time.time()) * 1000))
                    wait_ms = min(BROWSER_SELECTOR_TIMEOUT_MS, remaining_ms)

                    box.wait_for(state="visible", timeout=wait_ms)
                    if box.is_visible():
                        json_log(
                            level="DEBUG",
                            message="Browser input selector matched",
                            stage="PROCESSING",
                            status="IN_PROGRESS",
                            context={
                                "operation": "input_selector_matched",
                                "selector": sel,
                                "url": getattr(page, "url", ""),
                            },
                        )
                        return box

                except Exception as e:
                    last_exc = e
                    json_log(
                        level="DEBUG",
                        message="Browser input selector skipped",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "input_selector_skipped",
                            "selector": sel,
                            "error": str(e)[:300],
                        },
                    )

            now = time.time()
            if now - last_wait_log >= 2.0:
                last_wait_log = now
                json_log(
                    level="DEBUG",
                    message="Browser input composer wait continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "input_composer_wait_continue",
                        "url": getattr(page, "url", ""),
                        "saw_candidate": saw_candidate,
                    },
                )

            page.wait_for_timeout(BROWSER_SELECTOR_POLL_MS)

        fail(
            "SELECTOR_TIMEOUT",
            "Could not find ChatGPT input box.",
            field="browser_input_box",
            expected="visible contenteditable, role textbox, or textarea composer before composer readiness timeout",
            actual=f"url={getattr(page, 'url', '')}; last_error={last_exc}",
            stage="PROCESSING",
        )

    def send_prompt(self, page, payload: str) -> str:
        json_log(
            level="DEBUG",
            message="Browser prompt send started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"operation": "send_prompt_start", "payload_chars": len(payload)},
        )
        before_assistant_count = page.locator("[data-message-author-role='assistant']").count()
        before_user_count = page.locator("[data-message-author-role='user']").count()
        before_last_assistant_text = ""
        try:
            if before_assistant_count > 0:
                before_last_assistant_text = page.locator("[data-message-author-role='assistant']").last.inner_text(timeout=5000).strip()
        except Exception:
            before_last_assistant_text = ""
        box = self._input_box(page)
        json_log(
            level="DEBUG",
            message="Browser input box resolved",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"operation": "input_box_resolved"},
        )

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
        json_log(
            level="DEBUG",
            message="Browser prompt submission attempted",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"operation": "prompt_submit_attempt"},
        )
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
        json_log(
            level="DEBUG",
            message="Browser assistant response wait started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "assistant_response_wait_start",
                "before_assistant_count": before_assistant_count,
                "before_user_count": before_user_count,
            },
        )
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
        json_log(
            level="DEBUG",
            message="Browser assistant response detected",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "assistant_response_detected",
                "assistant_count": page.locator("[data-message-author-role='assistant']").count(),
            },
        )
        # Wait for streaming to settle to avoid capturing partial (invalid) JSON.
        # This window starts only after an assistant response has been detected.
        # It must be shorter than the full browser action timeout so malformed JSON
        # can be captured, parsed, repaired, or retried instead of hanging at capture.
        stable_required = BROWSER_RESPONSE_STABLE_REQUIRED
        stable_count = 0
        last_text = ""
        deadline = time.time() + BROWSER_RESPONSE_STABILIZE_SECONDS
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
            if current:
                if not assistant_response_ready(current):
                    last_text = current
                    stable_count = 0
                    json_log(
                        level="DEBUG",
                        message="Browser assistant response not ready",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "assistant_response_not_ready",
                            "response_chars": len(current),
                            "response_excerpt": current[:120],
                            "requires_json_candidate": BROWSER_REQUIRE_JSON_CANDIDATE,
                            "requires_parseable_json": BROWSER_REQUIRE_PARSEABLE_JSON,
                            "has_json_candidate": has_json_candidate(current),
                        },
                    )
                    page.wait_for_timeout(500)
                    continue

                if current == last_text:
                    stable_count += 1
                    if stable_count >= stable_required:
                        json_log(
                            level="DEBUG",
                            message="Browser assistant response stabilized",
                            stage="PROCESSING",
                            status="IN_PROGRESS",
                            context={
                                "operation": "assistant_response_stabilized",
                                "response_chars": len(current),
                                "stable_count": stable_count,
                            },
                        )
                        return current
                else:
                    stable_count = 0
                    last_text = current
            page.wait_for_timeout(500)
        json_log(
            level="DEBUG",
            message="Browser assistant response stabilization ended by deadline",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "assistant_response_stabilization_deadline",
                "response_chars": len(last_text or ""),
            },
        )
        return last_text.strip()

    def execute_text(self, step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        json_log(
            level="DEBUG",
            message="Browser text execution started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"step_id": step_id, "operation": "execute_text_start"},
        )
        page = self._page()
        json_log(
            level="DEBUG",
            message="Browser page ready",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"step_id": step_id, "operation": "browser_page_ready", "url": getattr(page, "url", "")},
        )
        # By default: start a fresh chat for every prompt (same tab) to avoid context bleed.
        if os.getenv("BROWSER_NEW_CHAT_EACH_PROMPT", "1") == "1":
            self._start_new_chat(page)
        elif not self._prepared_chat and os.getenv("BROWSER_NEW_CHAT", "1") == "1":
            self._start_new_chat(page)
            self._prepared_chat = True

        # Step 01B requires actual image attachments to do real visual grounding.
        if step_id == "01B":
            self._attach_images_for_state(page, state)

        max_retries = int(os.getenv("BROWSER_JSON_RETRIES", "2"))
        payload = build_text_input(state, prompt_text)
        json_log(
            level="DEBUG",
            message="Browser payload built",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "step_id": step_id,
                "operation": "payload_built",
                "payload_chars": len(payload),
                "context_type": state.get("context_type", "WORKFLOW_STATE_JSON"),
            },
        )

        last_response = ""
        for attempt in range(max_retries + 1):
            json_log(
                level="DEBUG",
                message="Browser JSON attempt started",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "step_id": step_id,
                    "operation": "json_attempt_start",
                    "attempt": attempt,
                    "max_retries": max_retries,
                },
            )
            response_text = self.send_prompt(page, payload if attempt == 0 else _json_only_retry_prompt(step_id, schema, last_response))
            last_response = response_text
            json_log(
                level="DEBUG",
                message="Browser response received",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "step_id": step_id,
                    "operation": "browser_response_received",
                    "attempt": attempt,
                    "response_chars": len(response_text or ""),
                },
            )
            if not response_text:
                fail("EMPTY_MODEL_OUTPUT", f"Step {step_id} returned empty browser output.")
            parsed, err, excerpt = try_parse_response_json(response_text)
            if parsed is not None:
                json_log(
                    level="DEBUG",
                    message="Browser response parsed as JSON",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "step_id": step_id,
                        "operation": "json_parse_success",
                        "attempt": attempt,
                        "output_keys": list(parsed.keys()),
                    },
                )
                return parsed
            json_log(
                level="DEBUG",
                message="Browser response JSON parse failed",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "step_id": step_id,
                    "operation": "json_parse_failed",
                    "attempt": attempt,
                    "error": err,
                    "excerpt_chars": len(excerpt or ""),
                },
            )
            if attempt >= max_retries:
                fail(
                    "MODEL_OUTPUT_NOT_JSON",
                    f"Model output is not valid JSON: {err}",
                    actual=excerpt[:2000],
                )

        fail("MODEL_OUTPUT_NOT_JSON", "Model output is not valid JSON: exhausted retries.")

    def _extract_generation_source_images(
        self,
        generation_context: Optional[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
        source_images: List[str] = []
        missing_images: List[str] = []

        if isinstance(generation_context, dict):
            raw_source_images = generation_context.get("source_images") or []
            if isinstance(raw_source_images, list):
                for item in raw_source_images:
                    if not isinstance(item, str):
                        continue
                    path = Path(item)
                    if path.exists() and path.is_file():
                        source_images.append(str(path))
                    else:
                        missing_images.append(item)

        return source_images, missing_images

    def _attach_images_for_generation(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        json_log(
            level="INFO",
            message="Browser image generation reference attachment started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_image_reference_attach_start",
                "source_image_count": len(source_images),
            },
        )

        attach_selectors = [
            "button[aria-label*='Attach']",
            "button[aria-label*='attach']",
            "button:has-text('Attach')",
            "button[data-testid*='attach']",
        ]

        try:
            if page.locator("input[type=file]").count() == 0:
                for sel in attach_selectors:
                    btn = page.locator(sel).first
                    if btn.count() and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(250)
                        break
        except Exception:
            pass

        try:
            inp = page.locator("input[type=file]").first
            if not inp.count():
                fail(
                    "BROWSER_IMAGE_ATTACH_INPUT_MISSING",
                    "Could not find browser file input for image generation reference images.",
                    field="browser_file_input",
                    expected="input[type=file]",
                    actual=f"url={getattr(page, 'url', '')}",
                    stage="PROCESSING",
                )

            inp.set_input_files(source_images, timeout=self.action_timeout_ms)
            page.wait_for_timeout(1000)

            json_log(
                level="INFO",
                message="Browser image generation reference images attached",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "browser_image_reference_attach_success",
                    "source_image_count": len(source_images),
                },
            )
        except SystemExit:
            raise
        except Exception as e:
            fail(
                "BROWSER_IMAGE_REFERENCE_ATTACH_FAILED",
                "Failed to attach reference images for browser image generation.",
                field="generation_context.source_images",
                expected="reference images attached through browser file input",
                actual=str(e)[:1000],
                stage="PROCESSING",
            )

    def _submit_image_generation_prompt(self, page, prompt: str) -> int:
        before_assistant_count = page.locator("[data-message-author-role='assistant']").count()
        before_user_count = page.locator("[data-message-author-role='user']").count()

        box = self._input_box(page)
        json_log(
            level="DEBUG",
            message="Browser image prompt input box resolved",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={"operation": "browser_image_input_box_resolved"},
        )

        box.click()
        try:
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass

        try:
            box.fill(prompt, timeout=self.action_timeout_ms)
        except Exception:
            try:
                page.keyboard.insert_text(prompt)
            except Exception:
                box.type(prompt, delay=0, timeout=self.action_timeout_ms)

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

        json_log(
            level="INFO",
            message="Browser image generation prompt submission attempted",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_image_prompt_submit_attempt",
                "prompt_chars": len(prompt or ""),
            },
        )

        page.keyboard.press("Enter")
        send_deadline = time.time() + 20.0
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

        return before_assistant_count

    def _capture_latest_browser_generated_image_base64(self, page, before_assistant_count: int) -> str:
        deadline = time.time() + BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS
        last_assistant_excerpt = ""
        last_diag_log = 0.0

        def locator_key(locator) -> str:
            try:
                src = locator.get_attribute("src") or ""
            except Exception:
                src = ""
            try:
                alt = locator.get_attribute("alt") or ""
            except Exception:
                alt = ""
            try:
                box = locator.bounding_box() or {}
            except Exception:
                box = {}

            # Do not store full data URLs in the baseline key; only a stable prefix.
            if src.startswith("data:image"):
                src_key = src[:120]
            else:
                src_key = src

            return json.dumps(
                {
                    "src": src_key,
                    "alt": alt[:120],
                    "w": int(box.get("width", 0) or 0),
                    "h": int(box.get("height", 0) or 0),
                },
                sort_keys=True,
            )

        def visible_large_enough(locator) -> bool:
            try:
                if not locator.is_visible():
                    return False
            except Exception:
                return False

            try:
                box = locator.bounding_box() or {}
            except Exception:
                return False

            width = float(box.get("width", 0) or 0)
            height = float(box.get("height", 0) or 0)

            # Skip icons, avatars, buttons, and uploaded-reference thumbnails.
            return width >= 256 and height >= 256

        def collect_candidate_locators():
            locators = []

            selectors = [
                "[data-message-author-role='assistant'] img",
                "[data-message-author-role='assistant'] picture img",
                "[data-message-author-role='assistant'] canvas",
                "[data-message-author-role='assistant'] [role='img']",
                "article img",
                "article picture img",
                "article canvas",
                "main img[src^='blob:']",
                "main img[src^='data:image']",
                "main img[src*='oaiusercontent']",
                "main img[src*='oaidalleapiprodscus']",
                "main img[src*='openai']",
                "main canvas",
                "[role='img']",
            ]

            for sel in selectors:
                try:
                    collection = page.locator(sel)
                    count = min(collection.count(), 20)
                    for idx in range(count):
                        locators.append((sel, collection.nth(idx)))
                except Exception:
                    pass

            return locators

        baseline_keys = set()
        for _sel, candidate in collect_candidate_locators():
            try:
                if visible_large_enough(candidate):
                    baseline_keys.add(locator_key(candidate))
            except Exception:
                pass

        json_log(
            level="INFO",
            message="Browser image generation wait started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "browser_image_generation_wait_start",
                "timeout_seconds": BROWSER_IMAGE_GENERATION_TIMEOUT_SECONDS,
                "before_assistant_count": before_assistant_count,
                "baseline_large_image_count": len(baseline_keys),
            },
        )

        while time.time() < deadline:
            assistant_count = page.locator("[data-message-author-role='assistant']").count()

            if assistant_count > before_assistant_count:
                try:
                    assistant = page.locator("[data-message-author-role='assistant']").last
                    last_assistant_excerpt = assistant.inner_text(timeout=5000).strip()[:1000]
                except Exception:
                    last_assistant_excerpt = ""

            candidate_count = 0
            visible_large_count = 0
            skipped_baseline_count = 0

            for selector, candidate in collect_candidate_locators():
                candidate_count += 1

                try:
                    if not visible_large_enough(candidate):
                        continue

                    visible_large_count += 1
                    key = locator_key(candidate)

                    if key in baseline_keys:
                        skipped_baseline_count += 1
                        continue

                    # Give the rendered asset a brief moment to finish loading.
                    page.wait_for_timeout(1500)

                    src = ""
                    try:
                        src = candidate.get_attribute("src") or ""
                    except Exception:
                        src = ""

                    if src.startswith("data:image") and "," in src:
                        image_base64 = src.split(",", 1)[1]
                        json_log(
                            level="INFO",
                            message="Browser generated image captured from data URL",
                            stage="PROCESSING",
                            status="IN_PROGRESS",
                            context={
                                "operation": "browser_generated_image_captured_data_url",
                                "selector": selector,
                                "assistant_count": assistant_count,
                                "image_base64_chars": len(image_base64),
                            },
                        )
                        return image_base64

                    screenshot_bytes = candidate.screenshot(timeout=self.action_timeout_ms)
                    image_base64 = base64.b64encode(screenshot_bytes).decode("ascii")

                    json_log(
                        level="INFO",
                        message="Browser generated image captured from candidate locator",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "browser_generated_image_captured_candidate_screenshot",
                            "selector": selector,
                            "assistant_count": assistant_count,
                            "image_base64_chars": len(image_base64),
                        },
                    )
                    return image_base64

                except Exception as e:
                    json_log(
                        level="DEBUG",
                        message="Browser generated image candidate skipped",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "browser_generated_image_candidate_skipped",
                            "selector": selector,
                            "error": str(e)[:300],
                        },
                    )

            now = time.time()
            if now - last_diag_log >= 10.0:
                last_diag_log = now
                json_log(
                    level="DEBUG",
                    message="Browser image generation capture scan continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "browser_image_capture_scan_continue",
                        "assistant_count": assistant_count,
                        "candidate_count": candidate_count,
                        "visible_large_count": visible_large_count,
                        "skipped_baseline_count": skipped_baseline_count,
                        "last_assistant_excerpt": last_assistant_excerpt[:300],
                    },
                )

            try:
                stop_btn = page.get_by_role("button", name=re.compile(r"stop generating", re.I)).first
                if stop_btn.count() and stop_btn.is_visible():
                    page.wait_for_timeout(1000)
                    continue
            except Exception:
                pass

            page.wait_for_timeout(1000)

        fail(
            "BROWSER_IMAGE_GENERATION_TIMEOUT",
            "Timed out waiting for generated image in browser assistant response.",
            field="browser_generated_image",
            expected="visible generated image candidate captured from assistant/main image surface",
            actual=last_assistant_excerpt[:1000],
            stage="PROCESSING",
        )

    def execute_image(
        self,
        prompt: str,
        size: str = "1024x1536",
        generation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        source_images, missing_images = self._extract_generation_source_images(generation_context)

        if missing_images and IMAGE_REFERENCE_STRICT:
            fail(
                "IMAGE_REFERENCE_IMAGE_MISSING",
                "One or more reference images listed in generation_context.source_images do not exist.",
                field="generation_context.source_images",
                expected="all listed reference image paths exist",
                actual=json.dumps(missing_images, ensure_ascii=False),
                stage="PROCESSING",
            )

        if IMAGE_REFERENCE_STRICT and not source_images:
            fail(
                "IMAGE_REFERENCE_IMAGES_NOT_AVAILABLE",
                "Strict browser image generation requires source_images at the adapter boundary.",
                field="generation_context.source_images",
                expected="at least one existing reference image path",
                actual=str((generation_context or {}).get("source_images") if isinstance(generation_context, dict) else None),
                stage="PROCESSING",
            )

        json_log(
            level="INFO",
            message="Browser image generation started",
            stage="PROCESSING",
            status="STARTED",
            context={
                "operation": "browser_image_generation_start",
                "source_image_count": len(source_images),
                "size": size,
                "has_generation_context": generation_context is not None,
            },
        )

        page = self._page()

        if os.getenv("BROWSER_NEW_CHAT_EACH_PROMPT", "1") == "1":
            self._start_new_chat(page)
        elif not self._prepared_chat and os.getenv("BROWSER_NEW_CHAT", "1") == "1":
            self._start_new_chat(page)
            self._prepared_chat = True

        self._attach_images_for_generation(page, source_images)
        before_assistant_count = self._submit_image_generation_prompt(page, prompt)
        image_base64 = self._capture_latest_browser_generated_image_base64(page, before_assistant_count)

        return {
            "image_base64": image_base64,
            "revised_prompt": None,
            "source_images_used": source_images,
        }


class FlowBrowserImageGenerationAdapter(PromptExecutionAdapter):
    def __init__(
        self,
        cdp_url: str,
        flow_url: str,
        action_timeout_ms: int,
        shared_browser_adapter: Optional[BrowserPromptExecutionAdapter] = None,
    ) -> None:
        self.cdp_url = cdp_url
        self.flow_url = flow_url
        self.action_timeout_ms = action_timeout_ms
        self.shared_browser_adapter = shared_browser_adapter
        self._playwright = None
        self._browser = None
        self._context = None
        self._page_obj = None

    def execute_text(self, step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("FlowBrowserImageGenerationAdapter does not execute text or JSON prompt steps.")

    def _page(self):
        if self._page_obj is not None:
            try:
                if not self._page_obj.is_closed() and "labs.google/fx/tools/flow" in (self._page_obj.url or ""):
                    return self._page_obj
            except Exception:
                self._page_obj = None

        if self._browser is None:
            shared = self.shared_browser_adapter
            if shared is not None and getattr(shared, "_browser", None) is not None:
                self._playwright = getattr(shared, "_playwright", None)
                self._browser = getattr(shared, "_browser", None)
                self._context = getattr(shared, "_context", None)
                json_log(
                    level="INFO",
                    message="Flow adapter reused shared browser session",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_reuse_shared_browser_session",
                        "source_adapter": "BrowserPromptExecutionAdapter",
                    },
                )
            else:
                self._playwright = sync_playwright().start()
                try:
                    self._browser = self._playwright.chromium.connect_over_cdp(self.cdp_url)
                except Exception:
                    if "localhost" in self.cdp_url:
                        alt = self.cdp_url.replace("localhost", "127.0.0.1")
                        try:
                            self._browser = self._playwright.chromium.connect_over_cdp(alt)
                            self.cdp_url = alt
                        except Exception as exc:
                            fail(
                                "FLOW_PAGE_UNAVAILABLE",
                                "Unable to connect to Chrome over CDP for Flow image generation.",
                                field="BROWSER_CDP_URL",
                                expected="reachable Chrome remote debugging endpoint",
                                actual=f"{alt}: {exc}",
                                stage="PROCESSING",
                            )
                    else:
                        fail(
                            "FLOW_PAGE_UNAVAILABLE",
                            "Unable to connect to Chrome over CDP for Flow image generation.",
                            field="BROWSER_CDP_URL",
                            expected="reachable Chrome remote debugging endpoint",
                            actual=self.cdp_url,
                            stage="PROCESSING",
                        )

        chosen_context = None
        chosen_page = None
        for ctx in self._browser.contexts:
            for page in ctx.pages:
                try:
                    if "labs.google/fx/tools/flow" in (page.url or ""):
                        chosen_context = ctx
                        chosen_page = page
                        break
                except Exception:
                    continue
            if chosen_page is not None:
                break

        if chosen_context is None:
            if self._context is not None:
                chosen_context = self._context
            elif self._browser.contexts:
                chosen_context = self._browser.contexts[0]
            else:
                chosen_context = self._browser.new_context()

        if chosen_page is None:
            try:
                chosen_page = chosen_context.new_page()
                chosen_page.goto(self.flow_url, wait_until="domcontentloaded", timeout=self.action_timeout_ms)
            except Exception as exc:
                fail(
                    "FLOW_PAGE_UNAVAILABLE",
                    "Flow page could not be opened or navigated.",
                    field="FLOW_URL",
                    expected="reachable Flow project URL",
                    actual=f"{self.flow_url}: {exc}",
                    stage="PROCESSING",
                )

        self._context = chosen_context
        self._page_obj = chosen_page
        try:
            chosen_page.bring_to_front()
        except Exception:
            pass
        self._wait_for_flow_ready(chosen_page)
        return chosen_page

    def _flow_ready(self, page) -> bool:
        try:
            url = page.url or ""
            body_text = page.locator("body").inner_text(timeout=2000)
        except Exception:
            return False

        normalized = body_text.lower()
        if "sign in" in normalized or "choose an account" in normalized:
            fail(
                "FLOW_AUTH_REQUIRED",
                "Flow page is reachable but Google authentication is required.",
                field="FLOW_URL",
                expected="authenticated Flow project or prompt UI",
                actual=url,
                stage="PROCESSING",
            )

        readiness_markers = [
            "flow",
            "prompt",
            "create",
            "generate",
            "ingredient",
            "camera",
            "video",
        ]
        return "labs.google/fx/tools/flow" in url and any(marker in normalized for marker in readiness_markers)

    def _wait_for_flow_ready(self, page) -> None:
        deadline = time.time() + (self.action_timeout_ms / 1000.0)
        last_url = ""
        last_excerpt = ""
        while time.time() < deadline:
            try:
                last_url = page.url or ""
                last_excerpt = page.locator("body").inner_text(timeout=1000)[:500]
                if self._flow_ready(page):
                    json_log(
                        level="INFO",
                        message="Flow page ready",
                        stage="PROCESSING",
                        status="COMPLETED",
                        context={"operation": "flow_page_ready", "url": last_url},
                    )
                    return
            except Exception:
                pass
            page.wait_for_timeout(1000)

        fail(
            "FLOW_READY_TIMEOUT",
            "Timed out waiting for Flow project or prompt UI to become ready.",
            field="FLOW_URL",
            expected="Flow UI with project or prompt controls visible",
            actual=json.dumps({"url": last_url, "excerpt": last_excerpt}, ensure_ascii=False),
            stage="PROCESSING",
        )

    def _extract_reference_images(self, generation_context: Optional[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        source_images: List[str] = []
        missing_images: List[str] = []

        if isinstance(generation_context, dict):
            raw_source_images = generation_context.get("source_images") or []
            if isinstance(raw_source_images, list):
                for item in raw_source_images:
                    if not isinstance(item, str):
                        continue
                    path = Path(item)
                    if path.exists() and path.is_file():
                        source_images.append(str(path))
                    else:
                        missing_images.append(item)

        if missing_images and FLOW_REFERENCE_STRICT:
            fail(
                "FLOW_REFERENCE_IMAGE_MISSING",
                "One or more reference images listed in generation_context.source_images do not exist.",
                field="generation_context.source_images",
                expected="all listed Flow reference image paths exist",
                actual=json.dumps(missing_images, ensure_ascii=False),
                stage="PROCESSING",
            )

        if FLOW_REFERENCE_STRICT and not source_images:
            fail(
                "FLOW_REFERENCE_IMAGES_NOT_AVAILABLE",
                "Strict Flow image generation requires source_images at the adapter boundary.",
                field="generation_context.source_images",
                expected="at least one existing reference image path",
                actual=str((generation_context or {}).get("source_images") if isinstance(generation_context, dict) else None),
                stage="PROCESSING",
            )

        return source_images, missing_images

    def _flow_click_first(self, page, selectors: List[str], *, label: str, force: bool = False) -> bool:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() and locator.is_visible() and locator.is_enabled():
                    locator.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=force)
                    json_log(
                        level="DEBUG",
                        message=f"Flow UI clicked {label}",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "flow_ui_click_first",
                            "label": label,
                            "selector": selector,
                            "force": force,
                        },
                    )
                    return True
            except Exception:
                continue
        return False

    def _dismiss_flow_transient_overlays(self, page) -> None:
        for key in ["Escape", "Escape"]:
            try:
                page.keyboard.press(key)
                page.wait_for_timeout(250)
            except Exception:
                pass

    def _flow_norm(self, text_value: str) -> str:
        return re.sub(r"\s+", " ", (text_value or "").strip())

    def _copy_image_to_windows_clipboard(self, image_path: str) -> None:
        path = str(Path(image_path).resolve())

        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Path = @'
{path}
'@

$img = [System.Drawing.Image]::FromFile($Path)
$bmp = New-Object System.Drawing.Bitmap $img
$img.Dispose()

[System.Windows.Forms.Clipboard]::SetImage($bmp)
Start-Sleep -Milliseconds 300
"""

        subprocess.run(
            [
                "powershell.exe",
                "-STA",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps_script,
            ],
            check=True,
            timeout=max(30, int(self.action_timeout_ms / 1000)),
        )

    def _open_flow_composer_settings_pill(self, page) -> None:
        selectors = [
            "button:has-text('Nano Banana')",
            "[role='button']:has-text('Nano Banana')",
            "button:has-text('Imagen')",
            "[role='button']:has-text('Imagen')",
            "button:has-text('1x')",
            "[role='button']:has-text('1x')",
        ]

        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() and locator.is_visible() and locator.is_enabled():
                    locator.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    page.wait_for_timeout(1000)
                    json_log(
                        level="INFO",
                        message="Flow composer settings menu opened",
                        stage="PROCESSING",
                        status="IN_PROGRESS",
                        context={
                            "operation": "flow_composer_settings_menu_opened",
                            "selector": selector,
                        },
                    )
                    return
            except Exception:
                continue

        fail(
            "FLOW_SETTINGS_MENU_NOT_FOUND",
            "Could not find Flow composer model/settings pill.",
            field="flow_composer_settings",
            expected="composer pill containing Nano Banana, Imagen, or 1x",
            actual=f"url={getattr(page, 'url', '')}",
            stage="PROCESSING",
        )

    def _flow_open_menu(self, page):
        menu = page.locator(
            "[data-radix-menu-content][data-state='open'], [role='menu'][data-state='open']"
        ).last

        if not menu.count() or not menu.is_visible():
            fail(
                "FLOW_SETTINGS_MENU_NOT_OPEN",
                "Flow composer settings menu was not open after clicking the composer model/settings pill.",
                field="flow_settings_menu",
                expected="open Radix menu from composer model/settings pill",
                actual=f"url={getattr(page, 'url', '')}",
                stage="PROCESSING",
            )

        return menu

    def _flow_click_menu_button_containing(self, page, wanted: str, label: str) -> bool:
        menu = self._flow_open_menu(page)
        buttons = menu.locator("button, [role='tab'], [role='button'], [role='menuitem'], [role='option']")
        wanted_l = wanted.lower()

        for idx in range(min(buttons.count(), 80)):
            try:
                button = buttons.nth(idx)
                if not button.is_visible() or not button.is_enabled():
                    continue

                text = self._flow_norm(button.inner_text(timeout=500))
                if wanted_l not in text.lower():
                    continue

                button.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                page.wait_for_timeout(700)

                json_log(
                    level="INFO",
                    message="Flow settings option clicked",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "flow_settings_option_clicked",
                        "label": label,
                        "wanted": wanted,
                        "actual_text": text,
                    },
                )
                return True
            except Exception:
                continue

        return False

    def _select_flow_image_mode(self, page) -> bool:
        return self._flow_click_menu_button_containing(page, "Image", "image_mode")

    def _select_flow_aspect_ratio(self, page) -> bool:
        return self._flow_click_menu_button_containing(page, FLOW_ASPECT_RATIO, "aspect_ratio")

    def _select_flow_output_count(self, page) -> bool:
        count = str(FLOW_OUTPUT_COUNT).strip()
        label = "1x" if count == "1" else f"x{count}"
        return self._flow_click_menu_button_containing(page, label, "output_count")

    def _select_flow_model(self, page) -> bool:
        menu = self._flow_open_menu(page)

        buttons = menu.locator("button, [role='button']")
        model_button = None

        for idx in range(min(buttons.count(), 80)):
            try:
                button = buttons.nth(idx)
                if not button.is_visible() or not button.is_enabled():
                    continue

                text = self._flow_norm(button.inner_text(timeout=500))
                if "Nano Banana" in text or "Imagen" in text:
                    model_button = button

                    if FLOW_IMAGE_MODEL.lower() in text.lower():
                        json_log(
                            level="INFO",
                            message="Flow model selected",
                            stage="PROCESSING",
                            status="COMPLETED",
                            context={
                                "operation": "flow_model_already_selected",
                                "target_model": FLOW_IMAGE_MODEL,
                                "actual_text": text,
                            },
                        )
                        return True

                    button.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    page.wait_for_timeout(1000)
                    break
            except Exception:
                continue

        if model_button is None:
            return False

        selectors = [
            f"text={FLOW_IMAGE_MODEL}",
            f"button:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='menuitem']:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='option']:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='button']:has-text('{FLOW_IMAGE_MODEL}')",
        ]

        for selector in selectors:
            try:
                option = page.locator(selector).last
                if option.count() and option.is_visible():
                    option.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    page.wait_for_timeout(800)

                    json_log(
                        level="INFO",
                        message="Flow model selected",
                        stage="PROCESSING",
                        status="COMPLETED",
                        context={
                            "operation": "flow_model_selected",
                            "target_model": FLOW_IMAGE_MODEL,
                            "selector": selector,
                        },
                    )
                    return True
            except Exception:
                continue

        return False

    def _configure_flow_generation_settings(self, page) -> None:
        json_log(
            level="INFO",
            message="Flow generation settings selection started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_generation_settings_selection_start",
                "target_model": FLOW_IMAGE_MODEL,
                "aspect_ratio": FLOW_ASPECT_RATIO,
                "output_count": FLOW_OUTPUT_COUNT,
            },
        )

        self._open_flow_composer_settings_pill(page)

        image_ok = self._select_flow_image_mode(page)
        aspect_ok = self._select_flow_aspect_ratio(page)
        output_ok = self._select_flow_output_count(page)
        model_ok = self._select_flow_model(page)

        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass

        if FLOW_MODEL_STRICT and not model_ok:
            fail(
                "FLOW_MODEL_NOT_AVAILABLE",
                "Required Flow image model is not visible or selectable in the Flow composer settings menu.",
                field="FLOW_IMAGE_MODEL",
                expected=f"{FLOW_IMAGE_MODEL} selected from Flow composer settings menu",
                actual=json.dumps(
                    {
                        "image_ok": image_ok,
                        "aspect_ok": aspect_ok,
                        "output_ok": output_ok,
                        "model_ok": model_ok,
                        "url": getattr(page, "url", ""),
                    },
                    ensure_ascii=False,
                ),
                stage="PROCESSING",
            )

        if not image_ok or not aspect_ok or not output_ok:
            fail(
                "FLOW_SETTINGS_NOT_CONFIGURED",
                "Flow image mode, aspect ratio, or output count could not be selected.",
                field="flow_generation_settings",
                expected="Image mode, requested aspect ratio, and requested output count selected",
                actual=json.dumps(
                    {
                        "image_ok": image_ok,
                        "aspect_ok": aspect_ok,
                        "output_ok": output_ok,
                        "model_ok": model_ok,
                        "target_model": FLOW_IMAGE_MODEL,
                        "aspect_ratio": FLOW_ASPECT_RATIO,
                        "output_count": FLOW_OUTPUT_COUNT,
                    },
                    ensure_ascii=False,
                ),
                stage="PROCESSING",
            )

        json_log(
            level="INFO",
            message="Flow generation settings selected",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_generation_settings_selected",
                "image_ok": image_ok,
                "aspect_ok": aspect_ok,
                "output_ok": output_ok,
                "model_ok": model_ok,
                "target_model": FLOW_IMAGE_MODEL,
                "aspect_ratio": FLOW_ASPECT_RATIO,
                "output_count": FLOW_OUTPUT_COUNT,
            },
        )

    def _paste_flow_reference_images_into_composer(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        prompt_box = self._find_flow_prompt_box(page)

        json_log(
            level="INFO",
            message="Flow reference image clipboard paste started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_reference_clipboard_paste_start",
                "source_image_count": len(source_images),
                "paste_wait_seconds": FLOW_CLIPBOARD_PASTE_WAIT_SECONDS,
                "final_settle_seconds": FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS,
            },
        )

        for idx, image_path in enumerate(source_images, start=1):
            before_count = self._flow_composer_reference_count(page)

            self._copy_image_to_windows_clipboard(image_path)

            try:
                prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
            except Exception:
                prompt_box = self._find_flow_prompt_box(page)
                prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)

            page.keyboard.press("Control+V")

            # Required: let Flow finish rendering/uploading this pasted image before the next action.
            page.wait_for_timeout(int(FLOW_CLIPBOARD_PASTE_WAIT_SECONDS * 1000))

            after_count = self._flow_composer_reference_count(page)

            json_log(
                level="INFO",
                message="Flow reference image pasted into composer",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_reference_image_pasted_into_composer",
                    "image_index": idx,
                    "source_image_count": len(source_images),
                    "image_path": image_path,
                    "before_composer_reference_count": before_count,
                    "after_composer_reference_count": after_count,
                    "paste_wait_seconds": FLOW_CLIPBOARD_PASTE_WAIT_SECONDS,
                },
            )

        page.wait_for_timeout(int(FLOW_CLIPBOARD_FINAL_SETTLE_SECONDS * 1000))

        json_log(
            level="INFO",
            message="Flow reference images pasted into composer",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_reference_images_pasted_into_composer",
                "source_image_count": len(source_images),
                "composer_reference_count": self._flow_composer_reference_count(page),
                "attach_method": "clipboard",
            },
        )

    def _flow_visible_media_count(self, page, *, scope_label: str = "page") -> int:
        selectors = [
            "img",
            "canvas",
            "[role='img']",
            "[data-testid*='image']",
            "[data-testid*='asset']",
            "[data-testid*='media']",
            "[data-testid*='thumbnail']",
        ]
        seen = 0
        for selector in selectors:
            try:
                collection = page.locator(selector)
                count = min(collection.count(), 80)
                for idx in range(count):
                    item = collection.nth(idx)
                    if not item.is_visible():
                        continue
                    box = item.bounding_box() or {}
                    width = float(box.get("width", 0) or 0)
                    height = float(box.get("height", 0) or 0)
                    if width >= 40 and height >= 40:
                        seen += 1
            except Exception:
                continue
        return seen

    def _flow_composer_reference_count(self, page) -> int:
        composer_scopes = [
            "form",
            "[role='form']",
            "[data-testid*='composer']",
            "[data-testid*='prompt']",
            "[class*='composer']",
            "[class*='prompt']",
            "main",
        ]

        media_selectors = [
            "img",
            "canvas",
            "[role='img']",
            "[data-testid*='attachment']",
            "[data-testid*='chip']",
            "[data-testid*='asset']",
            "[data-testid*='media']",
            "[aria-label*='Remove']",
        ]

        max_seen = 0
        for scope_selector in composer_scopes:
            try:
                scopes = page.locator(scope_selector)
                scope_count = min(scopes.count(), 10)
                for sidx in range(scope_count):
                    scope = scopes.nth(sidx)
                    if not scope.is_visible():
                        continue
                    seen = 0
                    for media_selector in media_selectors:
                        try:
                            media = scope.locator(media_selector)
                            count = min(media.count(), 30)
                            for midx in range(count):
                                item = media.nth(midx)
                                if item.is_visible():
                                    box = item.bounding_box() or {}
                                    width = float(box.get("width", 0) or 0)
                                    height = float(box.get("height", 0) or 0)
                                    if width >= 16 and height >= 16:
                                        seen += 1
                        except Exception:
                            continue
                    max_seen = max(max_seen, seen)
            except Exception:
                continue

        return max_seen

    def _flow_reference_attach_summary(self, page) -> Dict[str, Any]:
        return {
            "url": getattr(page, "url", ""),
            "visible_media_count": self._flow_visible_media_count(page),
            "composer_reference_count": self._flow_composer_reference_count(page),
            "surface_summary": self._flow_prompt_surface_summary(page),
        }

    def _flow_open_uploaded_media_gallery(self, page) -> bool:
        open_selectors = [
            "button:has-text('View uploaded media')",
            "[role='button']:has-text('View uploaded media')",
            "button:has-text('Uploaded media')",
            "[role='button']:has-text('Uploaded media')",
            "button:has-text('All Media')",
            "[role='button']:has-text('All Media')",
            "button:has-text('Add Media')",
            "[role='button']:has-text('Add Media')",
            "button[aria-label*='uploaded media']",
            "button[aria-label*='Uploaded media']",
            "button[aria-label*='All Media']",
            "button[aria-label*='Add Media']",
            "[aria-label*='View uploaded media']",
            "[aria-label*='View images']",
            "[aria-label*='All Media']",
            "[aria-label*='Add Media']",
        ]

        clicked = self._flow_click_first(
            page,
            open_selectors,
            label="open_uploaded_media_gallery",
            force=True,
        )

        if clicked:
            page.wait_for_timeout(2000)

        json_log(
            level="INFO" if clicked else "DEBUG",
            message="Flow uploaded media gallery open attempted",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_open_uploaded_media_gallery",
                "clicked": clicked,
                "summary": self._flow_reference_attach_summary(page),
            },
        )

        return clicked

    def _flow_media_candidate_summary(self, page) -> Dict[str, Any]:
        selectors = [
            "[role='dialog'] img",
            "[role='dialog'] canvas",
            "[role='dialog'] [role='img']",
            "[data-testid*='gallery'] img",
            "[data-testid*='asset'] img",
            "[data-testid*='media'] img",
            "[data-testid*='thumbnail'] img",
            "main img",
            "main canvas",
            "[role='button'] img",
            "button img",
        ]

        details: List[Dict[str, Any]] = []
        for selector in selectors:
            try:
                collection = page.locator(selector)
                count = min(collection.count(), 20)
                visible_count = 0
                large_count = 0
                for idx in range(count):
                    try:
                        item = collection.nth(idx)
                        if not item.is_visible():
                            continue
                        visible_count += 1
                        box = item.bounding_box() or {}
                        width = float(box.get("width", 0) or 0)
                        height = float(box.get("height", 0) or 0)
                        if width >= 48 and height >= 48:
                            large_count += 1
                    except Exception:
                        continue
                if count or visible_count or large_count:
                    details.append(
                        {
                            "selector": selector,
                            "count": count,
                            "visible_count": visible_count,
                            "large_count": large_count,
                        }
                    )
            except Exception:
                continue

        return {
            "url": getattr(page, "url", ""),
            "selectors": details[:20],
        }

    def _flow_click_media_candidate(self, candidate) -> bool:
        try:
            candidate.scroll_into_view_if_needed(timeout=FLOW_UI_CLICK_TIMEOUT_MS)
        except Exception:
            pass

        try:
            candidate.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
            return True
        except Exception:
            pass

        try:
            box = candidate.bounding_box() or {}
            x = float(box.get("x", 0) or 0) + (float(box.get("width", 0) or 0) / 2)
            y = float(box.get("y", 0) or 0) + (float(box.get("height", 0) or 0) / 2)
            candidate.page.mouse.click(x, y)
            return True
        except Exception:
            return False

    def _flow_select_gallery_assets(self, page, expected_count: int) -> int:
        self._flow_open_uploaded_media_gallery(page)

        gallery_selectors = [
            "[role='dialog'] [aria-selected='false']",
            "[role='dialog'] [aria-checked='false']",
            "[role='dialog'] [role='checkbox']",
            "[role='dialog'] [role='option']",
            "[role='dialog'] [role='gridcell']",
            "[role='dialog'] [role='button'] img",
            "[role='dialog'] button img",
            "[role='dialog'] img",
            "[role='dialog'] canvas",
            "[data-testid*='uploaded'] img",
            "[data-testid*='gallery'] img",
            "[data-testid*='asset'] img",
            "[data-testid*='media'] img",
            "[data-testid*='thumbnail'] img",
            "[aria-label*='uploaded'] img",
            "[aria-label*='Uploaded'] img",
            "main [data-testid*='asset'] img",
            "main [data-testid*='media'] img",
            "main [data-testid*='thumbnail'] img",
            "main [role='button'] img",
            "main button img",
        ]

        selected = 0
        attempted = 0
        seen_keys = set()

        for selector in gallery_selectors:
            try:
                collection = page.locator(selector)
                count = min(collection.count(), 40)

                for idx in range(count):
                    if selected >= expected_count:
                        break

                    item = collection.nth(idx)

                    try:
                        if not item.is_visible():
                            continue
                    except Exception:
                        continue

                    try:
                        box = item.bounding_box() or {}
                    except Exception:
                        continue

                    width = float(box.get("width", 0) or 0)
                    height = float(box.get("height", 0) or 0)
                    x = float(box.get("x", 0) or 0)
                    y = float(box.get("y", 0) or 0)

                    if width < 48 or height < 48:
                        continue

                    key = f"{int(x)}:{int(y)}:{int(width)}:{int(height)}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    attempted += 1

                    target = item
                    try:
                        # Prefer clicking a containing card/button when the image itself
                        # is not the selectable element.
                        container = item.locator(
                            "xpath=ancestor-or-self::*[@role='button' or @role='option' or @role='gridcell' or self::button][1]"
                        ).first
                        if container.count() and container.is_visible():
                            target = container
                    except Exception:
                        pass

                    if self._flow_click_media_candidate(target):
                        selected += 1
                        page.wait_for_timeout(700)

                if selected >= expected_count:
                    break

            except Exception:
                continue

        json_log(
            level="INFO" if selected else "WARNING",
            message="Flow gallery asset selection attempted",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_gallery_asset_selection_attempted",
                "expected_count": expected_count,
                "selected_count": selected,
                "attempted_click_count": attempted,
                "candidate_summary": self._flow_media_candidate_summary(page),
            },
        )

        return selected

    def _flow_click_attach_selected_to_composer(self, page) -> bool:
        attach_selectors = [
            "button:has-text('Add to prompt')",
            "[role='button']:has-text('Add to prompt')",
            "button:has-text('Add selected')",
            "[role='button']:has-text('Add selected')",
            "button:has-text('Use selected')",
            "[role='button']:has-text('Use selected')",
            "button:has-text('Insert selected')",
            "[role='button']:has-text('Insert selected')",
            "button:has-text('Attach selected')",
            "[role='button']:has-text('Attach selected')",
            "button:has-text('Add image')",
            "[role='button']:has-text('Add image')",
            "button:has-text('Use image')",
            "[role='button']:has-text('Use image')",
            "button:has-text('Insert')",
            "[role='button']:has-text('Insert')",
            "button:has-text('Attach')",
            "[role='button']:has-text('Attach')",
            "button:has-text('Done')",
            "[role='button']:has-text('Done')",
            "button:has-text('Add')",
            "[role='button']:has-text('Add')",
            "button[aria-label*='Add']",
            "button[aria-label*='Use']",
            "button[aria-label*='Insert']",
            "button[aria-label*='Attach']",
            "button[aria-label*='Done']",
        ]
        return self._flow_click_first(page, attach_selectors, label="gallery_attach_selected_to_composer", force=True)

    def _wait_for_flow_references_in_composer(self, page, expected_count: int) -> bool:
        deadline = time.time() + FLOW_GALLERY_ATTACH_TIMEOUT_SECONDS
        last_log = 0.0

        while time.time() < deadline:
            count = self._flow_composer_reference_count(page)
            if count >= max(1, min(expected_count, 2)):
                json_log(
                    level="INFO",
                    message="Flow reference composer attachment confirmed",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_reference_composer_attach_confirmed",
                        "composer_reference_count": count,
                        "expected_source_image_count": expected_count,
                    },
                )
                return True

            now = time.time()
            if now - last_log >= 5.0:
                last_log = now
                json_log(
                    level="DEBUG",
                    message="Flow reference composer attachment wait continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "flow_reference_composer_attach_wait_continue",
                        "summary": self._flow_reference_attach_summary(page),
                    },
                )

            page.wait_for_timeout(1000)

        return False

    def _flow_submit_started(self, page) -> bool:
        indicators = [
            "text=/generating/i",
            "text=/creating/i",
            "text=/queued/i",
            "text=/rendering/i",
            "text=/processing/i",
            "[aria-label*='Cancel']",
            "[aria-label*='Stop']",
            "button:has-text('Cancel')",
            "button:has-text('Stop')",
            "[role='progressbar']",
            "[data-testid*='progress']",
            "[data-testid*='generating']",
            "[class*='spinner']",
            "[class*='loading']",
        ]

        for selector in indicators:
            try:
                loc = page.locator(selector).first
                if loc.count() and loc.is_visible():
                    return True
            except Exception:
                continue

        return False

    def _wait_for_flow_submit_confirmation(self, page) -> bool:
        deadline = time.time() + FLOW_SUBMIT_CONFIRM_TIMEOUT_SECONDS
        last_log = 0.0

        while time.time() < deadline:
            if self._flow_submit_started(page):
                json_log(
                    level="INFO",
                    message="Flow prompt submission confirmed",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_prompt_submission_confirmed",
                        "summary": self._flow_prompt_surface_summary(page),
                    },
                )
                return True

            now = time.time()
            if now - last_log >= 5.0:
                last_log = now
                json_log(
                    level="DEBUG",
                    message="Flow prompt submission confirmation wait continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "flow_prompt_submit_confirm_wait_continue",
                        "summary": self._flow_prompt_surface_summary(page),
                    },
                )

            page.wait_for_timeout(1000)

        return False

    def _finalize_flow_reference_attachment_to_composer(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        expected_count = len(source_images)

        json_log(
            level="INFO",
            message="Flow reference composer attachment verification started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_reference_composer_attach_verify_start",
                "source_image_count": expected_count,
                "strict": FLOW_REFERENCE_ATTACH_STRICT,
            },
        )

        before_count = self._flow_composer_reference_count(page)

        # Correct Flow order:
        # 1. Open the uploaded-media/gallery surface.
        # 2. Select uploaded image assets.
        # 3. Click the attach/add/use control.
        # 4. Confirm visible composer reference chips/assets.
        opened_gallery = self._flow_open_uploaded_media_gallery(page)
        selected_count = self._flow_select_gallery_assets(page, expected_count)
        clicked_attach = self._flow_click_attach_selected_to_composer(page)

        page.wait_for_timeout(2000)
        self._dismiss_flow_transient_overlays(page)

        attached = self._wait_for_flow_references_in_composer(page, expected_count)
        after_count = self._flow_composer_reference_count(page)

        if attached:
            json_log(
                level="INFO",
                message="Flow reference images attached to composer",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_reference_images_attached_to_composer",
                    "source_image_count": expected_count,
                    "opened_gallery": opened_gallery,
                    "selected_gallery_asset_count": selected_count,
                    "clicked_attach_control": clicked_attach,
                    "before_composer_reference_count": before_count,
                    "after_composer_reference_count": after_count,
                },
            )
            return

        context = {
            "operation": "flow_reference_gallery_attach_failed",
            "source_image_count": expected_count,
            "opened_gallery": opened_gallery,
            "selected_gallery_asset_count": selected_count,
            "clicked_attach_control": clicked_attach,
            "before_composer_reference_count": before_count,
            "after_composer_reference_count": after_count,
            "summary": self._flow_reference_attach_summary(page),
            "media_candidate_summary": self._flow_media_candidate_summary(page),
        }

        if FLOW_REFERENCE_ATTACH_STRICT:
            fail(
                "FLOW_REFERENCE_NOT_ATTACHED_TO_COMPOSER",
                "Flow reference images were uploaded to the gallery but were not confirmed attached to the active composer.",
                field="flow_reference_composer",
                expected="uploaded gallery image selected and attached into prompt composer",
                actual=json.dumps(context, ensure_ascii=False),
                stage="PROCESSING",
            )

        json_log(
            level="WARNING",
            message="Flow reference images uploaded but composer attachment was not confirmed",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context=context,
        )

    def _flow_prompt_surface_summary(self, page) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "url": getattr(page, "url", ""),
            "textarea_count": 0,
            "textbox_count": 0,
            "contenteditable_count": 0,
            "input_text_count": 0,
            "visible_button_texts": [],
        }

        try:
            summary["textarea_count"] = page.locator("textarea").count()
        except Exception:
            pass

        try:
            summary["textbox_count"] = page.locator("[role='textbox']").count()
        except Exception:
            pass

        try:
            summary["contenteditable_count"] = page.locator("[contenteditable='true']").count()
        except Exception:
            pass

        try:
            summary["input_text_count"] = page.locator("input[type='text'], input:not([type])").count()
        except Exception:
            pass

        try:
            buttons = page.locator("button, [role='button']")
            count = min(buttons.count(), 30)
            texts: List[str] = []
            for idx in range(count):
                try:
                    button = buttons.nth(idx)
                    if button.is_visible():
                        text = (button.inner_text(timeout=500) or "").strip()
                        aria = button.get_attribute("aria-label") or ""
                        label = text or aria
                        if label:
                            texts.append(label[:80])
                except Exception:
                    continue
            summary["visible_button_texts"] = texts[:20]
        except Exception:
            pass

        return summary

    def _activate_flow_prompt_surface(self, page) -> None:
        self._dismiss_flow_transient_overlays(page)

        activation_selectors = [
            "button:has-text('Text to image')",
            "[role='button']:has-text('Text to image')",
            "button:has-text('Create image')",
            "[role='button']:has-text('Create image')",
            "button:has-text('New image')",
            "[role='button']:has-text('New image')",
            "button:has-text('Start creating')",
            "[role='button']:has-text('Start creating')",
            "button:has-text('Image')",
            "[role='button']:has-text('Image')",
            "button:has-text('Prompt')",
            "[role='button']:has-text('Prompt')",
            "button[aria-label*='Prompt']",
            "[role='button'][aria-label*='Prompt']",
            "button[aria-label*='Create']",
            "[role='button'][aria-label*='Create']",
            "button[aria-label*='New']",
            "[role='button'][aria-label*='New']",
        ]

        clicked = self._flow_click_first(
            page,
            activation_selectors,
            label="flow_prompt_surface_activation",
            force=True,
        )

        if clicked:
            page.wait_for_timeout(1500)
            json_log(
                level="INFO",
                message="Flow prompt surface activation attempted",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_prompt_surface_activation_attempted",
                    "summary": self._flow_prompt_surface_summary(page),
                },
            )
        else:
            json_log(
                level="DEBUG",
                message="Flow prompt surface activation controls not found",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_prompt_surface_activation_not_found",
                    "summary": self._flow_prompt_surface_summary(page),
                },
            )

    def _find_flow_prompt_box(self, page):
        self._activate_flow_prompt_surface(page)

        prompt_selectors = [
            "textarea[placeholder*='prompt' i]",
            "textarea[aria-label*='prompt' i]",
            "textarea[placeholder*='describe' i]",
            "textarea[aria-label*='describe' i]",
            "[contenteditable='true'][aria-label*='prompt' i]",
            "[contenteditable='true'][aria-label*='describe' i]",
            "div[role='textbox'][aria-label*='prompt' i]",
            "div[role='textbox'][aria-label*='describe' i]",
            "[data-lexical-editor='true']",
            ".ProseMirror",
            "[contenteditable='true']",
            "div[role='textbox']",
            "textarea",
            "input[type='text']",
            "input:not([type])",
        ]

        def candidate_is_usable(candidate) -> bool:
            try:
                if not candidate.is_visible():
                    return False
            except Exception:
                return False

            try:
                box = candidate.bounding_box() or {}
                width = float(box.get("width", 0) or 0)
                height = float(box.get("height", 0) or 0)
                if width < 120 or height < 20:
                    return False
            except Exception:
                return False

            try:
                disabled = candidate.get_attribute("disabled")
                readonly = candidate.get_attribute("readonly")
                aria_disabled = candidate.get_attribute("aria-disabled")
                input_type = (candidate.get_attribute("type") or "").lower()
                if disabled is not None or readonly is not None or aria_disabled == "true" or input_type == "file":
                    return False
            except Exception:
                pass

            return True

        def scan_scope(scope, scope_label: str):
            for selector in prompt_selectors:
                try:
                    collection = scope.locator(selector)
                    count = min(collection.count(), 15)
                    for idx in range(count):
                        candidate = collection.nth(idx)
                        if candidate_is_usable(candidate):
                            json_log(
                                level="INFO",
                                message="Flow prompt box discovered",
                                stage="PROCESSING",
                                status="COMPLETED",
                                context={
                                    "operation": "flow_prompt_box_discovered",
                                    "selector": selector,
                                    "scope": scope_label,
                                    "index": idx,
                                },
                            )
                            return candidate
                except Exception:
                    continue
            return None

        deadline = time.time() + FLOW_PROMPT_READY_TIMEOUT_SECONDS
        last_summary: Dict[str, Any] = {}
        last_activation = 0.0

        while time.time() < deadline:
            found = scan_scope(page, "page")
            if found is not None:
                return found

            try:
                for frame in page.frames:
                    if frame == page.main_frame:
                        continue
                    found = scan_scope(frame, f"frame:{getattr(frame, 'url', '')[:120]}")
                    if found is not None:
                        return found
            except Exception:
                pass

            now = time.time()
            if now - last_activation >= 5.0:
                last_activation = now
                self._activate_flow_prompt_surface(page)
                last_summary = self._flow_prompt_surface_summary(page)
                json_log(
                    level="DEBUG",
                    message="Flow prompt composer discovery continuing",
                    stage="PROCESSING",
                    status="IN_PROGRESS",
                    context={
                        "operation": "flow_prompt_box_discovery_continue",
                        "summary": last_summary,
                    },
                )

            page.wait_for_timeout(500)

        fail(
            "FLOW_PROMPT_INPUT_MISSING",
            "Could not find Flow prompt input for image generation.",
            field="flow_prompt_input",
            expected="visible Flow prompt textarea/textbox/contenteditable composer",
            actual=json.dumps(
                {
                    "url": getattr(page, "url", ""),
                    "summary": last_summary or self._flow_prompt_surface_summary(page),
                },
                ensure_ascii=False,
            ),
            stage="PROCESSING",
        )

    def _fill_flow_prompt_box(self, page, prompt_box, prompt: str) -> None:
        try:
            prompt_box.scroll_into_view_if_needed(timeout=FLOW_UI_CLICK_TIMEOUT_MS)
        except Exception:
            pass

        try:
            prompt_box.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
        except Exception:
            try:
                prompt_box.evaluate("(el) => el.focus()")
            except Exception:
                pass

        try:
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
        except Exception:
            pass

        filled = False

        try:
            prompt_box.fill(prompt, timeout=FLOW_UI_CLICK_TIMEOUT_MS)
            filled = True
        except Exception:
            pass

        if not filled:
            try:
                prompt_box.evaluate(
                    """
                    (el, value) => {
                      el.focus();
                      if ("value" in el) {
                        el.value = value;
                      } else {
                        el.textContent = value;
                      }
                      el.dispatchEvent(new InputEvent("input", {
                        bubbles: true,
                        cancelable: true,
                        inputType: "insertText",
                        data: value
                      }));
                      el.dispatchEvent(new Event("change", { bubbles: true }));
                    }
                    """,
                    prompt,
                )
                filled = True
            except Exception:
                pass

        if not filled:
            try:
                page.keyboard.insert_text(prompt)
                filled = True
            except Exception:
                prompt_box.type(prompt, delay=0, timeout=self.action_timeout_ms)
                filled = True

        try:
            value_len = prompt_box.evaluate(
                """
                (el) => {
                  if ("value" in el) return String(el.value || "").length;
                  return String(el.innerText || el.textContent || "").length;
                }
                """
            )
        except Exception:
            value_len = -1

        if value_len == 0:
            fail(
                "FLOW_PROMPT_INPUT_NOT_FILLED",
                "Flow prompt input was discovered but did not retain prompt text.",
                field="flow_prompt_input",
                expected="prompt text inserted into Flow composer",
                actual=f"value_len={value_len}; prompt_chars={len(prompt or '')}",
                stage="PROCESSING",
            )

        json_log(
            level="INFO",
            message="Flow prompt box filled",
            stage="PROCESSING",
            status="COMPLETED",
            context={
                "operation": "flow_prompt_box_filled",
                "prompt_chars": len(prompt or ""),
                "detected_value_chars": value_len,
            },
        )

    def _attach_reference_images(self, page, source_images: List[str]) -> None:
        if not source_images:
            return

        json_log(
            level="INFO",
            message="Flow reference image attachment started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_reference_image_attach_start",
                "source_image_count": len(source_images),
                "attach_method": FLOW_REFERENCE_ATTACH_METHOD,
            },
        )

        if FLOW_REFERENCE_ATTACH_METHOD != "clipboard":
            fail(
                "FLOW_REFERENCE_ATTACH_METHOD_UNSUPPORTED",
                "Only the confirmed clipboard Flow reference attachment method is enabled for PATCH_12O.",
                field="FLOW_REFERENCE_ATTACH_METHOD",
                expected="clipboard",
                actual=FLOW_REFERENCE_ATTACH_METHOD,
                stage="PROCESSING",
            )

        try:
            self._paste_flow_reference_images_into_composer(page, source_images)
        except SystemExit:
            raise
        except Exception as exc:
            fail(
                "FLOW_REFERENCE_CLIPBOARD_PASTE_FAILED",
                "Failed to paste Flow reference images into the composer via Windows clipboard.",
                field="generation_context.source_images",
                expected="each source image copied to clipboard and pasted into Flow composer with upload wait",
                actual=str(exc)[:1000],
                stage="PROCESSING",
            )

    def _submit_flow_prompt(self, page, prompt: str) -> None:
        json_log(
            level="INFO",
            message="Flow model selection started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_model_selection_start",
                "target_model": FLOW_IMAGE_MODEL,
                "strict": FLOW_MODEL_STRICT,
            },
        )

        model_visible = False
        model_selectors = [
            f"button:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='button']:has-text('{FLOW_IMAGE_MODEL}')",
            f"text={FLOW_IMAGE_MODEL}",
            "button[aria-label*='model']",
            "button[aria-label*='Model']",
            "[role='button'][aria-label*='model']",
            "[role='button'][aria-label*='Model']",
        ]

        for selector in model_selectors:
            try:
                candidate = page.locator(selector).first
                if not candidate.count() or not candidate.is_visible():
                    continue
                candidate.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                page.wait_for_timeout(500)
                model_visible = True
                break
            except Exception:
                continue

        if not model_visible:
            try:
                model_option = page.get_by_text(FLOW_IMAGE_MODEL, exact=False).first
                if model_option.count() and model_option.is_visible():
                    model_option.click(timeout=FLOW_UI_CLICK_TIMEOUT_MS, force=True)
                    page.wait_for_timeout(500)
                    model_visible = True
            except Exception:
                pass

        if not model_visible:
            if FLOW_MODEL_STRICT:
                json_log(
                    level="ERROR",
                    message="Flow model not available",
                    stage="PROCESSING",
                    status="FAILED",
                    context={
                        "operation": "flow_model_not_available",
                        "target_model": FLOW_IMAGE_MODEL,
                    },
                )
                fail(
                    "FLOW_MODEL_NOT_AVAILABLE",
                    "Required Flow image model is not visible or selectable in the Flow UI.",
                    field="FLOW_IMAGE_MODEL",
                    expected=f"{FLOW_IMAGE_MODEL} visible/selectable in Flow model menu",
                    actual=f"url={getattr(page, 'url', '')}",
                    stage="PROCESSING",
                )

            json_log(
                level="WARNING",
                message="Flow model selection skipped",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={
                    "operation": "flow_model_selection_skipped",
                    "target_model": FLOW_IMAGE_MODEL,
                },
            )
        else:
            json_log(
                level="INFO",
                message="Flow model selected",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_model_selected",
                    "target_model": FLOW_IMAGE_MODEL,
                },
            )

        self._dismiss_flow_transient_overlays(page)
        prompt_box = self._find_flow_prompt_box(page)
        self._fill_flow_prompt_box(page, prompt_box, prompt)

        generate_selectors = [
            "button:has-text('Generate')",
            "button[aria-label*='Generate']",
            "button[aria-label*='generate']",
            "[role='button']:has-text('Generate')",
            "button:has-text('Create')",
            "button[aria-label*='Create']",
            "button[aria-label*='create']",
            "[role='button']:has-text('Create')",
        ]

        clicked_generate = self._flow_click_first(page, generate_selectors, label="flow_generate_button", force=True)

        if clicked_generate and self._wait_for_flow_submit_confirmation(page):
            json_log(
                level="INFO",
                message="Flow image prompt submitted",
                stage="PROCESSING",
                status="COMPLETED",
                context={
                    "operation": "flow_prompt_submitted",
                    "prompt_chars": len(prompt or ""),
                    "target_model": FLOW_IMAGE_MODEL,
                    "submit_method": "button",
                },
            )
            return

        try:
            page.keyboard.press("Control+Enter")
            if self._wait_for_flow_submit_confirmation(page):
                json_log(
                    level="INFO",
                    message="Flow image prompt submitted",
                    stage="PROCESSING",
                    status="COMPLETED",
                    context={
                        "operation": "flow_prompt_submitted_keyboard",
                        "prompt_chars": len(prompt or ""),
                        "target_model": FLOW_IMAGE_MODEL,
                        "submit_method": "keyboard",
                    },
                )
                return
        except Exception:
            pass

        fail(
            "FLOW_PROMPT_SUBMIT_NOT_CONFIRMED",
            "Flow prompt text was filled but generation start was not confirmed.",
            field="flow_generate_button",
            expected="Flow generation indicator after button click or Control+Enter",
            actual=json.dumps(
                {
                    "clicked_generate": clicked_generate,
                    "summary": self._flow_prompt_surface_summary(page),
                    "reference_attach_summary": self._flow_reference_attach_summary(page),
                },
                ensure_ascii=False,
            ),
            stage="PROCESSING",
        )

    def _capture_flow_generated_image_base64(self, page) -> str:
        json_log(
            level="INFO",
            message="Flow image generation wait started",
            stage="PROCESSING",
            status="IN_PROGRESS",
            context={
                "operation": "flow_image_generation_wait_start",
                "timeout_seconds": FLOW_IMAGE_TIMEOUT_SECONDS,
            },
        )

        def locator_key(locator) -> str:
            try:
                src = locator.get_attribute("src") or ""
                if src:
                    return src[:500]
            except Exception:
                pass
            try:
                box = locator.bounding_box() or {}
                tag_name = locator.evaluate("el => el.tagName.toLowerCase()")
                return json.dumps(
                    {
                        "tag": tag_name,
                        "x": round(float(box.get("x", 0)), 1),
                        "y": round(float(box.get("y", 0)), 1),
                        "w": round(float(box.get("width", 0)), 1),
                        "h": round(float(box.get("height", 0)), 1),
                    },
                    sort_keys=True,
                )
            except Exception:
                return ""

        def visible_large_enough(locator) -> bool:
            try:
                if not locator.is_visible():
                    return False
                box = locator.bounding_box() or {}
                return float(box.get("width", 0)) >= 180 and float(box.get("height", 0)) >= 180
            except Exception:
                return False

        def collect_candidates():
            candidates = []
            selectors = [
                "main img[src^='blob:']",
                "main img[src^='data:image']",
                "main img",
                "main canvas",
                "[data-testid*='generation'] img",
                "[data-testid*='generation'] canvas",
                "[data-testid*='result'] img",
                "[data-testid*='result'] canvas",
                "[role='img']",
            ]
            for selector in selectors:
                try:
                    collection = page.locator(selector)
                    count = min(collection.count(), 20)
                    for idx in range(count):
                        candidates.append((selector, collection.nth(idx)))
                except Exception:
                    continue
            return candidates

        def read_locator_image_base64(locator) -> Optional[str]:
            try:
                src = locator.get_attribute("src") or ""
                if src.startswith("data:image") and "," in src:
                    return src.split(",", 1)[1]
                if src.startswith("blob:") or src.startswith("http://") or src.startswith("https://"):
                    return page.evaluate(
                        """
                        async (src) => {
                          const response = await fetch(src);
                          const blob = await response.blob();
                          const bytes = new Uint8Array(await blob.arrayBuffer());
                          let binary = "";
                          for (let i = 0; i < bytes.length; i += 1) {
                            binary += String.fromCharCode(bytes[i]);
                          }
                          return btoa(binary);
                        }
                        """,
                        src,
                    )
            except Exception:
                return None
            return None

        baseline_keys = set()
        for _selector, candidate in collect_candidates():
            try:
                key = locator_key(candidate)
                if key:
                    baseline_keys.add(key)
            except Exception:
                continue

        download_selectors = [
            "button[aria-label*='Download']",
            "button[aria-label*='download']",
            "[role='button'][aria-label*='Download']",
            "[role='button'][aria-label*='download']",
            "button:has-text('Download')",
            "[data-testid*='download']",
        ]

        deadline = time.time() + FLOW_IMAGE_TIMEOUT_SECONDS
        last_error = ""
        while time.time() < deadline:
            for selector in download_selectors:
                try:
                    button = page.locator(selector).last
                    if not button.count() or not button.is_visible() or not button.is_enabled():
                        continue
                    with page.expect_download(timeout=3000) as download_info:
                        button.click(timeout=self.action_timeout_ms)
                    download = download_info.value
                    download_path = download.path()
                    if download_path:
                        image_base64 = base64.b64encode(Path(download_path).read_bytes()).decode("ascii")
                        json_log(
                            level="INFO",
                            message="Flow generated image captured from download",
                            stage="PROCESSING",
                            status="COMPLETED",
                            context={
                                "operation": "flow_generated_image_captured_download",
                                "image_base64_chars": len(image_base64),
                            },
                        )
                        return image_base64
                except Exception as exc:
                    last_error = str(exc)[:500]

            for selector, candidate in collect_candidates():
                try:
                    if not visible_large_enough(candidate):
                        continue
                    key = locator_key(candidate)
                    if key and key in baseline_keys:
                        continue

                    image_base64 = read_locator_image_base64(candidate)
                    if image_base64:
                        json_log(
                            level="INFO",
                            message="Flow generated image captured from image tile",
                            stage="PROCESSING",
                            status="COMPLETED",
                            context={
                                "operation": "flow_generated_image_captured_tile",
                                "selector": selector,
                                "image_base64_chars": len(image_base64),
                            },
                        )
                        return image_base64

                    screenshot_bytes = candidate.screenshot(timeout=self.action_timeout_ms)
                    image_base64 = base64.b64encode(screenshot_bytes).decode("ascii")
                    json_log(
                        level="INFO",
                        message="Flow generated image captured from canvas/screenshot",
                        stage="PROCESSING",
                        status="COMPLETED",
                        context={
                            "operation": "flow_generated_image_captured_screenshot",
                            "selector": selector,
                            "image_base64_chars": len(image_base64),
                        },
                    )
                    return image_base64
                except Exception as exc:
                    last_error = str(exc)[:500]

            page.wait_for_timeout(1000)

        fail(
            "FLOW_IMAGE_GENERATION_TIMEOUT",
            "Timed out waiting for Flow to produce a downloadable, image, canvas, or screenshot-capturable result.",
            field="flow_generated_image",
            expected="generated Flow output captured as base64 image",
            actual=last_error,
            stage="PROCESSING",
        )

        fail(
            "FLOW_GENERATED_IMAGE_CAPTURE_FAILED",
            "Flow generated image capture failed after waiting for generation output.",
            field="flow_generated_image",
            expected="generated Flow output captured as base64 image",
            actual=last_error,
            stage="PROCESSING",
        )

    def execute_image(
        self,
        prompt: str,
        size: str = "1024x1536",
        generation_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        source_images, _missing_images = self._extract_reference_images(generation_context)
        page = self._page()
        self._attach_reference_images(page, source_images)
        self._submit_flow_prompt(page, prompt)
        image_base64 = self._capture_flow_generated_image_base64(page)

        return {
            "image_base64": image_base64,
            "revised_prompt": None,
            "source_images_used": source_images,
            "generation_backend": "flow_browser",
            "generation_model": FLOW_IMAGE_MODEL,
        }


def _json_only_retry_prompt(step_id: str, schema: Dict[str, Any], previous_response: str) -> str:
    schema_compact = json.dumps(schema, ensure_ascii=False, indent=2)
    prev = previous_response.strip()
    if len(prev) > 1500:
        prev = prev[:1500] + "…"
    return (
        f"Your previous reply for step {step_id} was not valid JSON.\n\n"
        f"Return ONLY valid JSON now. No prose, no markdown fences, no prefix text.\n"
        f"If you are unsure, still return best-effort JSON that matches the schema.\n\n"
        f"JSON SCHEMA:\n{schema_compact}\n\n"
        f"PREVIOUS (invalid) RESPONSE:\n{prev}\n"
    )


client: Any = None
TEXT_EXECUTION_ADAPTER: Optional[PromptExecutionAdapter] = None
IMAGE_EXECUTION_ADAPTER: Optional[PromptExecutionAdapter] = None


def get_text_execution_adapter() -> PromptExecutionAdapter:
    global client, TEXT_EXECUTION_ADAPTER
    if TEXT_EXECUTION_ADAPTER is None:
        if EXECUTION_BACKEND == "browser":
            TEXT_EXECUTION_ADAPTER = BrowserPromptExecutionAdapter(
                BROWSER_CDP_URL,
                BROWSER_CHAT_URL,
                BROWSER_ACTION_TIMEOUT_MS,
            )
        else:
            if OpenAI is None:
                fail("MISSING_DEPENDENCY", "Python package 'openai' is required for EXECUTION_BACKEND != browser.")
            if client is None:
                client = OpenAI()
            TEXT_EXECUTION_ADAPTER = OpenAIPromptExecutionAdapter(client)
    return TEXT_EXECUTION_ADAPTER


def get_image_execution_adapter() -> PromptExecutionAdapter:
    global IMAGE_EXECUTION_ADAPTER
    if IMAGE_EXECUTION_ADAPTER is None:
        if IMAGE_EXECUTION_BACKEND == "flow_browser":
            text_adapter = get_text_execution_adapter()
            shared_browser_adapter = text_adapter if isinstance(text_adapter, BrowserPromptExecutionAdapter) else None
            IMAGE_EXECUTION_ADAPTER = FlowBrowserImageGenerationAdapter(
                BROWSER_CDP_URL,
                FLOW_URL,
                BROWSER_ACTION_TIMEOUT_MS,
                shared_browser_adapter=shared_browser_adapter,
            )
        else:
            IMAGE_EXECUTION_ADAPTER = get_text_execution_adapter()
    return IMAGE_EXECUTION_ADAPTER


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


def is_transient_assistant_text(text: str) -> bool:
    stripped = (text or "").strip()
    lowered = stripped.lower().strip(".… ")

    if not stripped:
        return True

    if stripped.lstrip().startswith("{") or stripped.lstrip().startswith("["):
        return False

    transient_values = {
        "thinking",
        "thinking...",
        "thinking…",
    }

    return lowered in transient_values


def has_json_candidate(text: str) -> bool:
    normalized = normalize_json_text(text or "")
    return "{" in normalized and "}" in normalized


def assistant_response_ready(text: str) -> bool:
    if is_transient_assistant_text(text):
        return False
    if BROWSER_REQUIRE_JSON_CANDIDATE and not has_json_candidate(text):
        return False
    if BROWSER_REQUIRE_PARSEABLE_JSON:
        parsed, _err, _excerpt = try_parse_response_json(text)
        if parsed is None:
            return False
    return True


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

    # Fix doubled terminal quote characters inside JSON string values, e.g.:
    # "sensor_size":"1/2.9""
    # becomes a valid JSON string containing the inch quote:
    # "sensor_size":"1/2.9\""
    json_text = re.sub(r'(?<=\d)""(?=\s*[,}\]])', r'\\""', json_text)

    return json_text


def try_parse_response_json(response_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], str]:
    """
    Returns (parsed, error, excerpt). Does not call fail().
    """
    excerpt = normalize_json_text(response_text)
    try:
        return json.loads(excerpt), None, excerpt
    except Exception:
        repaired = repair_common_json_glitches(excerpt)
        repaired = repair_unescaped_quotes(repaired)
        try:
            return json.loads(repaired), None, excerpt
        except Exception as e:
            return None, str(e), excerpt


def parse_response_json(response_text: str) -> Dict[str, Any]:
    parsed, error, excerpt = try_parse_response_json(response_text)
    if parsed is None:
        fail(
            "MODEL_OUTPUT_NOT_JSON",
            f"Model output is not valid JSON: {error}",
            actual=excerpt[:2000],
        )
    return parsed


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
            "spatial_image_contract",
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
            "spatial_image_contract": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "product_dimensions",
                    "product_3d_geometry",
                    "component_interaction_rules",
                    "photographer_scene_rules",
                    "physics_constraints",
                    "negative_spatial_constraints",
                ],
                "properties": {
                    "product_dimensions": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "exact_dimensions",
                            "dimension_source",
                            "dimension_status",
                            "relative_scale",
                        ],
                        "properties": {
                            "exact_dimensions": {"type": "string"},
                            "dimension_source": {"type": "string"},
                            "dimension_status": {"type": "string"},
                            "relative_scale": {"type": "string"},
                        },
                    },
                    "product_3d_geometry": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "overall_shape",
                            "front_face",
                            "rear_face",
                            "top_face",
                            "bottom_face",
                            "left_side",
                            "right_side",
                            "component_depth_relationships",
                        ],
                        "properties": {
                            "overall_shape": {"type": "string"},
                            "front_face": {"type": "string"},
                            "rear_face": {"type": "string"},
                            "top_face": {"type": "string"},
                            "bottom_face": {"type": "string"},
                            "left_side": {"type": "string"},
                            "right_side": {"type": "string"},
                            "component_depth_relationships": {"type": "string"},
                        },
                    },
                    "component_interaction_rules": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "mounting_or_support_logic",
                            "lens_or_primary_function_axis",
                            "screen_or_display_logic",
                            "controls_and_ports_logic",
                            "accessory_interaction_logic",
                        ],
                        "properties": {
                            "mounting_or_support_logic": {"type": "string"},
                            "lens_or_primary_function_axis": {"type": "string"},
                            "screen_or_display_logic": {"type": "string"},
                            "controls_and_ports_logic": {"type": "string"},
                            "accessory_interaction_logic": {"type": "string"},
                        },
                    },
                    "photographer_scene_rules": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "camera_pov_required",
                            "foreground_midground_background",
                            "focal_plane_and_depth_of_field",
                            "environment_sync_rules",
                            "scale_rules",
                        ],
                        "properties": {
                            "camera_pov_required": {"type": "string"},
                            "foreground_midground_background": {"type": "string"},
                            "focal_plane_and_depth_of_field": {"type": "string"},
                            "environment_sync_rules": {"type": "string"},
                            "scale_rules": {"type": "string"},
                        },
                    },
                    "physics_constraints": {"type": "array", "items": {"type": "string"}},
                    "negative_spatial_constraints": {"type": "array", "items": {"type": "string"}},
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
                    "spatial_scene_brief",
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
                    "spatial_scene_brief": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "system_role_context",
                            "technical_specifications",
                            "model_photographer_pov",
                            "binding_geometry",
                            "orientation_and_spatial_sync",
                            "scene_composition_and_environmental_sync",
                            "typography_and_graphic_overlays",
                            "physical_constraints",
                            "negative_spatial_constraints",
                            "amazon_compliance_constraints",
                        ],
                        "properties": {
                            "system_role_context": {"type": "string"},
                            "technical_specifications": {"type": "string"},
                            "model_photographer_pov": {"type": "string"},
                            "binding_geometry": {"type": "string"},
                            "orientation_and_spatial_sync": {"type": "string"},
                            "scene_composition_and_environmental_sync": {"type": "string"},
                            "typography_and_graphic_overlays": {"type": "string"},
                            "physical_constraints": {"type": "array", "items": {"type": "string"}},
                            "negative_spatial_constraints": {"type": "array", "items": {"type": "string"}},
                            "amazon_compliance_constraints": {"type": "array", "items": {"type": "string"}},
                        },
                    },
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


def pick_visual_attributes(product_data: Dict[str, Any]) -> Dict[str, Any]:
    attributes = product_data.get("attributes", {})
    additional = product_data.get("additional_attributes", {})
    if not isinstance(attributes, dict):
        attributes = {}
    if not isinstance(additional, dict):
        additional = {}

    visual_keywords = {
        "color",
        "material",
        "materials",
        "screen",
        "display",
        "lens",
        "viewing",
        "angle",
        "size",
        "dimensions",
        "shape",
        "mount",
        "bracket",
        "accessory",
        "accessories",
        "included",
        "app",
        "wifi",
        "wi-fi",
        "sensor",
        "night",
        "resolution",
        "frame",
        "coverage",
        "installation",
        "setup",
    }

    selected: Dict[str, Any] = {}
    for source in (attributes, additional):
        for key, value in source.items():
            key_text = str(key).lower()
            if any(token in key_text for token in visual_keywords):
                selected[key] = value
    return selected


def get_extraction_output(state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    outputs = state.get("outputs", {})
    if isinstance(outputs, dict) and isinstance(outputs.get(step_id), dict):
        return outputs[step_id]
    promoted_key = "prompt_01A" if step_id == "01A" else "prompt_01B"
    promoted = state.get(promoted_key)
    if isinstance(promoted, dict):
        return promoted
    return {}


def build_spatial_image_contract(product_data: Dict[str, Any], visual_data: Dict[str, Any]) -> Dict[str, Any]:
    existing = visual_data.get("spatial_image_contract")
    if isinstance(existing, dict):
        return existing

    visual_identity = visual_data.get("visual_identity", {})
    if not isinstance(visual_identity, dict):
        visual_identity = {}

    object_layout_map = visual_data.get("object_layout_map", {})
    if not isinstance(object_layout_map, dict):
        object_layout_map = {}

    product_geometry = visual_data.get("product_geometry", {})
    if not isinstance(product_geometry, dict):
        product_geometry = {}

    image_views = visual_data.get("image_views", {})
    if not isinstance(image_views, dict):
        image_views = {}

    attributes = product_data.get("attributes", {})
    if not isinstance(attributes, dict):
        attributes = {}

    additional_attributes = product_data.get("additional_attributes", {})
    if not isinstance(additional_attributes, dict):
        additional_attributes = {}

    package_contents = product_data.get("package_contents", [])
    if not isinstance(package_contents, list):
        package_contents = []

    dimension_sources = []
    for source in (attributes, additional_attributes):
        for key, value in source.items():
            key_text = str(key).lower()
            if any(token in key_text for token in ("dimension", "size", "width", "height", "depth", "length")):
                dimension_sources.append(f"{key}: {value}")

    exact_dimensions = "; ".join(dimension_sources) if dimension_sources else "Unconfirmed"
    dimension_source = "input attributes" if dimension_sources else "not provided in input/source data"
    dimension_status = "confirmed" if dimension_sources else "unconfirmed"

    product_type = str(visual_identity.get("product_type") or product_data.get("product_category") or "product")
    materials = str(visual_identity.get("materials") or "")
    dominant_color = str(visual_identity.get("dominant_color") or "")
    primary_components = visual_identity.get("primary_components") or []
    if not isinstance(primary_components, list):
        primary_components = []

    component_positions = object_layout_map.get("component_positions") or {}
    if not isinstance(component_positions, dict):
        component_positions = {}

    return {
        "product_dimensions": {
            "exact_dimensions": exact_dimensions,
            "dimension_source": dimension_source,
            "dimension_status": dimension_status,
            "relative_scale": str(product_geometry.get("relative_dimensions") or product_geometry.get("proportions") or "relative proportions from visual extraction"),
        },
        "product_3d_geometry": {
            "overall_shape": str(product_geometry.get("shape_description") or f"{product_type} physical body"),
            "front_face": str(image_views.get("front_3q_left") or image_views.get("front_3q_right") or "front face from source imagery"),
            "rear_face": str(image_views.get("rear_3q") or "rear face unconfirmed from source imagery"),
            "top_face": str(image_views.get("top_view") or "top face unconfirmed from source imagery"),
            "bottom_face": str(image_views.get("bottom_view") or "bottom face unconfirmed from source imagery"),
            "left_side": str(image_views.get("left_side") or "left side unconfirmed from source imagery"),
            "right_side": str(image_views.get("right_side") or "right side unconfirmed from source imagery"),
            "component_depth_relationships": json.dumps(component_positions, ensure_ascii=False) if component_positions else "Use component placement and depth from source imagery only.",
        },
        "component_interaction_rules": {
            "mounting_or_support_logic": str(attributes.get("mount") or additional_attributes.get("mount") or "Use visible support, mounting, resting, or included accessory logic only."),
            "lens_or_primary_function_axis": "Align any lens, sensor, nozzle, light, speaker, blade, handle, display, or primary functional face with its real-world operating direction.",
            "screen_or_display_logic": "If a screen/display is present, screen content must match the visible environment and physical viewing direction.",
            "controls_and_ports_logic": "Do not invent controls, ports, labels, lights, or markings that are not visible or provided in source data.",
            "accessory_interaction_logic": "Use only included accessories: " + (", ".join(str(item) for item in package_contents) if package_contents else "none confirmed"),
        },
        "photographer_scene_rules": {
            "camera_pov_required": "Describe a real camera position, optical axis, foreground, midground, background, focal plane, and product-facing direction.",
            "foreground_midground_background": "Place the product and surrounding objects in physically coherent depth layers.",
            "focal_plane_and_depth_of_field": "Keep the verified product geometry in focus; use depth of field only when it does not obscure required product details.",
            "environment_sync_rules": "Environment, reflections, displays, and functional axes must agree with the product geometry and scene perspective.",
            "scale_rules": f"Use confirmed dimensions when available; otherwise use unconfirmed relative scale for a {dominant_color} {materials} {product_type}.",
        },
        "physics_constraints": [
            "Product cannot float unless visibly suspended or supported.",
            "Component placement must match source imagery and extracted geometry.",
            "Functional axes must point toward what they capture, emit, display, cut, spray, hold, or affect.",
            "Do not invent exact dimensions when source dimensions are unconfirmed.",
        ],
        "negative_spatial_constraints": [
            "Do not copy the reference image as a flat sticker.",
            "Do not use impossible rotations, impossible support, or contradictory perspective.",
            "Do not show screen/display content that contradicts the visible environment.",
            "Do not invent unverified components, accessories, ports, labels, lights, or markings.",
        ],
    }


def build_image_prompt_context(state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    product_data = get_extraction_output(state, "01A")
    visual_data = get_extraction_output(state, "01B")
    image_task = IMAGE_TASKS.get(step_id)
    if image_task is None:
        fail(
            "IMAGE_CONTEXT_STEP_INVALID",
            f"No image task metadata exists for step {step_id}.",
            field="step_id",
            expected="one of IMAGE_PROMPT_STEP_IDS",
            actual=step_id,
        )

    product_profile = product_data.get("product_profile", {})
    if not isinstance(product_profile, dict):
        product_profile = {}

    context: Dict[str, Any] = {
        "reference_tag": state.get("reference_tag", ""),
        "image_task": image_task,
        "product_identity": {
            "product_category": product_data.get("product_category", ""),
            "brand": product_profile.get("brand", ""),
            "product_name": product_profile.get("product_name", ""),
            "model": product_profile.get("model", ""),
            "color": product_profile.get("color", ""),
        },
        "included_accessories": product_data.get("package_contents", []),
        "visual_grounding": {
            "visual_identity": visual_data.get("visual_identity", {}),
            "object_layout_map": visual_data.get("object_layout_map", {}),
            "product_geometry": visual_data.get("product_geometry", {}),
            "image_views": visual_data.get("image_views", {}),
        },
        "style_guidance": {
            "lighting_profile": visual_data.get("lighting_profile", {}),
            "camera_profile": visual_data.get("camera_profile", {}),
            "image_style_lock": state.get("image_style_lock", {}),
        },
        "visual_attribute_subset": pick_visual_attributes(product_data),
        "feature_subset": product_data.get("core_features", []),
        "spatial_image_contract": build_spatial_image_contract(product_data, visual_data),
        "source_images": state.get("source_payload", {}).get("source_images", []),
    }

    if step_id == "11":
        context["amazon_rules"] = {
            "background": "pure white RGB 255,255,255",
            "allowed_objects": "product and included accessories only",
            "text_graphics": "none",
            "frame_fill": "approximately 85%",
            "visibility": "entire product visible",
            "format": "1080x1920 vertical 9:16",
        }
    else:
        context["amazon_rules"] = {
            "product_visibility": "product must be clearly visible and accurately represented",
            "text_graphics": "allowed only for verified features and secondary-image explanation",
            "feature_accuracy": "graphics must represent real product features only",
            "accessory_limit": "do not show accessories not included with the product",
            "format": "1080x1920 vertical 9:16",
        }

    return context


def build_image_generation_context(state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    previous_strategy_key = f"image_strategy_{int(step_id) - 1}"
    strategy = state.get(previous_strategy_key) or state.get("image_strategy")
    if not isinstance(strategy, dict):
        fail(
            "MISSING_IMAGE_STRATEGY",
            f"No image strategy found for image generation step {step_id}",
            field="image_strategy",
            expected=previous_strategy_key,
            actual=type(strategy).__name__,
        )

    product_data = get_extraction_output(state, "01A")
    visual_data = get_extraction_output(state, "01B")

    return {
        "reference_tag": state.get("reference_tag", ""),
        "image_task": {
            "image_number": (int(step_id) - 10) // 2,
            "image_type": strategy.get("image_type", ""),
            "buyer_question": strategy.get("buyer_question", ""),
        },
        "image_generation_prompt": strategy.get("image_generation_prompt", ""),
        "included_accessories": product_data.get("package_contents", []),
        "visual_grounding": {
            "visual_identity": visual_data.get("visual_identity", {}),
            "object_layout_map": visual_data.get("object_layout_map", {}),
            "product_geometry": visual_data.get("product_geometry", {}),
            "image_views": visual_data.get("image_views", {}),
        },
        "style_lock": state.get("image_style_lock", deterministic_style_lock()),
        "spatial_image_contract": build_spatial_image_contract(product_data, visual_data),
        "source_images": state.get("source_payload", {}).get("source_images", []),
    }


def build_model_context_for_step(state: Dict[str, Any], step_id: str) -> Dict[str, Any]:
    if step_id in IMAGE_PROMPT_STEP_IDS:
        return {
            "context_type": "IMAGE_CONTEXT_JSON",
            "image_context": build_image_prompt_context(state, step_id),
        }
    return state


def build_text_input(state: Dict[str, Any], prompt_text: str) -> str:
    context_label = "IMAGE_CONTEXT_JSON" if state.get("context_type") == "IMAGE_CONTEXT_JSON" else "WORKFLOW_STATE_JSON"
    compact_state = json.dumps(state, ensure_ascii=False, indent=2)
    return (
        f"{context_label}:\n{compact_state}\n\n"
        f"INSTRUCTIONS:\n{prompt_text}\n\n"
        f"OUTPUT RULES:\nReturn only valid JSON."
    )


def call_text_step(step_id: str, prompt_text: str, schema: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    json_log("step_start", step_id=step_id, kind="text")
    parsed = get_text_execution_adapter().execute_text(step_id, prompt_text, schema, state)
    json_log("step_end", step_id=step_id, kind="text", output_keys=list(parsed.keys()))
    return parsed


def call_image_generation(
    prompt: str,
    size: str = "1024x1536",
    generation_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    source_images = []
    image_task = {}

    if isinstance(generation_context, dict):
        raw_source_images = generation_context.get("source_images") or []
        if isinstance(raw_source_images, list):
            source_images = [p for p in raw_source_images if isinstance(p, str)]
        raw_image_task = generation_context.get("image_task") or {}
        if isinstance(raw_image_task, dict):
            image_task = raw_image_task

    json_log(
        level="INFO",
        message="Image generation adapter handoff started",
        stage="PROCESSING",
        status="STARTED",
        context={
            "kind": "image_generation",
            "size": size,
            "image_number": image_task.get("image_number"),
            "image_type": image_task.get("image_type"),
            "source_image_count": len(source_images),
            "has_generation_context": generation_context is not None,
        },
    )
    return get_image_execution_adapter().execute_image(
        prompt,
        size=size,
        generation_context=generation_context,
    )


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

    wait_seconds = 0

    if step_kind == "text":
        wait_seconds = TEXT_STEP_WAIT_SECONDS
    elif step_kind == "image_generate":
        wait_seconds = IMAGE_STEP_WAIT_SECONDS

    if wait_seconds <= 0:
        return

    json_log(
        level="INFO",
        message="Model cooldown wait started",
        stage="PROCESSING",
        status="IN_PROGRESS",
        context={
            "operation": "model_cooldown_wait",
            "step_kind": step_kind,
            "wait_seconds": wait_seconds,
        },
    )

    time.sleep(wait_seconds)
    SYNTHETIC_DURATION_MS += wait_seconds * 1000

    json_log(
        level="INFO",
        message="Model cooldown wait completed",
        stage="PROCESSING",
        status="IN_PROGRESS",
        context={
            "operation": "model_cooldown_complete",
            "step_kind": step_kind,
            "wait_seconds": wait_seconds,
        },
    )


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
        image_content = {
            "reference_tag": state.get("reference_tag", ""),
            "spatial_image_contract": state.get("spatial_image_contract", {}),
            "image_prompts": prompts,
        }
        IMAGE_CONTENT_PATH.write_text(json.dumps(image_content, indent=2, ensure_ascii=False), encoding="utf-8")


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
        model_context = build_model_context_for_step(state, step.step_id)
        output = call_text_step(step.step_id, prompt_text, schema, model_context)
        update_state_with_prompt(state, step.step_id, output, step.output_key)

        # Promote key outputs for downstream prompts.
        if step.step_id == "01A":
            state["dataset"] = output
        elif step.step_id == "01B":
            state["visual_grounding"] = output
            state["spatial_image_contract"] = build_spatial_image_contract(
                get_extraction_output(state, "01A"),
                output,
            )
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

        generation_context = build_image_generation_context(state, step.step_id)
        prompt = generation_context["image_generation_prompt"]
        strategy = {
            "image_type": generation_context["image_task"]["image_type"],
            "buyer_question": generation_context["image_task"]["buyer_question"],
            "image_generation_prompt": prompt,
        }

        result = call_image_generation(prompt, generation_context=generation_context)
        image_filename = f"image_{step.step_id}.png"
        saved_path = save_image(result["image_base64"], image_filename)

        output = {
            "reference_tag": state["reference_tag"],
            "generated_image": {
                "image_number": (int(step.step_id) - 10) // 2,
                "image_type": strategy["image_type"],
                "image_generation_prompt": prompt,
                "saved_path": saved_path,
                "revised_prompt": result.get("revised_prompt"),
                "source_images_used": result.get("source_images_used", []),
                "generation_backend": result.get("generation_backend", IMAGE_EXECUTION_BACKEND),
                "generation_model": result.get("generation_model", FLOW_IMAGE_MODEL if IMAGE_EXECUTION_BACKEND == "flow_browser" else IMAGE_MODEL),
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
    parser.add_argument("--stop-after", default=None, help="Run through the matching step id, then stop before the next step (e.g. 01A, 11)")
    parser.add_argument("--stop-before", default=None, help="Stop before the matching step id without executing it (e.g. 01A, 11)")
    parser.add_argument("--restart-from", default=None, help="Restart execution from a specific step id (e.g. 01B)")
    parser.add_argument(
        "--enable-image-generation",
        action="store_true",
        help="Enable image generation steps (requires OPENAI_API_KEY). Default is prompt-only.",
    )
    args = parser.parse_args()

    ensure_dirs()

    if args.stop_after and args.stop_before:
        fail(
            "INVALID_ARGS",
            "--stop-after and --stop-before cannot be used together.",
            field="stop_controls",
            expected="only one of --stop-after or --stop-before",
            actual=f"stop_after={args.stop_after}, stop_before={args.stop_before}",
        )

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
    if args.restart_from:
        restart_step = str(args.restart_from)
        # Clear cached outputs for the restarted step and all subsequent steps in the current plan.
        found_restart = False
        for i, step in enumerate(plan):
            if step.step_id == restart_step:
                start_from = i
                found_restart = True
            if not found_restart:
                continue
            if isinstance(state.get("outputs"), dict):
                state["outputs"].pop(step.step_id, None)
            # Remove promoted/top-level outputs if present.
            if step.kind == "text" and step.output_key in state:
                state.pop(step.output_key, None)
        if found_restart:
            state.pop("last_completed_step", None)
        else:
            fail("INVALID_ARGS", f"--restart-from step id not found in plan: {restart_step}")

    if args.resume and state.get("last_completed_step"):
        last_step = str(state["last_completed_step"])
        for i, step in enumerate(plan):
            if step.step_id == last_step:
                start_from = i + 1
                break

    for i in range(start_from, len(plan)):
        step = plan[i]
        current_step_number = i + 1

        if args.stop_before and step.step_id == args.stop_before:
            json_log(
                level="INFO",
                message=f"Stopped before step {step.step_id}",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={"step_id": step.step_id, "control": "stop_before"},
            )
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

        if args.stop_after and step.step_id == args.stop_after:
            json_log(
                level="INFO",
                message=f"Stopped after step {step.step_id}",
                stage="PROCESSING",
                status="IN_PROGRESS",
                context={"step_id": step.step_id, "control": "stop_after"},
            )
            break

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
