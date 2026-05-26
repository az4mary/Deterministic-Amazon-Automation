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
Use this as the Codex handoff packet for **STEP 8 through STEP 14**.

````md
# Codex Task Brief: STEP 8 - STEP 14 Capability Validation

## Objective

Continue the Codex Desktop validation workflow after the successful raw-file ownership test.

The goal is to prove Codex can operate as the local repo specialist for:

- repo inspection
- caller tracing
- schema validation against prompts
- test creation
- parser patching
- local validation commands
- diff production

## Operating rules

- Work from the project root.
- Prefer direct filesystem reads, `rg`, AST parsing, Git commands, and local test tools.
- Do not use indexed/semantic retrieval when local files are available.
- Do not use the internet.
- Do not install dependencies unless explicitly approved.
- Do not edit files during STEP 8, STEP 9, or STEP 10.
- Stop after each step and wait for user confirmation before proceeding.
- Report exact file paths and line numbers wherever applicable.
- If a command fails, report the exact command, exit code, and error output.
- If output is too long for chat, write the full output to a local markdown report file and summarize the result.

---

# STEP 8 - Inspect this repo

## Objective

Inspect the full repository structure and identify the files relevant to workflow orchestration, prompts, schema validation, tests, configs, and execution.

## Constraints

- Read-only.
- Do not modify files.
- Do not run tests yet.
- Do not infer missing files. Report only what exists.

## Required inspection

Run commands equivalent to:

```powershell
Get-Location
git status --short
git branch --show-current
Get-ChildItem -Force
````

Find and report:

* repo root
* current Git branch
* current Git status
* top-level folders/files
* Python files
* prompt files
* markdown instruction files
* test files
* config files
* dependency files
* generated/output folders
* likely entrypoints

Suggested commands:

```powershell
Get-ChildItem -Recurse -File -Include *.py | Select-Object FullName
Get-ChildItem -Recurse -File -Include *.md | Select-Object FullName
Get-ChildItem -Recurse -File -Include pyproject.toml,requirements.txt,setup.cfg,setup.py,pytest.ini,mypy.ini,ruff.toml,.ruff.toml | Select-Object FullName
Get-ChildItem -Recurse -Directory -Include tests,test,docs,prompts,output,generated | Select-Object FullName
```

Alternative with `rg`:

```bash
rg --files
rg --files | rg "(^|/)(tests?|docs|prompts|output|generated)/|\.py$|\.md$|pyproject\.toml|requirements\.txt|pytest\.ini|mypy\.ini|ruff\.toml|\.ruff\.toml"
```

## Required report

```md
# STEP 8 Repo Inspection Report

## Verdict

PASS / PARTIAL / FAIL

## Repo identity

- Root:
- Branch:
- Git status summary:

## Top-level inventory

List top-level files and folders.

## Relevant files discovered

### Python files

List relevant Python files.

### Prompt / markdown files

List relevant prompt and instruction files.

### Test files

List discovered test files.

### Config / dependency files

List discovered config and dependency files.

### Generated / output folders

List likely generated/output folders.

## Likely workflow entrypoints

List likely entrypoint files/functions/commands.

## Risks or gaps

List anything missing, ambiguous, or potentially generated.

## Commands run

Paste exact commands.

## Next recommended step

Proceed to STEP 9 after user confirmation.
```

Stop after STEP 8.

---

# STEP 9 - Find every caller of this function

## Objective

Prove Codex can perform precise caller/reference tracing across the local repo.

## Target function

Use this initial target unless the user overrides it:

```text
validate_initial_inputs
```

## Constraints

* Read-only.
* Do not edit files.
* Use direct filesystem inspection only.
* Do not rely on semantic search.

## Required method

Use at least two approaches:

1. Text search with exact line numbers.
2. AST-based or structural inspection where possible.

Suggested commands:

```bash
rg -n "validate_initial_inputs" .
rg -n "def validate_initial_inputs|validate_initial_inputs\(" .
```

Suggested Python AST script:

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

## Required report

```md
# STEP 9 Caller Discovery Report

## Verdict

PASS / PARTIAL / FAIL

## Target function

`validate_initial_inputs`

## Definition found

- File:
- Lines:

## Direct callers found

List every direct caller with file and line number.

## Other references

List non-call references, imports, string mentions, comments, or indirect references if any.

## Methods used

- Text search:
- AST inspection:
- Other:

## Confidence

High / Medium / Low

Explain why.

