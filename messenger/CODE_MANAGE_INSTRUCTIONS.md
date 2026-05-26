# CODE_MANAGE Instructions

Source response file: `CODE_MANAGE_response.md`
Source checkpoint: `2026-05-26T11:21:32.4338044-05:00`

## Standalone Execution Context

This file is the complete executable instruction source for the CODE_MANAGE workflow. Do not rely on chat history for context.

Repository root:

```text
D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch
```

Active messenger files:

```text
D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_INSTRUCTIONS.md
D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_Progress.md
D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\CODE_MANAGE_response.md
D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\messenger\WORKFLOW_RULES.md
```

CODE_MANAGE messenger URL:

```text
https://chatgpt.com/c/6a15ab66-1080-83ea-a8ab-38e06a452642
```

Target file:

```text
D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\workflow_orchestrator.py
```

Task objective:

```text
Verify whether Codex can access workflow_orchestrator.py as a raw local file from byte 1 to EOF, rather than only through indexed/chunked retrieval.
```

Success requires evidence that Codex can:

1. Read `workflow_orchestrator.py` from beginning to end.
2. Count exact bytes, characters, and lines.
3. Produce exact line-numbered beginning, middle, and ending excerpts.
4. Generate a Python AST symbol/function/class map with exact line ranges.
5. Search the file deterministically with exact line numbers.
6. Report whether the evidence proves raw local-file access rather than chunked/indexed retrieval access.

## Current State

CODE_MANAGE provided a Codex handoff packet for verifying raw local-file ownership of `workflow_orchestrator.py`.

The extracted CODE_MANAGE response has been recorded in `CODE_MANAGE_response.md` and pushed.

Execution is paused until the user confirms starting STEP 1.

## Mandatory Execution And Reporting Rules

Follow `WORKFLOW_RULES.md` exactly.

Before STEP 1:

```text
Wait for explicit user confirmation to start STEP 1.
```

For every step:

1. Run only the current step.
2. Record the exact result in `CODE_MANAGE_Progress.md` using the step's reporting format.
3. Include a local checkpoint time from `Get-Date -Format o` under the current step heading.
4. Commit and push only `CODE_MANAGE_Progress.md` with a task-specific commit message.
5. Send a short CODE_MANAGE messenger prompt asking it to review the attached progress file and confirm the next concrete action.
6. Attach `CODE_MANAGE_Progress.md` to the CODE_MANAGE messenger prompt.
7. Detect the new CODE_MANAGE assistant response after the submitted user message.
8. Extract the full response into `CODE_MANAGE_response.md` before any analysis.
9. Commit and push only `CODE_MANAGE_response.md`.
10. Process the response into `CODE_MANAGE_INSTRUCTIONS.md` only if CODE_MANAGE creates new executable steps.
11. Commit and push only `CODE_MANAGE_INSTRUCTIONS.md` after any instruction update.
12. Do not proceed to the next step until CODE_MANAGE confirms the current step.

Messenger prompt format:

```text
Please review attached CODE_MANAGE_Progress.md and confirm the next concrete action.
```

Blocked format:

```md
NEXT STEP BLOCKED
No future-step edits/proceeding
Do you need any additional files/logs for troubleshooting?
```

Do not edit `workflow_orchestrator.py`.

Do not summarize from memory.

Do not rely on indexed search, semantic retrieval, or chat-provided snippets.

Use direct filesystem reads only.

Use exact file paths and line numbers.

If output is too long, write the full output to the local report artifact requested in STEP 8 and report that path.

## Ready To Execute Steps

## STEP 1 - Confirm `workflow_orchestrator.py` exists and collect basic metadata

Run from the repository root:

```text
D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch
```

```powershell
Get-Item .\workflow_orchestrator.py | Format-List FullName,Length,LastWriteTime
```

Python fallback:

