# CODE_MANAGE Instructions

Source response file: `CODE_MANAGE_response.md`
Source checkpoint: `2026-05-26T11:21:32.4338044-05:00`

## Current State

CODE_MANAGE provided a Codex handoff packet for verifying raw local-file ownership of `workflow_orchestrator.py`.

The extracted CODE_MANAGE response has been recorded in `CODE_MANAGE_response.md` and pushed.

Execution is paused until the user confirms starting STEP 1.

## Ready To Execute Steps

## STEP 1 - Confirm `workflow_orchestrator.py` exists and collect basic metadata

Run from the project root.

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

## STEP 2 - Read `workflow_orchestrator.py` from byte 1 to EOF

Run from the project root.

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

## STEP 3 - Count exact lines and characters

Run from the project root.

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

## STEP 4 - Produce exact line-numbered excerpts

Run from the project root.

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

## STEP 5 - Generate the Python AST symbol map

Run from the project root.

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

## STEP 6 - Search for validation, prompt, schema, and ownership terms

Run from the project root.

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

## Constraints

Do not edit `workflow_orchestrator.py`.

Do not summarize from memory.

Do not rely on indexed search, semantic retrieval, or chat-provided snippets.

Use direct filesystem reads only.

Use exact file paths and line numbers.

If any output is too long, write the full output to a local report file and show the report file path.