## Commands run

Paste exact commands/scripts.

## Errors or limitations

List any parsing errors, skipped files, dynamic call limitations, or generated files excluded.

## Next recommended step

Proceed to STEP 10 after user confirmation.
```

Stop after STEP 9.

---

# STEP 10 - Validate schema against `prompts.md`

## Objective

Compare schema expectations in `workflow_orchestrator.py` against prompt content in:

* `docs/prompts.md`
* `docs/prompts/`
* any other discovered prompt files from STEP 8

Identify mismatches before making any edits.

## Constraints

* Read-only.
* Do not edit files.
* Do not patch yet.
* Do not normalize away mismatches silently.
* Report exact file paths and line numbers.

## Required inspection

Inspect these known areas first:

* `workflow_orchestrator.py`
* `docs/prompts.md`
* `docs/prompts/`

Search for:

```text
build_schema
schema_builder
prompt_file
PROMPTS_MD_PATH
PROMPTS_DIR
expected
required
json
fields
```

Suggested commands:

```bash
rg -n "build_schema|schema_builder|prompt_file|PROMPTS_MD_PATH|PROMPTS_DIR|required|expected|json|fields" workflow_orchestrator.py docs
```

Use AST and direct reads to identify:

* schema builder functions
* fields required by schemas
* prompt files referenced by steps
* JSON structures requested by prompts
* fields written to or read from workflow state
* mismatches between prompt instructions and schema validation

## Required report

```md
# STEP 10 Schema-vs-Prompts Validation Report

## Verdict

PASS / PARTIAL / FAIL

## Files inspected

List exact files inspected.

## Schema sources found

List schema builder functions, dataclasses, constants, or validation functions with file/line ranges.

## Prompt sources found

List prompt markdown files and prompt sections with file/line ranges.

## Field comparison

| Field / concept | Schema expectation | Prompt expectation | Status | Evidence |
|---|---|---|---|---|

## Mismatches

List each mismatch with:

- field/concept
- schema location
- prompt location
- impact
- recommended fix

## Missing or ambiguous items

List any schema or prompt areas that could not be confidently mapped.

## Recommended patch plan

Propose a minimal patch plan, but do not edit files.

## Commands run

Paste exact commands/scripts.

## Next recommended step

Proceed to STEP 11 only after user approval of the patch/test target.
```

Stop after STEP 10.

---

# STEP 11 - Write tests

## Objective

Add focused tests for the highest-priority mismatch or behavior approved after STEP 10.

## Constraints

* Editing is allowed only for test files unless the user explicitly approves source changes.
* Prefer minimal tests.
* Do not refactor unrelated code.
* Do not change production code in this step unless unavoidable and explicitly approved.
* Preserve existing test style.

## Required pre-edit checks

```bash
git status --short
```

Inspect existing test structure first:

```bash
rg --files | rg "(^|/)tests?/|test_.*\.py$|.*_test\.py$"
```

If no test structure exists, propose a minimal test file path before creating it.

## Test target

Use the approved target from STEP 10.

If no target has been approved yet, stop and ask for user approval.

## Required validation

Run the narrowest relevant test command first.

Examples:

```bash
python -m pytest tests/test_workflow_orchestrator.py
python -m pytest
```

If pytest is unavailable, report that clearly and do not install packages without approval.

## Required report

````md
# STEP 11 Test-Writing Report

## Verdict

PASS / PARTIAL / FAIL

## Test target

Describe the behavior or mismatch being tested.

## Files changed

List files changed.

## Tests added

List test names and what each validates.

## Commands run

Paste exact commands.

## Results

- Narrow test result:
- Full test result if run:

## Git diff summary

Include:

```bash
git status --short
git diff --stat
````

## Full diff

Paste `git diff` or write it to a report file if too long.

## Errors or limitations

List any failures, missing dependencies, or skipped validation.

## Next recommended step

Proceed to STEP 12 after user confirmation.

````

Stop after STEP 11.

---

# STEP 12 - Patch the parser

## Objective

Apply the minimal production-code patch needed to satisfy the approved schema/prompt/parser issue.

## Constraints

- Do not perform broad refactors.
- Do not change unrelated behavior.
- Do not edit generated/output files.
- Keep the patch minimal and reviewable.
- Preserve public interfaces unless explicitly approved.
- Update tests only as needed.

## Required pre-edit checks