```python
from pathlib import Path

path = Path("workflow_orchestrator.py")
print("exists:", path.exists())
print("absolute_path:", path.resolve())
print("bytes:", path.stat().st_size if path.exists() else None)
print("modified:", path.stat().st_mtime if path.exists() else None)
```

Expected:

```text
exists: True
absolute_path: <absolute path ending in workflow_orchestrator.py>
bytes: <nonzero byte count>
modified: <file modified timestamp>
```

Progress reporting format:

````md
## STEP 1 - Confirm `workflow_orchestrator.py` exists and collect basic metadata

```text
<exact metadata output>
```
````

## STEP 2 - Read `workflow_orchestrator.py` from byte 1 to EOF

Run from the repository root shown in Standalone Execution Context.

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

Expected:

```text
file: <absolute path ending in workflow_orchestrator.py>
byte_count: <same nonzero byte count from STEP 1>
sha256: <64-character SHA-256 hash>
first_100_bytes: <repr of first 100 bytes>
last_100_bytes: <repr of last 100 bytes>
```

Progress reporting format:

````md
## STEP 2 - Read `workflow_orchestrator.py` from byte 1 to EOF

```text
<exact EOF verification output>
```
````

## STEP 3 - Count exact lines and characters

Run from the repository root shown in Standalone Execution Context.

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

Expected:

```text
character_count: <nonzero character count>
line_count: <nonzero exact line count>
first_line: <repr of first line>
last_line: <repr of last line>
```

Progress reporting format:

````md
## STEP 3 - Count exact lines and characters

```text
<exact line and character count output>
```
````

## STEP 4 - Produce exact line-numbered excerpts

Run from the repository root shown in Standalone Execution Context.

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

Expected:

```text
--- workflow_orchestrator.py:1-<up to 40> ---
<line-numbered beginning excerpt>

--- workflow_orchestrator.py:<middle start>-<middle end> ---
<line-numbered middle excerpt>

--- workflow_orchestrator.py:<end start>-<final line> ---
<line-numbered ending excerpt>
```

Progress reporting format:

````md
## STEP 4 - Produce exact line-numbered excerpts

```text
Beginning excerpt: yes
Middle excerpt: yes
End excerpt: yes
<include exact excerpt output or report artifact path if too long>
```
````

## STEP 5 - Generate the Python AST symbol map

Run from the repository root shown in Standalone Execution Context.

```python
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
```

Expected:

```text
symbol_count: <nonzero symbol count>

--- symbols ---
workflow_orchestrator.py:<start>-<end> <ClassDef|FunctionDef|AsyncFunctionDef> <symbol_name>
```

Progress reporting format:

````md
## STEP 5 - Generate the Python AST symbol map

```text
AST parse succeeded: yes
symbol_count: <exact symbol count>
<first symbols, last symbols, or report artifact path if too long>
```
````

## STEP 6 - Search for validation, prompt, schema, and ownership terms

Run from the repository root shown in Standalone Execution Context.

```python
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
```

Expected:

```text
--- matches for 'schema' ---
total_matches: <count>
--- matches for 'validate' ---
total_matches: <count>
--- matches for 'validation' ---
total_matches: <count>
--- matches for 'prompt' ---
total_matches: <count>
--- matches for 'citation' ---
total_matches: <count>
--- matches for 'line' ---
total_matches: <count>
--- matches for 'file' ---
total_matches: <count>
--- matches for 'chunk' ---
total_matches: <count>
--- matches for 'orchestrator' ---
total_matches: <count>
```

Progress reporting format:

````md
## STEP 6 - Search for validation, prompt, schema, and ownership terms

```text
schema: <count>
validate: <count>
validation: <count>
prompt: <count>
citation: <count>
line: <count>
file: <count>
chunk: <count>
orchestrator: <count>
<include exact search output or report artifact path if too long>
```
````

## STEP 7 - Produce the CODE_MANAGE file ownership report

Return the result in this exact structure:

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

Expected:

```text
Report contains one verdict: PASS, PARTIAL, or FAIL.
Report includes file metadata, EOF verification, excerpt status, AST symbol status, search counts, exact commands run, errors or limitations, and conclusion.
```

Progress reporting format:

````md
## STEP 7 - Produce the CODE_MANAGE file ownership report

```text
VERDICT: <PASS|PARTIAL|FAIL>
REPORT_LOCATION: <chat response or local report file path>
LINE_COUNT: <exact line count>
BYTE_COUNT: <exact byte count>
SHA256: <64-character SHA-256 hash>
SYMBOL_COUNT: <exact symbol count>
```
````

## STEP 8 - Optional stronger complete local report artifact if output is too long

Run this only if the regular report output is too long or truncated.

```python
from pathlib import Path
import ast
import hashlib
import re

target = Path("workflow_orchestrator.py")
report = Path("codex_file_ownership_report.md")

data = target.read_bytes()
text = target.read_text(encoding="utf-8")
lines = text.splitlines()
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

out = []
out.append("# Codex File Ownership Report")
out.append("")
out.append("## File metadata")
out.append(f"- Absolute path: `{target.resolve()}`")
out.append(f"- Byte count: `{len(data)}`")
out.append(f"- Character count: `{len(text)}`")
out.append(f"- Line count: `{len(lines)}`")
out.append(f"- SHA-256: `{hashlib.sha256(data).hexdigest()}`")
out.append("")
out.append("## EOF verification")
out.append(f"- First 100 bytes: `{repr(data[:100])}`")
out.append(f"- Last 100 bytes: `{repr(data[-100:])}`")
out.append(f"- First line: `{repr(lines[0] if lines else '')}`")
out.append(f"- Last line: `{repr(lines[-1] if lines else '')}`")
out.append("")
out.append("## Symbol map")
out.append(f"- Symbol count: `{len(symbols)}`")
out.append("")
for start, end, kind, name in symbols:
    out.append(f"- `{target}:{start}-{end}` `{kind}` `{name}`")
out.append("")
out.append("## Search verification")
for term in terms:
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    matches = [(i, line) for i, line in enumerate(lines, 1) if pattern.search(line)]
    out.append(f"### `{term}`")
    out.append(f"Total matches: `{len(matches)}`")
    for i, line in matches[:50]:
        out.append(f"- `{target}:{i}` {line[:240]}")
    if len(matches) > 50:
        out.append(f"- Truncated in report: {len(matches) - 50} additional matches")
    out.append("")

report.write_text("\n".join(out), encoding="utf-8")
print(f"Wrote {report.resolve()}")
```

Expected:

```text
Wrote <absolute path ending in codex_file_ownership_report.md>
```

Required return format after STEP 8:

```md
The complete report was written to:

`codex_file_ownership_report.md`

Summary:
- PASS/PARTIAL/FAIL
- line count
- byte count
- SHA-256
- symbol count
```

Progress reporting format:

````md
## STEP 8 - Optional stronger complete local report artifact if output is too long

```text
REPORT_WRITTEN: <absolute path ending in codex_file_ownership_report.md>
VERDICT: <PASS|PARTIAL|FAIL>
LINE_COUNT: <exact line count>
BYTE_COUNT: <exact byte count>
SHA256: <64-character SHA-256 hash>
SYMBOL_COUNT: <exact symbol count>
```
````

## Blocked Reporting Format

If any step fails or cannot be confirmed, append only the requested diagnostic fields plus:

```md
NEXT STEP BLOCKED
No future-step edits/proceeding
Do you need any additional files/logs for troubleshooting?
```

## Constraints

Do not edit `workflow_orchestrator.py`.

Do not summarize from memory.

Do not rely on indexed search, semantic retrieval, or chat-provided snippets.

Use direct filesystem reads only.

Use exact file paths and line numbers.

If any output is too long, write the full output to a local report file and show the report file path.
