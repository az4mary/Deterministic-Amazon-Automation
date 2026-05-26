# CODE_MANAGE Instructions

# **file ownership / exact line-number test**.

## Important constraints

* Do not edit `workflow_orchestrator.py`.
* Do not summarize from memory.
* Do not rely on indexed search, semantic retrieval, or chat-provided snippets.
* Use direct filesystem reads only.
* Use exact file paths and line numbers.
* If any output is too long, write the full output to a local report file and show the report file path.

## STEP 1 - Verify Raw File Ownership
````md
# Codex Task Brief: Verify Raw File Ownership for `workflow_orchestrator.py`

## Objective

Determine whether Codex Desktop can access `workflow_orchestrator.py` as a raw local file from byte 1 to EOF, rather than only through indexed/chunked retrieval. Confirm this by producing deterministic file metadata, exact line counts, exact line-numbered excerpts, and a reproducible structural map.

## Target file

- `workflow_orchestrator.py`

## Primary question

Can Codex open and inspect the entire file directly as a local filesystem object?

A successful result means Codex can:

1. Read the file from beginning to end.
2. Count exact bytes, characters, and lines.
3. Produce exact line-numbered excerpts.
4. Generate a symbol/function/class map with exact line ranges.
5. Search the file deterministically with tools like `rg`, `grep`, PowerShell, or Python.
6. Report whether the file was read from the local filesystem or only via retrieval/indexed context.

---

## Required commands to run

Run these from the project root.

### 1. Confirm file exists and basic metadata

#### PowerShell

```powershell
Get-Item .\workflow_orchestrator.py | Format-List FullName,Length,LastWriteTime
````

#### Python fallback

```bash
python - <<'PY'
from pathlib import Path

path = Path("workflow_orchestrator.py")
print("exists:", path.exists())
print("absolute_path:", path.resolve())
print("bytes:", path.stat().st_size if path.exists() else None)
print("modified:", path.stat().st_mtime if path.exists() else None)
PY
```

---

## STEP 2 - Read the file from byte 1 to EOF

```bash
python - <<'PY'
from pathlib import Path
import hashlib

path = Path("workflow_orchestrator.py")
data = path.read_bytes()

print("file:", path.resolve())
print("byte_count:", len(data))
print("sha256:", hashlib.sha256(data).hexdigest())
print("first_100_bytes:", repr(data[:100]))
print("last_100_bytes:", repr(data[-100:]))
PY
```

Success criterion: Codex reports actual byte count, SHA-256 hash, first 100 bytes, and last 100 bytes.

---

## STEP 3 - Count exact lines and characters

```bash
python - <<'PY'
from pathlib import Path

path = Path("workflow_orchestrator.py")
text = path.read_text(encoding="utf-8")
lines = text.splitlines()

print("character_count:", len(text))
print("line_count:", len(lines))
print("first_line:", repr(lines[0] if lines else ""))
print("last_line:", repr(lines[-1] if lines else ""))
PY
```

Success criterion: Codex reports exact line count and verifies both first and last line.

---

## STEP 4 - Produce line-numbered excerpts

```bash
python - <<'PY'
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
PY
```

Success criterion: Codex returns beginning, middle, and end excerpts with exact line numbers.

---

## STEP 5 - Generate Python AST symbol map

```bash
python - <<'PY'
from pathlib import Path
import ast

path = Path("workflow_orchestrator.py")
text = path.read_text(encoding="utf-8")
tree = ast.parse(text)

symbols = []

for node in ast.walk(tree):
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        symbols.append(
            (
                node.lineno,
                getattr(node, "end_lineno", node.lineno),
                type(node).__name__,
                node.name,
            )
        )

symbols.sort()

print(f"symbol_count: {len(symbols)}")
print("\n--- symbols ---")
for start, end, kind, name in symbols:
    print(f"{path}:{start}-{end} {kind} {name}")
PY
```

Success criterion: Codex returns a complete symbol map with line ranges.

---

## STEP 6 - Search for likely validation/prompt/schema terms

```bash
python - <<'PY'
from pathlib import Path
import re

path = Path("workflow_orchestrator.py")
lines = path.read_text(encoding="utf-8").splitlines()

terms = [
    "schema",
    "validate",
    "validation",
    "prompt",
    "citation",
    "line",
    "file",
    "chunk",
    "orchestrator",
]

for term in terms:
    print(f"\n--- matches for {term!r} ---")
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    count = 0
    for i, line in enumerate(lines, start=1):
        if pattern.search(line):
            print(f"{path}:{i}: {line[:240]}")
            count += 1
    print(f"total_matches: {count}")
PY
```

Success criterion: Codex produces deterministic search results with exact line numbers.

---

## STEP 7 - Required report back

Return a report in this exact structure:

```md
# Codex File Ownership Report

