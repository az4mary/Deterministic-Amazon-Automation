# CODE_MANAGE Progress

## STEP 1 - Verify Raw File Ownership

```text
FullName      : D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py
Length        : 222797
LastWriteTime : 25/05/2026 04:39:09

exists: True
absolute_path: D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py
bytes: 222797
modified: 1779701949.2776754
```

## STEP 2 - Read the file from byte 1 to EOF

```text
file: D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py
byte_count: 222797
sha256: ec5054d3173daf973757631945ddfbfcda2cd1400227e78c2a0ed8d52790346f
first_100_bytes: b'# workflow_orchestrator.py\r\nfrom __future__ import annotations\r\n\r\nimport argparse\r\nimport base64\r\nim'
last_100_bytes: b'\r\n    except Exception as e:\r\n        json_log("unhandled_exception", error=str(e))\r\n        raise\r\n'
```

## STEP 3 - Count exact lines and characters

```text
character_count: 217117
line_count: 5672
first_line: '# workflow_orchestrator.py'
last_line: '        raise'
```

## STEP 4 - Produce line-numbered excerpts

```text
--- workflow_orchestrator.py:1-40 ---
    1: # workflow_orchestrator.py
    2: from __future__ import annotations
    3: 
    4: import argparse
    5: import base64
    6: import hashlib
    7: import json
    8: import logging
    9: import os
   10: import subprocess
   11: import re
   12: import inspect
   13: import linecache
   14: import sys
   15: import time
   16: from datetime import datetime, timezone, timedelta
   17: import uuid
   18: from dataclasses import dataclass
   19: from pathlib import Path
   20: from typing import Any, Callable, Dict, List, Optional, Tuple
   21: 
   22: try:
   23:     from openai import OpenAI  # type: ignore
   24: except ModuleNotFoundError:
   25:     OpenAI = None  # type: ignore
   26: from playwright.sync_api import sync_playwright
   27: 
   28: SCRIPT_METADATA = {
   29:     "script_id": "SCRIPT_002",
   30:     "name": "workflow_orchestrator",
   31:     "version": "1.1",
   32:     "category": "PROCESSOR",
   33:     "input_schema": "workflow inputs from local filesystem (raw text + images + prompt files)",
   34:     "output_schema": "workflow_state.json + generated artifacts under output/",
   35:     "dependencies": [],
   36:     "external_libraries": ["openai", "playwright"],
   37:     "status": "ACTIVE",
   38: }
   39: 
   40: ROOT = Path(__file__).resolve().parent

--- workflow_orchestrator.py:2816-2856 ---
 2816:         before_count = self._flow_composer_reference_count(page)
 2817: 
 2818:         # Correct Flow order:
 2819:         # 1. Open the uploaded-media/gallery surface.
 2820:         # 2. Select uploaded image assets.
 2821:         # 3. Click the attach/add/use control.
 2822:         # 4. Confirm visible composer reference chips/assets.
 2823:         opened_gallery = self._flow_open_uploaded_media_gallery(page)
 2824:         selected_count = self._flow_select_gallery_assets(page, expected_count)
 2825:         clicked_attach = self._flow_click_attach_selected_to_composer(page)
 2826: 
 2827:         page.wait_for_timeout(2000)
 2828:         self._dismiss_flow_transient_overlays(page)
 2829: 
 2830:         attached = self._wait_for_flow_references_in_composer(page, expected_count)
 2831:         after_count = self._flow_composer_reference_count(page)
 2832: 
 2833:         if attached:
 2834:             json_log(
 2835:                 level="INFO",
 2836:                 message="Flow reference images attached to composer",
 2837:                 stage="PROCESSING",
 2838:                 status="COMPLETED",
 2839:                 context={
 2840:                     "operation": "flow_reference_images_attached_to_composer",
 2841:                     "source_image_count": expected_count,
 2842:                     "opened_gallery": opened_gallery,
 2843:                     "selected_gallery_asset_count": selected_count,
 2844:                     "clicked_attach_control": clicked_attach,
 2845:                     "before_composer_reference_count": before_count,
 2846:                     "after_composer_reference_count": after_count,
 2847:                 },
 2848:             )
 2849:             return
 2850: 
 2851:         context = {
 2852:             "operation": "flow_reference_gallery_attach_failed",
 2853:             "source_image_count": expected_count,
 2854:             "opened_gallery": opened_gallery,
 2855:             "selected_gallery_asset_count": selected_count,
 2856:             "clicked_attach_control": clicked_attach,

--- workflow_orchestrator.py:5633-5672 ---
 5633:         )
 5634: 
 5635:         if args.stop_after and step.step_id == args.stop_after:
 5636:             json_log(
 5637:                 level="INFO",
 5638:                 message=f"Stopped after step {step.step_id}",
 5639:                 stage="PROCESSING",
 5640:                 status="IN_PROGRESS",
 5641:                 context={"step_id": step.step_id, "control": "stop_after"},
 5642:             )
 5643:             break
 5644: 
 5645:     save_json_atomic(STATE_PATH, state)
 5646:     write_image_prompts(state)
 5647: 
 5648:     output_hash = hashlib.sha256(STATE_PATH.read_bytes()).hexdigest()
 5649:     emit_lifecycle_event(
 5650:         stage="COMPLETED",
 5651:         status="SUCCESS",
 5652:         message="Workflow completed successfully",
 5653:         progress_percent=100,
 5654:         current_step=len(plan),
 5655:         total_steps=len(plan),
 5656:     )
 5657:     emit_terminal_event(
 5658:         status="SUCCESS",
 5659:         message="Workflow completed successfully",
 5660:         output_hash=output_hash,
 5661:         context={"completed_step": state.get("last_completed_step")},
 5662:     )
 5663: 
 5664: 
 5665: if __name__ == "__main__":
 5666:     try:
 5667:         main()
 5668:     except SystemExit:
 5669:         raise
 5670:     except Exception as e:
 5671:         json_log("unhandled_exception", error=str(e))
 5672:         raise
```

