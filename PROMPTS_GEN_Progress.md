# PROMPTS_GEN Progress

## STEP 1 - PATCH_12K1

Status: CONFIRMED

Local checkpoint time:
- `2026-05-21T03:17:48.5276637-05:00`

## STEP 2 - PATCH_12K2

Status: APPLIED

Local checkpoint time:
- `2026-05-21T03:27:55.8640677-05:00`

## STEP 3 - PATCH_12K3

Status: APPLIED

Local checkpoint time:
- `2026-05-21T03:38:04.0655951-05:00`

## STEP 4 - PATCH_12K4

Status: APPLIED

Local checkpoint time:
- `2026-05-21T03:51:27.4680398-05:00`

## STEP 5 - K-Validation 1

Status: PASS

Local checkpoint time:
- `2026-05-21T03:57:36.2630068-05:00`

## STEP 6 - K-Validation 2

Status: PASS

Local checkpoint time:
- `2026-05-21T04:03:52.1189295-05:00`

## STEP 7 - K-Validation 3

Status: PASS

Local checkpoint time:
- `2026-05-21T04:10:35.2239674-05:00`

## Resume STEP 7 after PATCH_12K

Status: FAILED_BLOCKED

Local checkpoint time:
- `2026-05-21T04:19:02.4000957-05:00`

Blocking rule:
- NEXT STEP BLOCKED
- No future-step edits/proceeding

Failure:
- `FLOW_PROMPT_INPUT_MISSING`
- `{"error_code": "FLOW_PROMPT_INPUT_MISSING", "field": "flow_prompt_input", "expected": "visible Flow prompt textarea/textbox/contenteditable composer", "actual": "url=https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28; last_error=", "file": "D:\\PROJECTS\\GITHUB\\az4mary\\Deterministic-Amazon-Automation-codex_branch\\workflow_orchestrator.py", "line": 1887, "snippet": "fail(", "trace_id": "fe78c8d6703134fe6184bd624f9936e8"}`

Messenger request:
- Do you need any additional files/logs for troubleshooting?

## STEP 1 - PATCH_12L1

Status: APPLIED

Local checkpoint time:
- `2026-05-21T04:33:39.6839256-05:00`

## STEP 2 - PATCH_12L2

Status: APPLIED

Local checkpoint time:
- `2026-05-21T04:38:48.5988969-05:00`

## STEP 3 - PATCH_12L3

Status: APPLIED

Local checkpoint time:
- `2026-05-21T04:45:02.9316067-05:00`

## STEP 4 - L-Validation 1

Status: PASS

Local checkpoint time:
- `2026-05-21T04:51:17.8117892-05:00`

## STEP 5 - L-Validation 2

Status: PASS

Local checkpoint time:
- `2026-05-21T04:57:49.5076432-05:00`

## STEP 6 - L-Validation 3

Status: PASS

Local checkpoint time:
- `2026-05-21T05:04:27.9937983-05:00`

## Resume STEP 7 after PATCH_12L

Status: FAILED_BLOCKED

Local checkpoint time:
- `2026-05-21T05:31:24.9453471-05:00`

Blocking rule:
- NEXT STEP BLOCKED
- No future-step edits/proceeding

Failure:
- `FLOW_IMAGE_GENERATION_TIMEOUT`
- `{"error_code": "FLOW_IMAGE_GENERATION_TIMEOUT", "field": "flow_generated_image", "expected": "generated Flow output captured as base64 image", "actual": "", "file": "D:\\PROJECTS\\GITHUB\\az4mary\\Deterministic-Amazon-Automation-codex_branch\\workflow_orchestrator.py", "line": 2582, "snippet": "fail(", "trace_id": "fe78c8d6703134fe6184bd624f9936e8"}`

Messenger request:
- Do you need any additional files/logs for troubleshooting?

## Expected checks