```bash
git status --short
````

If uncommitted changes exist from STEP 11, keep them and patch on top of them only if they are expected test changes.

## Patch target

Use the approved defect or mismatch from STEP 10 and the tests from STEP 11.

If there is no approved parser/source target, stop and ask for user approval.

## Required validation

Run:

```bash
python -m pytest
```

Then run narrower or broader commands depending on repo config.

## Required report

````md
# STEP 12 Parser Patch Report

## Verdict

PASS / PARTIAL / FAIL

## Defect patched

Describe the exact parser/schema/prompt issue addressed.

## Files changed

List source and test files changed.

## Functions changed

List exact functions/classes changed with file/line references.

## Patch summary

Explain the minimal change made.

## Commands run

Paste exact commands.

## Results

- Relevant tests:
- Full pytest:

## Git diff summary

Include:

```bash
git status --short
git diff --stat
````

## Full diff

Paste `git diff` or write it to a report file if too long.

## Risks

List any behavior changes or remaining edge cases.

## Next recommended step

Proceed to STEP 13 after user confirmation.

````

Stop after STEP 12.

---

# STEP 13 - Run pytest / ruff / mypy

## Objective

Run the repo’s local validation stack and report exact results.

## Constraints

- Do not edit files in this step unless the user explicitly approves a follow-up fix.
- Do not install missing tools without approval.
- Detect configuration before running tools.

## Required discovery

Look for:

```text
pyproject.toml
pytest.ini
setup.cfg
tox.ini
mypy.ini
ruff.toml
.ruff.toml
requirements.txt
````

Suggested commands:

```bash
rg --files | rg "pyproject\.toml|pytest\.ini|setup\.cfg|tox\.ini|mypy\.ini|ruff\.toml|\.ruff\.toml|requirements\.txt"
```

## Required validation commands

Run what is available.

Preferred:

```bash
python -m pytest
python -m ruff check .
python -m mypy .
```

If `ruff` or `mypy` is unavailable, try:

```bash
ruff check .
mypy .
```

If still unavailable, report as unavailable.

## Required report

````md
# STEP 13 Validation Stack Report

## Verdict

PASS / PARTIAL / FAIL

## Commands run

List every command.

## Results

| Tool | Command | Result | Notes |
|---|---|---|---|
| pytest |  | PASS/FAIL/SKIPPED |  |
| ruff |  | PASS/FAIL/SKIPPED |  |
| mypy |  | PASS/FAIL/SKIPPED |  |

## Failure details

For each failure, include:

- file
- line
- error code/message
- likely cause
- whether it appears related to current changes

## Missing tools

List unavailable tools and the exact error.

## Git status

Include:

```bash
git status --short
````

## Next recommended step

Proceed to STEP 14 after user confirmation.

````

Stop after STEP 13.

---

# STEP 14 - Produce a diff

## Objective

Produce a complete reviewable diff package for the user and ChatGPT manager review.

## Constraints

- Do not make additional edits.
- Do not stage or commit unless explicitly approved.
- Do not omit changed files.
- Include test/validation results from previous steps.

## Required commands

```bash
git status --short
git diff --stat
git diff
````

If diff is too long, write it to:

```text
CODEX_STEP_14_DIFF.patch
CODEX_STEP_14_DIFF_REPORT.md
```

Suggested commands:

```bash
git diff > CODEX_STEP_14_DIFF.patch
git diff --stat > CODEX_STEP_14_DIFF_STAT.txt
```

## Required report

```md
# STEP 14 Diff Package Report

## Verdict

PASS / PARTIAL / FAIL

## Changed files

List every changed file and whether it is:

- source
- test
- docs
- config
- generated/output

## Diff stat

Paste `git diff --stat`.

## Full diff

Paste full `git diff`, or provide the local path to the patch file if too long.

## Validation summary

Summarize STEP 13 results:

- pytest:
- ruff:
- mypy:

## Review notes

Explain:

- what changed
- why it changed
- how to review it
- rollback approach

## Commands run

Paste exact commands.

## Final recommendation

State whether the changes are ready for manager review, need another Codex fix pass, or should be reverted.
```

Stop after STEP 14.

---

# Final completion condition

This STEP 8 - STEP 14 sequence is complete only when Codex has produced:

1. Repo inspection report.
2. Caller discovery report.
3. Schema-vs-prompts validation report.
4. Test-writing report.
5. Parser patch report.
6. Validation stack report.
7. Diff package report.

Do not proceed from one step to the next without user confirmation.

```
```