## Verdict

Choose one:

- PASS: Codex accessed `workflow_orchestrator.py` as a raw local file from byte 1 to EOF.
- PARTIAL: Codex accessed some local file content but could not complete one or more required checks.
- FAIL: Codex could not access the raw local file.

## Evidence

### File metadata

- Absolute path:
- Byte count:
- Character count:
- Line count:
- SHA-256:
- Last modified:

### EOF verification

- First 100 bytes:
- Last 100 bytes:
- First line:
- Last line:

### Line-numbered excerpts produced

- Beginning excerpt: yes/no
- Middle excerpt: yes/no
- End excerpt: yes/no

### Symbol map

- AST parse succeeded: yes/no
- Symbol count:
- First 10 symbols:
- Last 10 symbols:

### Search verification

Report total matches for:

- schema:
- validate:
- validation:
- prompt:
- citation:
- line:
- file:
- chunk:
- orchestrator:

## Commands run

Paste the exact commands run.

## Errors or limitations

List any errors, missing dependencies, encoding issues, path issues, permission issues, or truncation.

## Conclusion

State whether this proves Codex has raw local-file access rather than chunked/indexed retrieval access.
```

The raw-file ownership test is complete. Codex proved it can read `workflow_orchestrator.py` directly from the local filesystem, including byte-level EOF access, exact line count, line-numbered excerpts, AST symbols, and deterministic search. 

What remains is everything **after single-file ownership**.

## Status by task

| Codex Desktop task                           |       Status | What still needs testing                                                                                                      |
| -------------------------------------------- | -----------: | ----------------------------------------------------------------------------------------------------------------------------- |
| **Inspect this repo**                        |  **Partial** | Codex inspected one target file, not the whole repo. Need repo inventory, key file map, dependency/config/test discovery.     |
| **Find every caller of this function**       | **Untested** | Need to pick a function and verify Codex can find all direct callers using `rg`, AST, and possibly import/reference analysis. |
| **Validate the schema against `prompts.md`** | **Untested** | Need Codex to compare `workflow_orchestrator.py` schema builders against prompt files and report mismatches.                  |
| **Write tests**                              | **Untested** | Need Codex to add focused tests for one behavior without broad refactoring.                                                   |
| **Patch the parser**                         | **Untested** | Need an actual parser defect or improvement target.                                                                           |
| **Run `pytest` / `ruff` / `mypy`**           | **Untested** | Need Codex to run the repo’s existing validation stack and report results.                                                    |
| **Produce a diff**                           | **Untested** | Requires a controlled edit, then `git diff` / reviewable patch output.                                                        |

## Recommended remaining test order

### STEP 8 — Repo inspection test

Purpose: prove Codex can inspect the **whole project**, not just one file.

Expected output:

```text
repo root
git branch/status
top-level files/folders
Python files
prompt files
test files
config files
dependency files
entrypoints
likely generated/output folders
```

No edits.

---

### STEP 9 — Caller-discovery test

Purpose: prove Codex can trace references precisely.

Use one known function from the AST map, for example:

```text
validate_initial_inputs
build_schema
run_step
write_image_prompts
```

Expected output:

```text
target function definition line
all direct callers
all indirect relevant references
search commands used
AST/reference method used
confidence level
```

No edits.

---

### STEP 10 — Schema-vs-prompts validation test

Purpose: test the actual workflow concern.

Codex should inspect:

```text
workflow_orchestrator.py
docs/prompts.md
docs/prompts/
```

Expected output:

```text
schema builders found
prompt files found
fields expected by schemas
fields requested by prompts
mismatches
missing fields
unused fields
recommended patch, but no edit yet
```

No edits unless you approve.

---

### STEP 11 — Test-writing test

Purpose: verify Codex can add a narrow regression test.

Expected output:

```text
test file created or updated
test target
commands run
pass/fail result
git diff
```

This is the first step that should allow edits.

---

### STEP 12 — Parser patch test

Purpose: verify Codex can make a minimal code change.

Expected output:

```text
bug/defect identified
minimal patch applied
tests added or updated
pytest/ruff/mypy results
git diff
```

---

### STEP 13 — Full validation test

Purpose: verify Codex can run the project’s validation stack.

Expected output:

```text
pytest result
ruff result
mypy result
any skipped tools
failures with exact files/lines
```

---

### STEP 14 — Diff production test

Purpose: verify Codex can package the work for review.

Expected output:

```text
git status
git diff --stat
git diff
files changed
risk summary
rollback notes
```

## Immediate next test

The next logical test is:

> **STEP 8 — Inspect this repo**

That tests the broader capability you need before caller tracing, schema validation, tests, or patches.