```json
{
  "expected": [
    "resume starts at step 12",✅
    "Image generation adapter handoff started",✅
    "Flow adapter reused shared browser session",✅ opened in new Tab
    "Flow page ready",✅
    "Flow reference images uploaded",✅uploaded to image gallery
    "Flow reference images attached to composer",❌attached button clicked, image gallery opened but image not selected or attached to composer.
    "Flow model selected",✅
    "Flow prompt box filled",✅prompt available in composer
    "Flow image prompt submitted",❌
    "Flow generated image captured",❌
    "output/generated_images/image_12.png exists",❌
    "generated_image_1.generation_backend=flow_browser",❌
    "generated_image_1.generation_model=Nano Banana 2",❌
    "last_completed_step=12",❌
    "OUTPUT/SUCCESS"FAILED
  ],
  "forbidden": [
    "Playwright Sync API inside the asyncio loop",
    "FLOW_IMAGE_BACKEND_NOT_IMPLEMENTED",
    "OpenAI image generation",
    "ChatGPT browser image generation",
    "Locator.click: Timeout 120000ms exceeded",
    "prompt_box.click(timeout=self.action_timeout_ms)"
  ]
}
```

## STEP 1 - PATCH_12M1

```json
{
  "patch_id": "PATCH_12M1",
  "expected_match_count": 1,
  "actual_match_count": 1,
  "expected_replacement_count": 1,
  "actual_replacement_count": 1
}
```

## STEP 2 - PATCH_12M2

```json
{
  "patch_id": "PATCH_12M2",
  "expected_insert_anchor_count": 1,
  "actual_insert_anchor_count": 1,
  "expected_existing_helper_count": 0,
  "actual_existing_helper_count": 0
}
```

## STEP 3 - PATCH_12M3

```json
{
  "patch_id": "PATCH_12M3",
  "expected_method_count": 1,
  "actual_method_count": 1,
  "expected_replacement_count": 1,
  "actual_replacement_count": 1
}
```

## STEP 4 - PATCH_12M4

```json
{
  "patch_id": "PATCH_12M4",
  "expected_match_count": 1,
  "actual_match_count": 1,
  "expected_replacement_count": 1,
  "actual_replacement_count": 1
}
```

## STEP 5 - M-Validation 1

```text
PASS / no output
```

## STEP 7 — O-Validation 2: static marker check

```text
PATCH_12O_FLOW_CLIPBOARD_SETTINGS_STATIC_OK
```

## STEP 8 — O-Validation 3: method sanity

```text
PATCH_12O_FLOW_CLIPBOARD_SETTINGS_METHODS_OK
```

## STEP 0 - Cleanup before PATCH_12P

```text
COMPLETED
```

## STEP 1 - PATCH_12P1: add composer-scoped submit helper

```text
{'anchor': 1, 'existing_helper': 0, 'keyboard_only_marker': 1}
PATCH_12P1_DRY_RUN_PASS
```

## STEP 2 - PATCH_12P2: replace `_submit_flow_prompt(...)`

```text
{'method': 1, 'old_keyboard_marker': 1, 'old_control_enter_comment': 1, 'new_helper_call': 0}
PATCH_12P2_DRY_RUN_PASS
```

## STEP 2 - PATCH_12P2: replace `_submit_flow_prompt(...)`

```text
{'method': 1, 'old_keyboard_marker': 1, 'old_control_enter_comment': 1, 'new_helper_call': 0}
PATCH_12P2_DRY_RUN_PASS
```

## STEP 0 - Cleanup before PATCH_12P

```text
COMPLETED
```

## STEP 1 - PATCH_12P1: add composer-scoped submit helper

```text
{'anchor': 1, 'existing_helper': 0, 'keyboard_only_marker': 1}
PATCH_12P1_DRY_RUN_PASS
```

## STEP 6 - M-Validation 2

```text
PATCH_12M_FLOW_GALLERY_ATTACH_SUBMIT_STATIC_OK
```

## STEP 7 - M-Validation 3

```text
PATCH_12M_FLOW_GALLERY_ATTACH_SUBMIT_METHODS_OK
```

## Resume STEP 7 after PATCH_12M

Status: FAILED_BLOCKED

Blocking rule:
- NEXT STEP BLOCKED
- No future-step edits/proceeding

