# INSTRUCTIONS_3

- Confirmed `PATCH_05D` halted only because the exact dry-run `FIND` block did not match due to escaping/string representation mismatch, not because the target function is absent.

## Decision

Do **not** skip `PATCH_05D` yet.

Apply `PATCH_05D` using the located `repair_common_json_glitches(...)` function as the target. The function is present and still only performs the existing inch-mark comma repair before returning `json_text`.

This is the correct next step because the real runtime failure already exposed malformed JSON around:

```json
"sensor_size":"1/2.9""
```

So the patch set should include the explicit repair before we run the final `PATCH_SET_05` validation.

---

# Revised PATCH_05D — Repair doubled terminal quote in JSON strings

## DRY-RUN EXPECTATION

```json
{
  "patch_id": "PATCH_05D_REVISED",
  "expected_match_count": 1,
  "expected_replacement_count": 1,
  "halt_if_match_count_is_not": 1
}
```

## FIND

Use this exact located function block:

```python
def repair_common_json_glitches(json_text: str) -> str:
    # Fix the common inch-mark issue that breaks JSON strings, e.g.:
    # "sensor": "SONY Exmor IMX323 (1/2.9", 2.8µ pixel)"
    # becomes:
    # "sensor": "SONY Exmor IMX323 (1/2.9 inches, 2.8µ pixel)"
    json_text = re.sub(r'(\d)"\s*,\s*(\d)', r"\1 inches, \2", json_text)
    return json_text
```

## REPLACE WITH

```python
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
```

---

# Validation after revised PATCH_05D

## 1. Compile

```powershell
D:\TOOLS\Python314\python.exe -m py_compile workflow_orchestrator.py
```

## 2. Focused JSON repair test

```powershell
D:\TOOLS\Python314\python.exe - <<'PY'
import workflow_orchestrator as w

bad = '{"sensor_size":"1/2.9"","pixel_size":"2.8µ"}'
parsed, err, excerpt = w.try_parse_response_json(bad)

assert parsed is not None, err
assert parsed["sensor_size"] == '1/2.9"'
assert parsed["pixel_size"] == "2.8µ"

print("PATCH_05D_JSON_REPAIR_OK")
print(parsed)
PY
```

## 3. Then run the focused 01A runtime test

```powershell
$env:BROWSER_JSON_RETRIES="0"
$env:BROWSER_RESPONSE_STABILIZE_SECONDS="20"
$env:BROWSER_RESPONSE_STABLE_REQUIRED="2"
D:\TOOLS\Python314\python.exe workflow_orchestrator.py --stop-after 01A
```

Expected outcome:

```json
{
  "expected": [
    "Browser assistant response detected",
    "Browser assistant response stabilized OR stabilization deadline reached",
    "Browser response received",
    "Then either JSON parse succeeds or MODEL_OUTPUT_NOT_JSON fails fast",
    "No hang after assistant response detection"
  ]
}
```

---

## Current PATCH_SET_05 status

```json
{
  "PATCH_05A": "PASS",
  "PATCH_05B": "PASS",
  "PATCH_05C": "PASS",
  "PATCH_05D": "REQUIRES_REVISED_APPLY",
  "PATCH_SET_05": "NOT_YET_COMPLETE"
}
```

Proceed with revised `PATCH_05D`; then send the compile, JSON repair test, and `--stop-after 01A` result.