## STEP 5 - Generate Python AST symbol map

```text
symbol_count: 143

--- first 10 symbols ---
workflow_orchestrator.py:127-137 FunctionDef build_patch_set_12_static_diagnostics
workflow_orchestrator.py:186-192 ClassDef Step
workflow_orchestrator.py:195-198 FunctionDef next_span_id
workflow_orchestrator.py:201-211 ClassDef PromptExecutionAdapter
workflow_orchestrator.py:202-203 FunctionDef execute_text
workflow_orchestrator.py:205-211 FunctionDef execute_image
workflow_orchestrator.py:214-363 ClassDef OpenAIPromptExecutionAdapter
workflow_orchestrator.py:215-216 FunctionDef __init__
workflow_orchestrator.py:218-228 FunctionDef execute_text
workflow_orchestrator.py:230-363 FunctionDef execute_image

--- last 10 symbols ---
workflow_orchestrator.py:5272-5274 FunctionDef update_state_with_prompt
workflow_orchestrator.py:5277-5285 FunctionDef deterministic_style_lock
workflow_orchestrator.py:5288-5326 FunctionDef apply_step_wait
workflow_orchestrator.py:5357-5360 FunctionDef build_step_plan
workflow_orchestrator.py:5363-5377 FunctionDef write_image_prompts
workflow_orchestrator.py:5380-5466 FunctionDef run_step
workflow_orchestrator.py:5381-5389 FunctionDef build_schema
workflow_orchestrator.py:5468-5477 FunctionDef validate_initial_inputs
workflow_orchestrator.py:5480-5485 FunctionDef resolve_raw_text_path
workflow_orchestrator.py:5488-5662 FunctionDef main
```

## STEP 6 - Search for likely validation/prompt/schema terms

```text
schema: 57
validate: 6
validation: 4
prompt: 246
citation: 0
line: 66
file: 57
chunk: 4
orchestrator: 7

Sample exact-line matches:

schema:
workflow_orchestrator.py:33:     "input_schema": "workflow inputs from local filesystem (raw text + images + prompt files)",
workflow_orchestrator.py:34:     "output_schema": "workflow_state.json + generated artifacts under output/",
workflow_orchestrator.py:191:     schema_builder: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None

validate:
workflow_orchestrator.py:4086:     validate_progress_percent(progress_percent, current_step, total_steps)
workflow_orchestrator.py:4117: def validate_progress_percent(progress_percent: int, current_step: int, total_steps: int) -> None:
workflow_orchestrator.py:5468: def validate_initial_inputs() -> None:

validation:
workflow_orchestrator.py:4040:             "fail_fast": ("ERROR", "Validation failed", "VALIDATION", "FAILED"),
workflow_orchestrator.py:4041:             "unhandled_exception": ("ERROR", "Unhandled exception", "VALIDATION", "FAILED"),
workflow_orchestrator.py:4163: def fail(code: str, message: str, field: str = "", expected: str = "", actual: str = "", stage: str = "VALIDATION") -> None:

prompt:
workflow_orchestrator.py:33:     "input_schema": "workflow inputs from local filesystem (raw text + images + prompt files)",
workflow_orchestrator.py:42: PROMPTS_DIR = ROOT / "docs" / "prompts"
workflow_orchestrator.py:43: PROMPTS_MD_PATH = ROOT / "docs" / "prompts.md"

citation:
total_matches: 0

line:
workflow_orchestrator.py:13: import linecache
workflow_orchestrator.py:448:         deadline = time.time() + (BROWSER_NEW_CHAT_READY_TIMEOUT_MS / 1000.0)
workflow_orchestrator.py:451:         while time.time() < deadline:

file:
workflow_orchestrator.py:33:     "input_schema": "workflow inputs from local filesystem (raw text + images + prompt files)",
workflow_orchestrator.py:40: ROOT = Path(__file__).resolve().parent
workflow_orchestrator.py:189:     prompt_file: Optional[str]

chunk:
workflow_orchestrator.py:3767:   const chunkSize = 0x8000;
workflow_orchestrator.py:3768:   for (let i = 0; i < bytes.length; i += chunkSize) {
workflow_orchestrator.py:3769:     const chunk = bytes.subarray(i, i + chunkSize);

orchestrator:
workflow_orchestrator.py:1: # workflow_orchestrator.py
workflow_orchestrator.py:30:     "name": "workflow_orchestrator",
workflow_orchestrator.py:4038:             "orchestrator_start": ("INFO", "Orchestrator started", "INIT", "STARTED"),
```

## STEP 7 - Required report back