Failure:
- `FLOW_IMAGE_GENERATION_TIMEOUT`
- {"error_code": "FLOW_REFERENCE_NOT_ATTACHED_TO_COMPOSER", "field": "flow_reference_composer", "expected": "uploaded gallery image selected and attached into prompt composer", "actual": "{\"operation\": \"flow_reference_gallery_attach_failed\", \"source_image_count\": 2, \"selected_gallery_asset_count\": 0, \"clicked_attach_control\": true, \"before_composer_reference_count\": 0, \"after_composer_reference_count\": 0, \"summary\": {\"url\": \"https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28\", \"visible_media_count\": 57, \"composer_reference_count\": 0, \"surface_summary\": {\"url\": \"https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28\", \"textarea_count\": 1, \"textbox_count\": 1, \"contenteditable_count\": 1, \"input_text_count\": 2, \"visible_button_texts\": [\"arrow_back\\nGo Back\", \"more_vert\\nMore options\", \"search\\nSearch\", \"filter_list\\nSort & Filter\", \"add\\nAdd Media\", \"help\\nProduct Help\", \"settings_2\\nView Settings\", \"more_vert\\nMore\", \"PRO\", \"dashboard\\nAll Media\", \"image\\nView images\", \"videocam\\nView videos\", \"accessibility_new\\nCharacters\", \"movie\\nView scenes\", \"drive_folder_upload\\nView uploaded media\", \"apps_spark_2\\nTools\", \"delete\\nView Trash\", \"left_panel_close\\nCollapse\"]}}}", "file": "D:\\PROJECTS\\GITHUB\\az4mary\\Deterministic-Amazon-Automation-codex_branch\\workflow_orchestrator.py", "line": 2065, "snippet": "fail(", "trace_id": "fe78c8d6703134fe6184bd624f9936e8"}

## Expected checks

```json
{
  "expected": [
    "resume starts at step 12",✅
    "Image generation adapter handoff started",✅
    "Flow adapter reused shared browser session",✅ opened in new Tab
    "Flow page ready",✅
    "Flow reference images uploaded",✅uploaded to image gallery
    "Flow reference images attached to composer",❌attached button clicked, image gallery opened but image not selected or attached to composer.
    "Flow model selected",❌
    "Flow prompt box filled",❌prompt available in composer
    "Flow image prompt submitted",❌
    "Flow generated image captured",❌
    "output/generated_images/image_12.png exists",❌
    "generated_image_1.generation_backend=flow_browser",❌
    "generated_image_1.generation_model=Nano Banana 2",❌
    "last_completed_step=12",❌
    "OUTPUT/SUCCESS"FAILED
  ],
  "forbidden": [
    "Playwright Sync API inside the asyncio loop",
    "FLOW_IMAGE_BACKEND_NOT_IMPLEMENTED",
    "OpenAI image generation",
    "ChatGPT browser image generation",
    "Locator.click: Timeout 120000ms exceeded",
    "prompt_box.click(timeout=self.action_timeout_ms)"
  ]
}
```

## STEP 1 - PATCH_12N1

```json
{
  "patch_id": "PATCH_12N1",
  "expected_insert_anchor_count": 1,
  "actual_insert_anchor_count": 1,
  "expected_existing_helper_count": 0,
  "actual_existing_helper_count": 0
}
```

## STEP 2 - PATCH_12N2

```json
{
  "patch_id": "PATCH_12N2",
  "expected_method_count": 1,
  "actual_method_count": 1,
  "expected_replacement_count": 1,
  "actual_replacement_count": 1
}
```

## STEP 3 - PATCH_12N3

```json
{
  "patch_id": "PATCH_12N3",
  "expected_method_count": 1,
  "actual_method_count": 1,
  "expected_replacement_count": 1,
  "actual_replacement_count": 1
}
```

## STEP 4 - N-Validation 1

```text
PASS / no output
```

## STEP 5 - N-Validation 2

```text
PATCH_12N_FLOW_GALLERY_SELECTION_STATIC_OK
```

## STEP 6 - N-Validation 3

```text
PATCH_12N_FLOW_GALLERY_SELECTION_METHODS_OK
```

## STEP 0 — Cleanup before PATCH_12O

```text
COMPLETED
```

## STEP 1 — PATCH_12O1: add subprocess import + clipboard timing env vars

