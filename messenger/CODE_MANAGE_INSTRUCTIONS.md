# CODE_MANAGE Instructions

Source response file: `CODE_MANAGE_response.md`
Source checkpoint: `2026-05-26T11:21:32.4338044-05:00`

Repository root:

```text
D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch
```

Target file:

```text
workflow_orchestrator.py
```

Objective:

```text
Verify raw local-file ownership of workflow_orchestrator.py from byte 1 to EOF, with exact metadata, counts, line-numbered excerpts, AST symbol ranges, deterministic search results, and a final file ownership report.
```

Before execution:

```text
Do not start STEP 1 until the user confirms.
```

After each step:

```text
Append only the requested result/report fields to CODE_MANAGE_Progress.md, commit and push CODE_MANAGE_Progress.md, send it to CODE_MANAGE for confirmation, extract CODE_MANAGE response into CODE_MANAGE_response.md, then commit and push CODE_MANAGE_response.md before continuing.
```

## STEP 1 - Confirm file exists and collect basic metadata

Run from the repository root.

```powershell
Get-Item .\workflow_orchestrator.py | Format-List FullName,Length,LastWriteTime
```

If needed, use this Python fallback:

```python
from pathlib import Path

path = Path("workflow_orchestrator.py")
print("exists:", path.exists())
print("absolute_path:", path.resolve())
print("bytes:", path.stat().st_size if path.exists() else None)
print("modified:", path.stat().st_mtime if path.exists() else None)
```

Expected result:

```text
exists: True
absolute_path: <absolute path ending in workflow_orchestrator.py>
bytes: <nonzero byte count>
modified: <file modified timestamp>
```

Progress reporting format:

````md
## STEP 1 - Confirm file exists and collect basic metadata

Local checkpoint time:
- `<Get-Date -Format o>`

```text
<exact metadata output>
```
````

## STEP 2 - Read file from byte 1 to EOF

Run from the repository root.

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

Expected result:

```text
file: <absolute path ending in workflow_orchestrator.py>
byte_count: <nonzero byte count>
sha256: <64-character SHA-256 hash>
first_100_bytes: <repr of first 100 bytes>
last_100_bytes: <repr of last 100 bytes>
```

Progress reporting format:

````md
## STEP 2 - Read file from byte 1 to EOF

Local checkpoint time:
- `<Get-Date -Format o>`

```text
<exact EOF verification output>
```
````

## STEP 3 - Count exact lines and characters

Run from the repository root.

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

Expected result:

```text
character_count: <nonzero character count>
line_count: <nonzero exact line count>
first_line: <repr of first line>
last_line: <repr of last line>
```

Progress reporting format:

````md
## STEP 3 - Count exact lines and characters

Local checkpoint time:
- `<Get-Date -Format o>`

```text
<exact line and character count output>
```
````

## STEP 4 - Produce line-numbered excerpts

Run from the repository root.

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

Expected result:

```text
Beginning excerpt with exact line numbers: produced
Middle excerpt with exact line numbers: produced
End excerpt with exact line numbers: produced
```

Progress reporting format:

````md
## STEP 4 - Produce line-numbered excerpts

Local checkpoint time:
- `<Get-Date -Format o>`

```text
Beginning excerpt: yes
Middle excerpt: yes
End excerpt: yes
<exact excerpt output or local report path if too long>
```
````

## STEP 5 - Generate AST symbol map

Run from the repository root.

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

print(f"symbol_count: {len(symbols)}")
print("\n--- symbols ---")
for start, end, kind, name in symbols:
    print(f"{path}:{start}-{end} {kind} {name}")
```

Expected result:

```text
AST parse succeeds.
symbol_count: <symbol count>
Each symbol line includes workflow_orchestrator.py:<start>-<end>, symbol kind, and symbol name.
```

Progress reporting format:

````md
## STEP 5 - Generate AST symbol map

Local checkpoint time:
- `<Get-Date -Format o>`

```text
AST parse succeeded: yes
symbol_count: <exact symbol count>
<exact symbol output or local report path if too long>
```
````

## STEP 6 - Search deterministic ownership terms

Run from the repository root.

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

Expected result:

```text
Each requested term is searched deterministically.
Each match includes workflow_orchestrator.py:<line number>.
Each term reports total_matches.
```

Progress reporting format:

````md
## STEP 6 - Search deterministic ownership terms

Local checkpoint time:
- `<Get-Date -Format o>`

```text
schema: <total_matches>
validate: <total_matches>
validation: <total_matches>
prompt: <total_matches>
citation: <total_matches>
line: <total_matches>
file: <total_matches>
chunk: <total_matches>
orchestrator: <total_matches>
<exact search output or local report path if too long>
```
````

## STEP 7 - Produce Codex File Ownership Report

Return the final report in this exact structure:

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

Expected result:

```text
The report contains the exact requested sections and a PASS, PARTIAL, or FAIL verdict.
```

Progress reporting format:

````md
## STEP 7 - Produce Codex File Ownership Report

Local checkpoint time:
- `<Get-Date -Format o>`

```text
VERDICT: <PASS|PARTIAL|FAIL>
REPORT_LOCATION: <chat response or local report file path>
LINE_COUNT: <exact line count>
BYTE_COUNT: <exact byte count>
SHA256: <64-character SHA-256 hash>
SYMBOL_COUNT: <exact symbol count>
```
````

## STEP 8 - Optional complete local report artifact if output is too long

Run only if the regular report output is too long or truncated.

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
        symbols.append((node.lineno, getattr(node, "end_lineno", node.lineno), type(node).__name__, node.name))
symbols.sort()

terms = ["schema", "validate", "validation", "prompt", "citation", "line", "file", "chunk", "orchestrator"]

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

Expected result:

```text
Wrote <absolute path ending in codex_file_ownership_report.md>
```

Required return format:

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
## STEP 8 - Optional complete local report artifact if output is too long

Local checkpoint time:
- `<Get-Date -Format o>`

```text
REPORT_WRITTEN: <absolute path ending in codex_file_ownership_report.md>
VERDICT: <PASS|PARTIAL|FAIL>
LINE_COUNT: <exact line count>
BYTE_COUNT: <exact byte count>
SHA256: <64-character SHA-256 hash>
SYMBOL_COUNT: <exact symbol count>
```
````

## Constraints

Do not edit `workflow_orchestrator.py`.

Do not summarize from memory.

Do not rely on indexed search, semantic retrieval, or chat-provided snippets.

Use direct filesystem reads only.

Use exact file paths and line numbers.

If any step fails or cannot be confirmed, append this to `CODE_MANAGE_Progress.md`:

```md
NEXT STEP BLOCKED
No future-step edits/proceeding
Do you need any additional files/logs for troubleshooting?
```