```md
# Codex File Ownership Report

## Verdict

PASS: Codex accessed `workflow_orchestrator.py` as a raw local file from byte 1 to EOF.

## Evidence

### File metadata

- Absolute path: `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py`
- Byte count: `222797`
- Character count: `217117`
- Line count: `5672`
- SHA-256: `ec5054d3173daf973757631945ddfbfcda2cd1400227e78c2a0ed8d52790346f`
- Last modified: `25/05/2026 04:39:09`

### EOF verification

- First 100 bytes: `b'# workflow_orchestrator.py\r\nfrom __future__ import annotations\r\n\r\nimport argparse\r\nimport base64\r\nim'`
- Last 100 bytes: `b'\r\n    except Exception as e:\r\n        json_log("unhandled_exception", error=str(e))\r\n        raise\r\n'`
- First line: `'# workflow_orchestrator.py'`
- Last line: `'        raise'`

### Line-numbered excerpts produced

- Beginning excerpt: yes
- Middle excerpt: yes
- End excerpt: yes

### Symbol map

- AST parse succeeded: yes
- Symbol count: `143`
- First 10 symbols:
  - `workflow_orchestrator.py:127-137 FunctionDef build_patch_set_12_static_diagnostics`
  - `workflow_orchestrator.py:186-192 ClassDef Step`
  - `workflow_orchestrator.py:195-198 FunctionDef next_span_id`
  - `workflow_orchestrator.py:201-211 ClassDef PromptExecutionAdapter`
  - `workflow_orchestrator.py:202-203 FunctionDef execute_text`
  - `workflow_orchestrator.py:205-211 FunctionDef execute_image`
  - `workflow_orchestrator.py:214-363 ClassDef OpenAIPromptExecutionAdapter`
  - `workflow_orchestrator.py:215-216 FunctionDef __init__`
  - `workflow_orchestrator.py:218-228 FunctionDef execute_text`
  - `workflow_orchestrator.py:230-363 FunctionDef execute_image`
- Last 10 symbols:
  - `workflow_orchestrator.py:5272-5274 FunctionDef update_state_with_prompt`
  - `workflow_orchestrator.py:5277-5285 FunctionDef deterministic_style_lock`
  - `workflow_orchestrator.py:5288-5326 FunctionDef apply_step_wait`
  - `workflow_orchestrator.py:5357-5360 FunctionDef build_step_plan`
  - `workflow_orchestrator.py:5363-5377 FunctionDef write_image_prompts`
  - `workflow_orchestrator.py:5380-5466 FunctionDef run_step`
  - `workflow_orchestrator.py:5381-5389 FunctionDef build_schema`
  - `workflow_orchestrator.py:5468-5477 FunctionDef validate_initial_inputs`
  - `workflow_orchestrator.py:5480-5485 FunctionDef resolve_raw_text_path`
  - `workflow_orchestrator.py:5488-5662 FunctionDef main`

### Search verification

- schema: `57`
- validate: `6`
- validation: `4`
- prompt: `246`
- citation: `0`
- line: `66`
- file: `57`
- chunk: `4`
- orchestrator: `7`

## Commands run

```powershell
Get-Item .\workflow_orchestrator.py | Format-List FullName,Length,LastWriteTime
```

```python
from pathlib import Path
path = Path("workflow_orchestrator.py")
print("exists:", path.exists())
print("absolute_path:", path.resolve())
print("bytes:", path.stat().st_size if path.exists() else None)
print("modified:", path.stat().st_mtime if path.exists() else None)
```

```python
from pathlib import Path
import hashlib
path = Path("workflow_orchestrator.py")
data = path.read_bytes()
print("file:", path.resolve())
print("byte_count:", len(data))
print("sha256:", hashlib.sha256(data).hexdigest())
print("first_100_bytes:", repr(data[:100]))
print("last_100_bytes:", repr(data[-100:]))
```

```python
from pathlib import Path
path = Path("workflow_orchestrator.py")
text = path.read_text(encoding="utf-8")
lines = text.splitlines()
print("character_count:", len(text))
print("line_count:", len(lines))
print("first_line:", repr(lines[0] if lines else ""))
print("last_line:", repr(lines[-1] if lines else ""))
```

```python
from pathlib import Path
path = Path("workflow_orchestrator.py")
lines = path.read_text(encoding="utf-8").splitlines()
def show_range(start, end):
    print(f"\n--- {path}:{start}-{end} ---")
    for i in range(start, min(end, len(lines)) + 1):
        print(f"{i:>5}: {lines[i-1]}")