```text
{'import_os': 1, 'import_subprocess_existing': 0, 'flow_reference_attach_strict': 1, 'flow_clipboard_wait_existing': 0}
PATCH_12O1_DRY_RUN_PASS
```

## STEP 2 — PATCH_12O2: add Flow settings + clipboard helper methods

```text
{'anchor': 1, 'existing_clipboard_helper': 0, 'existing_settings_helper': 0, 'existing_paste_helper': 0}
PATCH_12O2_DRY_RUN_PASS
```

## STEP 3 — PATCH_12O3: replace `_attach_reference_images(...)`

```text
{'method': 1, 'old_upload_marker': 2, 'old_finalize_call': 1}
PATCH_12O3_DRY_RUN_PASS
```

## STEP 4 — PATCH_12O4: replace `_submit_flow_prompt(...)`

```text
{'method': 1, 'old_generate_click': 1, 'old_model_selection_started': 2}
PATCH_12O4_DRY_RUN_PASS
```

## STEP 5 — PATCH_12O5: replace Flow `execute_image(...)` ordering

```text
{'old_execute_sequence_count': 1, 'configure_existing': 0}
PATCH_12O5_DRY_RUN_PASS
```

## STEP 6 — O-Validation 1: compile

```text
PASS / no output
```

## STEP 7 — O-Validation 2: static marker check

```text
PATCH_12O_FLOW_CLIPBOARD_SETTINGS_STATIC_OK
```

## STEP 8 — O-Validation 3: method sanity

```text
PATCH_12O_FLOW_CLIPBOARD_SETTINGS_METHODS_OK
```

## STEP 0 - Cleanup before PATCH_12P

```text
COMPLETED
```

## STEP 1 - PATCH_12P1: add composer-scoped submit helper

```text
{'anchor': 1, 'existing_helper': 0, 'keyboard_only_marker': 1}
PATCH_12P1_DRY_RUN_PASS
```

## STEP 2 - PATCH_12P2: replace `_submit_flow_prompt(...)`

```text
{'method': 1, 'old_keyboard_marker': 1, 'old_control_enter_comment': 1, 'new_helper_call': 0}
PATCH_12P2_DRY_RUN_PASS
```

## STEP 3 - PATCH_12P3: disable download-click capture path

```text
{'download_selectors': 1, 'expect_download': 1, 'captured_download_marker': 1, 'capture_method': 1}
PATCH_12P3_DRY_RUN_PASS
```

## STEP 4 - P-Validation 1: compile

```text
PASS / no output
```

## STEP 5 - P-Validation 2: static marker check

```text
PATCH_12P_SUBMIT_CAPTURE_STATIC_OK
```

## STEP 6 - P-Validation 3: method sanity

```text
PATCH_12P_SUBMIT_CAPTURE_METHODS_OK
```

## STEP 0 - Cleanup before PATCH_12Q

```text
COMPLETED
```

## STEP 1 - PATCH_12Q1: add submit-safe composer finder + user INFO trace

```text
{'click_helper_anchor': 1, 'existing_user_info': 0, 'existing_submit_finder': 0}
PATCH_12Q1_DRY_RUN_PASS
```

## STEP 2 - PATCH_12Q2: replace submit click helper

```text
{'old_signature': 1, 'old_rect_fail': 1, 'old_coord_fallback': 1, 'new_signature': 0}
PATCH_12Q2_DRY_RUN_PASS
```

## STEP 3 - PATCH_12Q3: replace submit method to avoid prompt-surface activation

```text
{'method': 1, 'old_find_call': 4, 'old_helper_call': 1, 'new_safe_find_call': 1, 'new_helper_call': 0}
PATCH_12Q3_DRY_RUN_PASS
```

## STEP 4 - Q-Validation 1: compile

```text
PASS / no output
```

## STEP 5 - Q-Validation 2: static marker check

```text
PATCH_12Q_SUBMIT_NO_ACTIVATION_STATIC_OK
```

## STEP 6 - Q-Validation 3: method sanity

```text
PATCH_12Q_SUBMIT_NO_ACTIVATION_METHODS_OK
```

