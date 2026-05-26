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