line_count = len(lines)
show_range(1, min(40, line_count))
mid = max(1, line_count // 2)
show_range(max(1, mid - 20), min(line_count, mid + 20))
show_range(max(1, line_count - 39), line_count)
```

```python
from pathlib import Path
import ast
path = Path("workflow_orchestrator.py")
text = path.read_text(encoding="utf-8")
tree = ast.parse(text)
symbols = []
for node in ast.walk(tree):
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        symbols.append((node.lineno, getattr(node, "end_lineno", node.lineno), type(node).__name__, node.name))
symbols.sort()
```

```python
from pathlib import Path
import re
path = Path("workflow_orchestrator.py")
lines = path.read_text(encoding="utf-8").splitlines()
terms = ["schema", "validate", "validation", "prompt", "citation", "line", "file", "chunk", "orchestrator"]
for term in terms:
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    count = 0
    for i, line in enumerate(lines, start=1):
        if pattern.search(line):
            count += 1
    print(term, count)
```

## Errors or limitations

None. No encoding, path, permission, dependency, or truncation issue blocked the required checks.

## Conclusion

This proves Codex has raw local-file access to `workflow_orchestrator.py` rather than relying only on chunked/indexed retrieval. The evidence includes direct filesystem metadata, byte-level EOF reads with SHA-256 and first/last bytes, exact character and line counts, exact line-numbered excerpts from beginning/middle/end, an AST symbol map with line ranges, and deterministic direct-file search results.

## STEP 8 - Inspect this repo

````md
# STEP 8 Repo Inspection Report

### Verdict

PASS

### Repo identity

- Root: `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch`
- Branch: `codex_branch`
- Git status summary: clean

### Top-level inventory

- `.codex_validation_patch_set_07/`
- `.git/`
- `data/`
- `diagnostic/`
- `docs/`
- `messenger/`
- `output/`
- `scripts/`
- `README.md`
- `workflow_orchestrator.py`

### Relevant files discovered

#### Python files

- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\amazon_listing_markdown_exporter.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\chatgpt_workflow_TESTED.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\flow_attach_smoke.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\flow_attach_smoke_settings.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\flow_clipboard_paste_smoke.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\flow_plus_upload_smoke.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\flow_settings_inspect.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\flow_settings_smoke.py`

#### Prompt / markdown files

- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\README.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\.codex_validation_patch_set_07\validation_output.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\data\raw_product_input.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\data\SYSTEM_ORCHESTRATOR.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\data\workflow.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\docs\Complete_Final_Implementation_Plan_Before_STATE_17.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\docs\general.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\docs\PATCH_SET_FORMAT.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\docs\prompts.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\WORKFLOW_RULES.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_INSTRUCTIONS.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_Progress.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_response.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\output\amazon_listing_copy_paste.md`

#### Test files

No `tests/`, `test/`, `test_*.py`, or `*_test.py` files were discovered.

#### Config / dependency files

No `pyproject.toml`, `requirements.txt`, `setup.cfg`, `setup.py`, `pytest.ini`, `mypy.ini`, `ruff.toml`, `.ruff.toml`, or `tox.ini` files were discovered.

#### Generated / output folders

- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\output`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\scripts\output`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\.codex_validation_patch_set_07`

### Likely workflow entrypoints

- `workflow_orchestrator.py:5488` - `main()`
- `workflow_orchestrator.py:5497` - `argparse.ArgumentParser(...)`
- `workflow_orchestrator.py:5357` - `build_step_plan(...)`
- `workflow_orchestrator.py:5380` - `run_step(...)`
- `workflow_orchestrator.py:5665` - `if __name__ == "__main__":`

### Risks or gaps

- No local test suite files were discovered.
- No dependency/config files were discovered.
- `output/`, `scripts/output/`, and `.codex_validation_patch_set_07/` appear generated or validation-output related.
- One attempted `rg` command using a shell glob for `scripts/*.py` returned a Windows path/glob error; direct filesystem inspection and `workflow_orchestrator.py` searches still succeeded.

### Commands run

```powershell
Get-Location; git status --short; git branch --show-current; Get-ChildItem -Force | Select-Object Mode,Length,LastWriteTime,Name
Get-ChildItem -Recurse -File -Include *.py -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|__pycache__|\\.venv\\|\\venv\\|\\env\\' } | Select-Object -ExpandProperty FullName
Get-ChildItem -Recurse -File -Include *.md -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|__pycache__|\\.venv\\|\\venv\\|\\env\\' } | Select-Object -ExpandProperty FullName
Get-ChildItem -Recurse -File -Include pyproject.toml,requirements.txt,setup.cfg,setup.py,pytest.ini,mypy.ini,ruff.toml,.ruff.toml,tox.ini -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|__pycache__|\\.venv\\|\\venv\\|\\env\\' } | Select-Object -ExpandProperty FullName
Get-ChildItem -Recurse -Directory -Include tests,test,docs,prompts,output,generated -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|__pycache__|\\.venv\\|\\venv\\|\\env\\' } | Select-Object -ExpandProperty FullName
Get-ChildItem -Recurse -File -Include test_*.py,*_test.py -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|__pycache__|\\.venv\\|\\venv\\|\\env\\' } | Select-Object -ExpandProperty FullName
rg -n "if __name__|def main\(|argparse|build_step_plan|run_step\(" workflow_orchestrator.py scripts/*.py
```

### Next recommended step

Proceed to STEP 9 after confirmation.
````

## STEP 9 - Find every caller of this function

````md
# STEP 9 Caller Discovery Report

## Verdict

PASS

## Target function

`validate_initial_inputs`

## Definition found

- File: `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py`
- Lines: `5468-5477`

## Direct callers found

- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py:5527`

## Other references

- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_INSTRUCTIONS.md:447`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_INSTRUCTIONS.md:467`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_INSTRUCTIONS.md:468`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_INSTRUCTIONS.md:477`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_INSTRUCTIONS.md:518`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_response.md:320`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_Progress.md:191`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_Progress.md:219`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_Progress.md:311`

## Methods used

- Text search: `rg -n "validate_initial_inputs" .`
- Text search: `rg -n "def validate_initial_inputs|validate_initial_inputs\(" .`
- AST inspection: parsed local `*.py` files and reported `FunctionDef` plus `Call` nodes matching `validate_initial_inputs`

## Confidence

High

The direct code definition and call were found by both exact text search and AST inspection. Workflow markdown references were identified separately as non-code references.

## Commands run

```powershell
rg -n "validate_initial_inputs" .
rg -n "def validate_initial_inputs|validate_initial_inputs\(" .
```

```python
from pathlib import Path
import ast

target = "validate_initial_inputs"

for path in Path(".").rglob("*.py"):
    if any(part in {".git", "__pycache__", ".venv", "venv", "env"} for part in path.parts):
        continue

    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except Exception as exc:
        print(f"SKIP {path}: {exc}")
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == target:
            print(f"DEF  {path}:{node.lineno}-{getattr(node, 'end_lineno', node.lineno)}")

        if isinstance(node, ast.Call):
            func = node.func
            name = None

            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr

            if name == target:
                print(f"CALL {path}:{node.lineno}")
```

## Errors or limitations

No parsing errors were reported. Dynamic invocation through strings, reflection, or generated code cannot be fully ruled out by AST call tracing, but exact text search found no additional Python-code callers.

## Next recommended step

Proceed to STEP 10 after confirmation.
````

## STEP 10 - Validate schema against `prompts.md`

````md
# STEP 10 Schema-vs-Prompts Validation Report

## Verdict

PASS

## Files inspected

- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\docs\prompts.md`
- `D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\docs\prompts\`

## Schema sources found

- `workflow_orchestrator.py:4401-4407` - `build_text_schema`
- `workflow_orchestrator.py:4410-4444` - `schema_1a`
- `workflow_orchestrator.py:4447-4617` - `schema_1b`
- `workflow_orchestrator.py:4620-4629` - `schema_title`
- `workflow_orchestrator.py:4632-4646` - `schema_bullets`
- `workflow_orchestrator.py:4649-4658` - `schema_description`
- `workflow_orchestrator.py:4661-4670` - `schema_backend`
- `workflow_orchestrator.py:4673-4700` - `schema_search_intent`
- `workflow_orchestrator.py:4703-4732` - `schema_aplus`
- `workflow_orchestrator.py:4735-4755` - `schema_specs`
- `workflow_orchestrator.py:4758-4776` - `schema_faq`
- `workflow_orchestrator.py:4779-4800` - `schema_social`
- `workflow_orchestrator.py:4803-4864` - `schema_image_prompt`
- `workflow_orchestrator.py:4867-4881` - `read_prompt_file`
- `workflow_orchestrator.py:4919-4939` - `read_prompt_from_prompts_md`
- `workflow_orchestrator.py:5100-5163` - `build_image_prompt_context`
- `workflow_orchestrator.py:5166-5199` - `build_image_generation_context`
- `workflow_orchestrator.py:5357-5360` - `build_step_plan`

## Prompt sources found

- `docs/prompts.md:1-70` - `PROMPT 1A`
- `docs/prompts.md:71-185` - `PROMPT 1B`
- `docs/prompts.md:186-237` - `PROMPT 2`
- `docs/prompts.md:238-290` - `PROMPT 3`
- `docs/prompts.md:291-342` - `PROMPT 4`
- `docs/prompts.md:343-387` - `PROMPT 5`
- `docs/prompts.md:388-444` - `PROMPT 6`
- `docs/prompts.md:445-523` - `PROMPT 7`
- `docs/prompts.md:524-577` - `PROMPT 8`
- `docs/prompts.md:578-653` - `PROMPT 9`
- `docs/prompts.md:654-727` - `PROMPT 10`
- `docs/prompts.md:728-846` - `PROMPT 11`
- `docs/prompts.md:847-935` - `PROMPT 12`
- `docs/prompts.md:936-1058` - `PROMPT 13`
- `docs/prompts.md:1059-1131` - `PROMPT 14`
- `docs/prompts.md:1132-1254` - `PROMPT 15`
- `docs/prompts.md:1255-1327` - `PROMPT 16`
- `docs/prompts.md:1328-1450` - `PROMPT 17`
- `docs/prompts.md:1451-1523` - `PROMPT 18`
- `docs/prompts.md:1524-1646` - `PROMPT 19`
- `docs/prompts.md:1647-1719` - `PROMPT 20`
- `docs/prompts.md:1720-1842` - `PROMPT 21`
- `docs/prompts.md:1843-1915` - `PROMPT 22`
- `docs/prompts.md:1916-2038` - `PROMPT 23`
- `docs/prompts.md:2039-2111` - `PROMPT 24`
- `docs/prompts\` contains no prompt files.

## Field comparison

| Field / concept | Schema expectation | Prompt expectation | Status | Evidence |
|---|---|---|---|---|
| Prompt 1A extraction | `schema_1a` requires `reference_tag`, `product_category`, `product_profile`, `core_features`, `attributes`, `additional_attributes`, `package_contents`, `product_summary` | `PROMPT 1A` includes the same output keys | PASS | `workflow_orchestrator.py:4410-4444`; `docs/prompts.md:1-70` |
| Prompt 1B spatial contract | `schema_1b` requires `spatial_image_contract` with nested physical-scene fields | `PROMPT 1B` includes `spatial_image_contract` and nested fields | PASS | `workflow_orchestrator.py:4447-4617`; `docs/prompts.md:71-185` |
| Title output | `schema_title` requires `reference_tag`, `amazon_product_title` | `PROMPT 2` includes `reference_tag`, `amazon_product_title` | PASS | `workflow_orchestrator.py:4620-4629`; `docs/prompts.md:186-237` |
| Bullet output | `schema_bullets` requires `reference_tag`, `amazon_bullet_points` | `PROMPT 3` includes `reference_tag`, `amazon_bullet_points` | PASS | `workflow_orchestrator.py:4632-4646`; `docs/prompts.md:238-290` |
| Description output | `schema_description` requires `reference_tag`, `amazon_product_description` | `PROMPT 4` includes `reference_tag`, `amazon_product_description` | PASS | `workflow_orchestrator.py:4649-4658`; `docs/prompts.md:291-342` |
| Backend search output | `schema_backend` requires `reference_tag`, `amazon_backend_search_terms` | `PROMPT 5` includes `reference_tag`, `amazon_backend_search_terms` | PASS | `workflow_orchestrator.py:4661-4670`; `docs/prompts.md:343-387` |
| Search intent output | `schema_search_intent` requires five keyword arrays | `PROMPT 6` includes all five arrays | PASS | `workflow_orchestrator.py:4673-4700`; `docs/prompts.md:388-444` |
| A+ content output | `schema_aplus` requires `brand_story` and four feature sections | `PROMPT 7` includes `brand_story` and four feature sections | PASS | `workflow_orchestrator.py:4703-4732`; `docs/prompts.md:445-523` |
| Technical specs output | `schema_specs` requires nested `technical_specifications` with `Brand`, `Product Name`, `Model`, `Color`, `Attributes` | `PROMPT 8` includes same nested structure | PASS | `workflow_orchestrator.py:4735-4755`; `docs/prompts.md:524-577` |
| FAQ output | `schema_faq` requires `reference_tag`, `customer_faq` array of question/answer items | `PROMPT 9` includes `reference_tag`, `customer_faq`, `question`, `answer` | PASS | `workflow_orchestrator.py:4758-4776`; `docs/prompts.md:578-653` |
| Social output | `schema_social` requires three posts with post number, title, text, tags, hashtags | `PROMPT 10` includes matching fields | PASS | `workflow_orchestrator.py:4779-4800`; `docs/prompts.md:654-727` |
| Image strategy outputs | `schema_image_prompt` requires `reference_tag`, `image_strategy`, `spatial_scene_brief`, `image_generation_prompt` | Prompts 11, 13, 15, 17, 19, 21, 23 include matching strategy keys | PASS | `workflow_orchestrator.py:4803-4864`; `docs/prompts.md:728-846`, `936-1058`, `1132-1254`, `1328-1450`, `1524-1646`, `1720-1842`, `1916-2038` |
| Image generation prompts | image generation steps 12, 14, 16, 18, 20, 22, 24 have no JSON schema builder | Prompts include generation instructions and `generated_image`-style fields where present | PASS / N/A | `workflow_orchestrator.py:5342`, `5344`, `5346`, `5348`, `5350`, `5352`, `5354`; `docs/prompts.md:847-935`, `1059-1131`, `1255-1327`, `1451-1523`, `1647-1719`, `1843-1915`, `2039-2111` |

## Mismatches

No schema-vs-prompt mismatches were found in the inspected current files.

## Missing or ambiguous items

- `docs/prompts\` exists but contains no prompt files; prompt fallback is `docs/prompts.md`.
- Image generation steps do not use a text JSON schema builder; they are handled as `image_generate` steps.
- No local tests exist yet to lock these schema/prompt alignments.

## Recommended patch plan

No production patch is recommended from STEP 10.

Recommended test target for STEP 11, if approved:

- Add focused tests that assert the current `docs/prompts.md` prompt keys remain aligned with `workflow_orchestrator.py` schema builders for `schema_1b`, `schema_aplus`, `schema_specs`, and `schema_image_prompt`.

## Commands run

```powershell
rg -n "build_schema|schema_builder|prompt_file|PROMPTS_MD_PATH|PROMPTS_DIR|required|expected|json|fields" workflow_orchestrator.py docs
Get-ChildItem -Recurse -File docs | Select-Object -ExpandProperty FullName
rg -n '^#|\"[A-Za-z0-9_]+\"\s*:|required|expected|json|fields|reference_tag|technical_specifications|brand_story|spatial_image_contract|package_contents' docs/prompts.md docs/prompts workflow_orchestrator.py
```

```python
from pathlib import Path
import ast
text = Path("workflow_orchestrator.py").read_text(encoding="utf-8")
mod = ast.parse(text)
for node in ast.walk(mod):
    if isinstance(node, ast.FunctionDef) and (node.name.startswith("schema") or node.name in {"build_text_schema","build_step_plan","read_prompt_file","read_prompt_from_prompts_md","build_image_prompt_context","build_image_generation_context"}):
        print(f"{node.name}: workflow_orchestrator.py:{node.lineno}-{getattr(node,'end_lineno',node.lineno)}")
```

```python
from pathlib import Path
import re
text = Path("docs/prompts.md").read_text(encoding="utf-8")
headings = [(m.start(), m.end(), m.group(1).strip()) for m in re.finditer(r"(?m)^#\s+PROMPT\s+(.+?)\s*$", text)]
for idx, (start, end_heading, key) in enumerate(headings):
    end = headings[idx+1][0] if idx+1 < len(headings) else len(text)
    section = text[end_heading:end]
    keys = sorted(set(re.findall(r'"([A-Za-z_][A-Za-z0-9_ ]*)"\s*:', section)))
    print(f"PROMPT {key}: docs/prompts.md:{text[:start].count(chr(10))+1}-{text[:end].count(chr(10))+1}")
    print("keys:", ", ".join(keys[:80]))
```

```python
from pathlib import Path
text = Path("docs/prompts.md").read_text(encoding="utf-8")
checks = {
    "brand_story exact": '"brand_story": ""' in text,
    "seller_or_brand_story absent": '"seller_or_brand_story": ""' not in text,
    "spatial_image_contract": '"spatial_image_contract"' in text,
    "technical_specifications": '"technical_specifications"' in text,
    "prompt8 top package_contents block absent": ' },\n "package_contents": []\n}' not in text,
    "Why do I need it": "Why do I need it?" in text,
    "When would I use it": "When would I use it?" in text,
    "What technology makes it better": "What technology makes it better?" in text,
    "What specifications matter": "What specifications matter?" in text,
}
for k, v in checks.items():
    print(f"{k}: {v}")
```

One scratch AST helper command failed with a Python `SyntaxError` and was rerun with the corrected AST extraction command above. No files were changed by the failed helper.

## Next recommended step

Proceed to STEP 11 only after user approval of the patch/test target.
````

## STEP 11 - Write tests

````md
# STEP 11 Test-Writing Report

## Verdict

PARTIAL

## Test target

Schema/prompt alignment markers approved by CODE_MANAGE after STEP 10:

- `schema_1b`
- `schema_aplus`
- `schema_specs`
- `schema_image_prompt`

The tests verify that required schema keys and buyer-question markers remain present in `docs/prompts.md` and `workflow_orchestrator.py`.

## Files changed

- `tests/test_schema_prompt_alignment.py`

## Tests added

- `test_schema_1b_spatial_contract_keys_present_in_prompts`
  - validates `spatial_image_contract` and nested spatial contract markers are present in both `workflow_orchestrator.py` and `docs/prompts.md`
- `test_schema_aplus_uses_brand_story_prompt_key`
  - validates `brand_story` is present and obsolete `seller_or_brand_story` is absent from prompts
- `test_schema_specs_matches_prompt_technical_specifications_shape`
  - validates `technical_specifications` required keys align and the old invalid top-level `package_contents` block is absent
- `test_schema_image_prompt_buyer_questions_match_step_plan`
  - validates image buyer questions match the current `STEP_PLAN` wording and obsolete buyer-question wording is absent from prompts

## Commands run

```powershell
git status --short
rg --files | rg "(^|/)tests?/|test_.*\.py$|.*_test\.py$"
Test-Path tests; Get-ChildItem -Force | Select-Object Name,Mode
python -m pytest tests/test_schema_prompt_alignment.py
python -m py_compile tests/test_schema_prompt_alignment.py
git status --short
git diff --stat
git diff --no-index -- /dev/null tests/test_schema_prompt_alignment.py
```

## Results

- Narrow test result: `PARTIAL` - `python -m pytest tests/test_schema_prompt_alignment.py` failed because `pytest` is not installed.
- Full test result if run: not run.
- Syntax validation: `PASS` - `python -m py_compile tests/test_schema_prompt_alignment.py`

## Git diff summary

```text
?? tests/
```

`git diff --stat` did not include the untracked test file. `git diff --no-index -- /dev/null tests/test_schema_prompt_alignment.py` produced the new-file diff.

## Full diff

```diff
diff --git a/tests/test_schema_prompt_alignment.py b/tests/test_schema_prompt_alignment.py
new file mode 100644
index 0000000..2531c92
--- /dev/null
+++ b/tests/test_schema_prompt_alignment.py
@@ -0,0 +1,91 @@
+from pathlib import Path
+
+
+ROOT = Path(__file__).resolve().parents[1]
+WORKFLOW = ROOT / "workflow_orchestrator.py"
+PROMPTS = ROOT / "docs" / "prompts.md"
+
+
+def read_workflow() -> str:
+    return WORKFLOW.read_text(encoding="utf-8")
+
+
+def read_prompts() -> str:
+    return PROMPTS.read_text(encoding="utf-8")
+
+
+def test_schema_1b_spatial_contract_keys_present_in_prompts() -> None:
+    workflow = read_workflow()
+    prompts = read_prompts()
+
+    required = [
+        '"spatial_image_contract"',
+        '"product_dimensions"',
+        '"product_3d_geometry"',
+        '"component_interaction_rules"',
+        '"photographer_scene_rules"',
+        '"physics_constraints"',
+        '"negative_spatial_constraints"',
+    ]
+
+    for marker in required:
+        assert marker in workflow
+        assert marker in prompts
+
+
+def test_schema_aplus_uses_brand_story_prompt_key() -> None:
+    workflow = read_workflow()
+    prompts = read_prompts()
+
+    assert '"brand_story"' in workflow
+    assert '"brand_story": ""' in prompts
+    assert '"seller_or_brand_story": ""' not in prompts
+
+
+def test_schema_specs_matches_prompt_technical_specifications_shape() -> None:
+    workflow = read_workflow()
+    prompts = read_prompts()
+
+    required = [
+        '"technical_specifications"',
+        '"Brand"',
+        '"Product Name"',
+        '"Model"',
+        '"Color"',
+        '"Attributes"',
+    ]
+
+    for marker in required:
+        assert marker in workflow
+        assert marker in prompts
+
+    assert ' },\n "package_contents": []\n}' not in prompts
+
+
+def test_schema_image_prompt_buyer_questions_match_step_plan() -> None:
+    workflow = read_workflow()
+    prompts = read_prompts()
+
+    required_questions = [
+        "What is this product?",
+        "Why do I need it?",
+        "What problem does this product solve?",
+        "When would I use it?",
+        "What technology makes it better?",
+        "How easy is it to install or use?",
+        "What specifications matter?",
+    ]
+
+    for question in required_questions:
+        assert question in workflow
+        assert question in prompts
+
+    forbidden_questions = [
+        "Why do I need this product?",
+        "When would I use this product?",
+        "What technology makes this product better?",
+        "What specifications or technical details matter?",
+    ]
+
+    for question in forbidden_questions:
+        assert question not in prompts
```

## Errors or limitations

- `pytest` is unavailable in the local Python environment:
  - Command: `python -m pytest tests/test_schema_prompt_alignment.py`
  - Exit code: `1`
  - Error: `D:\TOOLS\Python314\python.exe: No module named pytest`
- No dependencies were installed.
- Test syntax was validated with `python -m py_compile`.

## Next recommended step

Proceed to STEP 12 after confirmation. Because STEP 10 found no production patch requirement, STEP 12 should either be recorded as no production parser patch needed or CODE_MANAGE should provide a concrete parser/source target before any production edit.
````

## STEP 12 - Patch the parser

````md
# STEP 12 Parser Patch Report

## Verdict

PASS

## Defect patched

No production parser defect was patched.

CODE_MANAGE confirmed STEP 12 should be recorded as a no-op production parser patch because STEP 10 found no schema-vs-prompt mismatch and STEP 11 added alignment tests only.

## Files changed

No files were changed during STEP 12.

Existing STEP 11 artifact preserved:

- `tests/test_schema_prompt_alignment.py`

## Functions changed

None.

## Patch summary

No production code was modified.

`workflow_orchestrator.py` was not edited.

## Commands run

```powershell
git status --short
git diff --stat
git diff
python -m pytest
python -m py_compile tests\test_schema_prompt_alignment.py
git status --short
git diff --stat
git diff
```

## Results

- Relevant tests: `python -m py_compile tests\test_schema_prompt_alignment.py` passed.
- Full pytest: `python -m pytest` failed because `pytest` is not installed.
  - Exit code: `1`
  - Error: `D:\TOOLS\Python314\python.exe: No module named pytest`

## Git diff summary

```text
?? tests/
```

`git diff --stat` produced no output.

## Full diff

`git diff` produced no output.

## Risks

- `pytest` remains unavailable in the local Python environment.
- The STEP 11 test file is still untracked and preserved.

Proceed to STEP 13 after confirmation.
````

## STEP 13 - Run pytest / ruff / mypy

````md
# STEP 13 Validation Stack Report

## Verdict

PARTIAL

## Commands run

```powershell
rg --files | rg "pyproject\.toml|pytest\.ini|setup\.cfg|tox\.ini|mypy\.ini|ruff\.toml|\.ruff\.toml|requirements\.txt"
python -m pytest
python -m ruff check .
python -m mypy .
ruff check .
mypy .
git status --short
```

## Results

| Tool | Command | Result | Notes |
|---|---|---|---|
| pytest | `python -m pytest` | SKIPPED | `pytest` is not installed. |
| ruff | `python -m ruff check .` | SKIPPED | `ruff` Python module is not installed. |
| ruff | `ruff check .` | SKIPPED | `ruff` command is not available. |
| mypy | `python -m mypy .` | SKIPPED | `mypy` Python module is not installed. |
| mypy | `mypy .` | SKIPPED | `mypy` command is not available. |

## Failure details

- No validation failures were produced by project code because the validation tools could not run.

## Missing tools

- `pytest`
  - Command: `python -m pytest`
  - Exit code: `1`
  - Error: `D:\TOOLS\Python314\python.exe: No module named pytest`
- `ruff`
  - Command: `python -m ruff check .`
  - Exit code: `1`
  - Error: `D:\TOOLS\Python314\python.exe: No module named ruff`
  - Command: `ruff check .`
  - Exit code: `1`
  - Error: `ruff : The term 'ruff' is not recognized as the name of a cmdlet, function, script file, or operable program.`
- `mypy`
  - Command: `python -m mypy .`
  - Exit code: `1`
  - Error: `D:\TOOLS\Python314\python.exe: No module named mypy`
  - Command: `mypy .`
  - Exit code: `1`
  - Error: `mypy : The term 'mypy' is not recognized as the name of a cmdlet, function, script file, or operable program.`

## Git status

```text
?? tests/
```

Proceed to STEP 14 after confirmation.
````

## STEP 14 - Produce a diff

````md
# STEP 14 Diff Package Report

## Verdict

PARTIAL

## Changed files

- `tests/test_schema_prompt_alignment.py` - test
- `tests/__pycache__/test_schema_prompt_alignment.cpython-314.pyc` - generated/output

## Diff stat

`git diff --stat` produced no output because the current changed files are untracked.

Explicit untracked test-file diff stat:

```text
 /dev/null => tests/test_schema_prompt_alignment.py | 91 ++++++++++++++++++++++
 1 file changed, 91 insertions(+)
```

## Full diff

`git diff` produced no output because the current changed files are untracked.

Explicit untracked test-file diff:

```diff
diff --git a/tests/test_schema_prompt_alignment.py b/tests/test_schema_prompt_alignment.py
new file mode 100644
index 0000000..2531c92
--- /dev/null
+++ b/tests/test_schema_prompt_alignment.py
@@ -0,0 +1,91 @@
+from pathlib import Path
+
+
+ROOT = Path(__file__).resolve().parents[1]
+WORKFLOW = ROOT / "workflow_orchestrator.py"
+PROMPTS = ROOT / "docs" / "prompts.md"
+
+
+def read_workflow() -> str:
+    return WORKFLOW.read_text(encoding="utf-8")
+
+
+def read_prompts() -> str:
+    return PROMPTS.read_text(encoding="utf-8")
+
+
+def test_schema_1b_spatial_contract_keys_present_in_prompts() -> None:
+    workflow = read_workflow()
+    prompts = read_prompts()
+
+    required = [
+        '"spatial_image_contract"',
+        '"product_dimensions"',
+        '"product_3d_geometry"',
+        '"component_interaction_rules"',
+        '"photographer_scene_rules"',
+        '"physics_constraints"',
+        '"negative_spatial_constraints"',
+    ]
+
+    for marker in required:
+        assert marker in workflow
+        assert marker in prompts
+
+
+def test_schema_aplus_uses_brand_story_prompt_key() -> None:
+    workflow = read_workflow()
+    prompts = read_prompts()
+
+    assert '"brand_story"' in workflow
+    assert '"brand_story": ""' in prompts
+    assert '"seller_or_brand_story": ""' not in prompts
+
+
+def test_schema_specs_matches_prompt_technical_specifications_shape() -> None:
+    workflow = read_workflow()
+    prompts = read_prompts()
+
+    required = [
+        '"technical_specifications"',
+        '"Brand"',
+        '"Product Name"',
+        '"Model"',
+        '"Color"',
+        '"Attributes"',
+    ]
+
+    for marker in required:
+        assert marker in workflow
+        assert marker in prompts
+
+    assert ' },\n "package_contents": []\n}' not in prompts
+
+
+def test_schema_image_prompt_buyer_questions_match_step_plan() -> None:
+    workflow = read_workflow()
+    prompts = read_prompts()
+
+    required_questions = [
+        "What is this product?",
+        "Why do I need it?",
+        "What problem does this product solve?",
+        "When would I use it?",
+        "What technology makes it better?",
+        "How easy is it to install or use?",
+        "What specifications matter?",
+    ]
+
+    for question in required_questions:
+        assert question in workflow
+        assert question in prompts
+
+    forbidden_questions = [
+        "Why do I need this product?",
+        "When would I use this product?",
+        "What technology makes this product better?",
+        "What specifications or technical details matter?",
+    ]
+
+    for question in forbidden_questions:
+        assert question not in prompts
```

No textual diff was produced for `tests/__pycache__/test_schema_prompt_alignment.cpython-314.pyc`.

## Validation summary

- pytest: skipped/unavailable - `D:\TOOLS\Python314\python.exe: No module named pytest`
- ruff: skipped/unavailable - module and command unavailable
- mypy: skipped/unavailable - module and command unavailable

## Review notes

- What changed: STEP 11 added a focused schema/prompt alignment test file.
- Why it changed: CODE_MANAGE approved tests to lock the current schema/prompt alignment after STEP 10 found no production patch requirement.
- How to review it: inspect `tests/test_schema_prompt_alignment.py` and verify the marker assertions match `workflow_orchestrator.py` and `docs/prompts.md`.
- Rollback approach: remove the untracked `tests/` directory if CODE_MANAGE or the user rejects the test artifact.

## Commands run

```powershell
git status --short
git status --short --untracked-files=all
git diff --stat
git diff
git diff --no-index --stat -- /dev/null tests/test_schema_prompt_alignment.py
git diff --no-index -- /dev/null tests/test_schema_prompt_alignment.py
```

## Final recommendation

Ready for manager review as a diff package, with validation limited by unavailable local tools.
````