# PATCH_12R — enforce pasted-reference readiness before submit + recover from Flow page closure during capture

## STEP 0 - Cleanup before PATCH_12R

```text
COMPLETED
```

## STEP 1 - PATCH_12R1: add strict reference upload-ready wait

```text
{'paste_method': 1, 'reference_count_method': 1, 'existing_wait_helper': 0}
PATCH_12R1_DRY_RUN_PASS
```

## STEP 2 - PATCH_12R2: call upload-ready wait before submit

```text
{'final_settle_log': 1, 'ready_call': 0}
PATCH_12R2_DRY_RUN_PASS
```

## STEP 3 - PATCH_12R3: make Flow capture tolerate closed/replaced page

```text
{'capture_method': 1, 'raw_wait': 12, 'existing_safe_wait': 0}
PATCH_12R3_DRY_RUN_PASS
```

## STEP 4 - PATCH_12R4: add capture INFO at start and scan loop

```text
{'capture_method': 1, 'capture_info_existing': 0}
PATCH_12R4_DRY_RUN_PASS
```

## STEP 5 - R-Validation 1: compile

```text
PASS / no output
```

## STEP 6 - R-Validation 2: static marker check

```text
PATCH_12R_UPLOAD_READY_CAPTURE_RESILIENCE_STATIC_OK
```

## STEP 7 - R-Validation 3: method sanity

```text
PATCH_12R_UPLOAD_READY_CAPTURE_RESILIENCE_METHODS_OK
```

## STEP 1 - Inspect the actual attached image/chip element

``json
{   "url": "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28",   "selected": {     "depth": 0,     "tag": "IMG",     "attrs": {       "src": "/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3",       "alt": "A piece of media generated or uploaded by you, that is present in your collection.",       "class": "sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb",       "crossorigin": "anonymous",       "style": "opacity: 1;"     },     "text": "",     "rect": {       "x": 269,       "y": 748,       "width": 50,       "height": 50,       "visible": true,       "inViewport": true     },     "outerHTML": "<img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\">"   },   "ancestors": [     {       "depth": 0,       "tag": "IMG",       "attrs": {         "src": "/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3",         "alt": "A piece of media generated or uploaded by you, that is present in your collection.",         "class": "sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb",         "crossorigin": "anonymous",         "style": "opacity: 1;"       },       "text": "",       "rect": {         "x": 269,         "y": 748,         "width": 50,         "height": 50,         "visible": true,         "inViewport": true       },       "outerHTML": "<img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\">"     },     {       "depth": 1,       "tag": "DIV",       "attrs": {         "class": "sc-272106cb-1 dziwlH"       },       "text": "",       "rect": {         "x": 269,         "y": 748,         "width": 50,         "height": 50,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div>"     },     {       "depth": 2,       "tag": "BUTTON",       "attrs": {         "class": "sc-272106cb-0 iPeszA",         "data-card-open": "false",         "data-state": "closed"       },       "text": "cancel",       "rect": {         "x": 269,         "y": 748,         "width": 50,         "height": 50,         "visible": true,         "inViewport": true       },       "outerHTML": "<button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button>"     },     {       "depth": 3,       "tag": "DIV",       "attrs": {         "class": "sc-784d6f75-1 cbvblO"       },       "text": "cancel",       "rect": {         "x": 269,         "y": 748,         "width": 50,         "height": 50,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div>"     },     {       "depth": 4,       "tag": "DIV",       "attrs": {         "class": "sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg"       },       "text": "cancel",       "rect": {         "x": 269,         "y": 748,         "width": 50,         "height": 50,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div>"     },     {       "depth": 5,       "tag": "DIV",       "attrs": {         "class": "sc-273a6a40-0 hpgSgT"       },       "text": "cancel\ncancel",       "rect": {         "x": 261,         "y": 748,         "width": 582,         "height": 54,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gD"     },     {       "depth": 6,       "tag": "DIV",       "attrs": {         "class": "sc-439ac1d3-0 hMIBvb"       },       "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",       "rect": {         "x": 251,         "y": 736,         "width": 600,         "height": 152,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\">"     },     {       "depth": 7,       "tag": "DIV",       "attrs": {},       "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",       "rect": {         "x": 251,         "y": 736,         "width": 600,         "height": 152,         "visible": true,         "inViewport": true       },       "outerHTML": "<div><div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity:"     },     {       "depth": 8,       "tag": "DIV",       "attrs": {         "class": "sc-c9e4708a-0 kvaRPo"       },       "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",       "rect": {         "x": 251,         "y": 736,         "width": 600,         "height": 152,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-c9e4708a-0 kvaRPo\"><div><div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" cross"     },     {       "depth": 9,       "tag": "DIV",       "attrs": {         "class": "sc-53efa541-3 dJTbJz",         "style": "opacity: 1;"       },       "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",       "rect": {         "x": 0,         "y": 736,         "width": 1101,         "height": 152,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-53efa541-3 dJTbJz\" style=\"opacity: 1;\"><div class=\"sc-c9e4708a-0 kvaRPo\"><div><div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" c"     },     {       "depth": 10,       "tag": "DIV",       "attrs": {         "class": "sc-53efa541-1 bJLueu"       },       "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",       "rect": {         "x": 0,         "y": 736,         "width": 1101,         "height": 152,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-53efa541-1 bJLueu\"><div class=\"sc-53efa541-3 dJTbJz\" style=\"opacity: 1;\"><div class=\"sc-c9e4708a-0 kvaRPo\"><div><div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that"     },     {       "depth": 11,       "tag": "DIV",       "attrs": {         "class": "sc-c7ee1759-1 jhwuTJ"       },       "text": "arrow_back\nGo Back\nmore_vert\nMore options\nsearch\nSearch\nfilter_list\nSort & Filter\nadd\nAdd Media\nhelp\nProduct Help\nsettings_2\nView Settings\nmore_vert\nMore\nPRO\ndashboard\nAll Media\nAll Media\nimage\nView images\nImages\nvideocam\nView videos\nVideos\naccessibility_new\nCharacters\nCharacters\nmovie\nView scenes\nS",       "rect": {         "x": 0,         "y": 0,         "width": 1101,         "height": 920,         "visible": true,         "inViewport": true       },       "outerHTML": "<div class=\"sc-c7ee1759-1 jhwuTJ\"><div class=\"sc-8e1ee57d-0 sc-64b9b34d-9 loqVPM jWvFmt\"></div><div id=\"flow-desktop-header\" class=\"sc-64b9b34d-0 kZKCjW\" style=\"transform: translateY(0px);\"><div class=\"sc-64b9b34d-2 bCpdRw\"><nav class=\"sc-2eac5247-0 niIkg sc-64b9b34d-7 iIEIHk\"><div class=\"sc-2eac5247-1 eGKJom\" style=\"pointer-events: auto; opacity: 1; width: auto;\"><button class=\"sc-e8425ea6-0 hOBPaw sc-d3791a4f-0 sc-d3791a4f-4 sc-2eac5247-2 ewGlDn famhRe jUJxHE\"><i class=\"sc-a39c2a59-0 ZeJCP google-symbols sc-e8425ea6-1 jZhFNn\" font-size=\"1.5rem\" color=\"currentColor\">arrow_back</i><span style=\"position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;\">Go Back</span></button><div class=\"sc-e98e0e95-0 cynypI sc-2eac5247-3 bqmeht\"><input type=\"text\" size=\"8\" aria-label=\"Editable text\" class=\"sc-e98e0e95-2 dwTWkV\" value=\"PRODUCTS\"></div><button class=\"sc-e8425ea6-0 hOBPaw sc-d3791a4f-0 sc-d3791a4f-4 sc-26aa1721-3 ewGlDn famhRe dUDRen\" color=\"currentColor\" type=\"button\" id=\"radix-:r3:\" aria-haspopup=\"menu\" aria-expanded=\"false\" data-state=\"closed\"><i class=\"sc-a39c2a"     }   ] }
``

## STEP 1 - Inspect the actual attached image/chip element

```json
{
  "url": "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28",
  "selected": {
    "depth": 0,
    "tag": "IMG",
    "attrs": {
      "src": "/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3",
      "alt": "A piece of media generated or uploaded by you, that is present in your collection.",
      "class": "sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb",
      "crossorigin": "anonymous",
      "style": "opacity: 1;"
    },
    "text": "",
    "rect": {
      "x": 269,
      "y": 748,
      "width": 50,
      "height": 50,
      "visible": true,
      "inViewport": true
    },
    "outerHTML": "<img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\">"
  },
  "ancestors": [
    {
      "depth": 0,
      "tag": "IMG",
      "attrs": {
        "src": "/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3",
        "alt": "A piece of media generated or uploaded by you, that is present in your collection.",
        "class": "sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb",
        "crossorigin": "anonymous",
        "style": "opacity: 1;"
      },
      "text": "",
      "rect": {
        "x": 269,
        "y": 748,
        "width": 50,
        "height": 50,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\">"
    },
    {
      "depth": 1,
      "tag": "DIV",
      "attrs": {
        "class": "sc-272106cb-1 dziwlH"
      },
      "text": "",
      "rect": {
        "x": 269,
        "y": 748,
        "width": 50,
        "height": 50,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div>"
    },
    {
      "depth": 2,
      "tag": "BUTTON",
      "attrs": {
        "class": "sc-272106cb-0 iPeszA",
        "data-card-open": "false",
        "data-state": "closed"
      },
      "text": "cancel",
      "rect": {
        "x": 269,
        "y": 748,
        "width": 50,
        "height": 50,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button>"
    },
    {
      "depth": 3,
      "tag": "DIV",
      "attrs": {
        "class": "sc-784d6f75-1 cbvblO"
      },
      "text": "cancel",
      "rect": {
        "x": 269,
        "y": 748,
        "width": 50,
        "height": 50,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div>"
    },
    {
      "depth": 4,
      "tag": "DIV",
      "attrs": {
        "class": "sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg"
      },
      "text": "cancel",
      "rect": {
        "x": 269,
        "y": 748,
        "width": 50,
        "height": 50,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div>"
    },
    {
      "depth": 5,
      "tag": "DIV",
      "attrs": {
        "class": "sc-273a6a40-0 hpgSgT"
      },
      "text": "cancel\ncancel",
      "rect": {
        "x": 261,
        "y": 748,
        "width": 582,
        "height": 54,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gD"
    },
    {
      "depth": 6,
      "tag": "DIV",
      "attrs": {
        "class": "sc-439ac1d3-0 hMIBvb"
      },
      "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",
      "rect": {
        "x": 251,
        "y": 736,
        "width": 600,
        "height": 152,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\">"
    },
    {
      "depth": 7,
      "tag": "DIV",
      "attrs": {},
      "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",
      "rect": {
        "x": 251,
        "y": 736,
        "width": 600,
        "height": 152,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div><div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity:"
    },
    {
      "depth": 8,
      "tag": "DIV",
      "attrs": {
        "class": "sc-c9e4708a-0 kvaRPo"
      },
      "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",
      "rect": {
        "x": 251,
        "y": 736,
        "width": 600,
        "height": 152,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-c9e4708a-0 kvaRPo\"><div><div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" cross"
    },
    {
      "depth": 9,
      "tag": "DIV",
      "attrs": {
        "class": "sc-53efa541-3 dJTbJz",
        "style": "opacity: 1;"
      },
      "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",
      "rect": {
        "x": 0,
        "y": 736,
        "width": 1101,
        "height": 152,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-53efa541-3 dJTbJz\" style=\"opacity: 1;\"><div class=\"sc-c9e4708a-0 kvaRPo\"><div><div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" c"
    },
    {
      "depth": 10,
      "tag": "DIV",
      "attrs": {
        "class": "sc-53efa541-1 bJLueu"
      },
      "text": "cancel\ncancel\n\nWhat do you want to create?\n?\n\n\nadd_2\nCreate\nAgent\n?? Nano Banana 2\ncrop_9_16\n1x\narrow_forward\nCreate\nclose\nClear prompt",
      "rect": {
        "x": 0,
        "y": 736,
        "width": 1101,
        "height": 152,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-53efa541-1 bJLueu\"><div class=\"sc-53efa541-3 dJTbJz\" style=\"opacity: 1;\"><div class=\"sc-c9e4708a-0 kvaRPo\"><div><div class=\"sc-439ac1d3-0 hMIBvb\"><div class=\"sc-273a6a40-0 hpgSgT\"><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=1833e051-0ae1-4b55-a6c2-ac1798c662c3\" alt=\"A piece of media generated or uploaded by you, that is present in your collection.\" class=\"sc-f803b119-0 bhyZfD sc-621e6fb9-1 hZlsYb\" crossorigin=\"anonymous\" style=\"opacity: 1;\"></div><div class=\"sc-272106cb-2 gDtvdv\"><i class=\"sc-a39c2a59-0 lkKicR google-symbols sc-272106cb-3 husQRa\" font-size=\"1rem\" color=\"white\">cancel</i></div></button></div></div><div class=\"sc-784d6f75-0 bEnOCH sc-621e6fb9-0 buIBIg\"><div class=\"sc-784d6f75-1 cbvblO\"><button class=\"sc-272106cb-0 iPeszA\" data-card-open=\"false\" data-state=\"closed\"><div class=\"sc-272106cb-1 dziwlH\"><img src=\"/fx/api/trpc/media.getMediaUrlRedirect?name=eff0732a-4325-476d-b016-8ad41187376e\" alt=\"A piece of media generated or uploaded by you, that"
    },
    {
      "depth": 11,
      "tag": "DIV",
      "attrs": {
        "class": "sc-c7ee1759-1 jhwuTJ"
      },
      "text": "arrow_back\nGo Back\nmore_vert\nMore options\nsearch\nSearch\nfilter_list\nSort & Filter\nadd\nAdd Media\nhelp\nProduct Help\nsettings_2\nView Settings\nmore_vert\nMore\nPRO\ndashboard\nAll Media\nAll Media\nimage\nView images\nImages\nvideocam\nView videos\nVideos\naccessibility_new\nCharacters\nCharacters\nmovie\nView scenes\nS",
      "rect": {
        "x": 0,
        "y": 0,
        "width": 1101,
        "height": 920,
        "visible": true,
        "inViewport": true
      },
      "outerHTML": "<div class=\"sc-c7ee1759-1 jhwuTJ\"><div class=\"sc-8e1ee57d-0 sc-64b9b34d-9 loqVPM jWvFmt\"></div><div id=\"flow-desktop-header\" class=\"sc-64b9b34d-0 kZKCjW\" style=\"transform: translateY(0px);\"><div class=\"sc-64b9b34d-2 bCpdRw\"><nav class=\"sc-2eac5247-0 niIkg sc-64b9b34d-7 iIEIHk\"><div class=\"sc-2eac5247-1 eGKJom\" style=\"pointer-events: auto; opacity: 1; width: auto;\"><button class=\"sc-e8425ea6-0 hOBPaw sc-d3791a4f-0 sc-d3791a4f-4 sc-2eac5247-2 ewGlDn famhRe jUJxHE\"><i class=\"sc-a39c2a59-0 ZeJCP google-symbols sc-e8425ea6-1 jZhFNn\" font-size=\"1.5rem\" color=\"currentColor\">arrow_back</i><span style=\"position: absolute; border: 0px; width: 1px; height: 1px; padding: 0px; margin: -1px; overflow: hidden; clip: rect(0px, 0px, 0px, 0px); white-space: nowrap; overflow-wrap: normal;\">Go Back</span></button><div class=\"sc-e98e0e95-0 cynypI sc-2eac5247-3 bqmeht\"><input type=\"text\" size=\"8\" aria-label=\"Editable text\" class=\"sc-e98e0e95-2 dwTWkV\" value=\"PRODUCTS\"></div><button class=\"sc-e8425ea6-0 hOBPaw sc-d3791a4f-0 sc-d3791a4f-4 sc-26aa1721-3 ewGlDn famhRe dUDRen\" color=\"currentColor\" type=\"button\" id=\"radix-:r3:\" aria-haspopup=\"menu\" aria-expanded=\"false\" data-state=\"closed\"><i class=\"sc-a39c2a"
    }
  ]
}
```
