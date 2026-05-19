# WORKFLOW_RULES

## PART 1 - Mandatory Messenger Workflow Rules

1. These rules apply to any task assigned to Codex that involves interacting with a messenger, including Codex_Tech, PROMPTS_GEN, or any future ChatGPT messenger used as a workflow partner. They do not automatically apply to ordinary repo work that does not involve messenger interaction, and they do not override higher-priority platform, system, safety, or developer instructions. Always read this file before starting or resuming messenger workflow work. Treat this file as the live operating rule source.

2. Do not create automation-based waits for messenger workflow pauses. Waits are tracked by local time.

3. Before sending a new messenger prompt, wait at least 5 minutes from the local time when the last messenger response was detected or extracted. Record the local checkpoint time using PowerShell `Get-Date -Format o`, including fractional seconds and UTC offset, for example `2026-05-19T00:42:30.9338090-05:00`. In `Codex_Tech_Progress.md`, place it under the current step heading as:

```md
Local checkpoint time:
- `2026-05-19T00:42:30.9338090-05:00`
```

In `Codex_Tech_response.md`, place it in the checkpoint title and repeat it in the metadata block as:

```md
# Codex_Tech Messenger Checkpoint - 2026-05-19T00:41:43.7506145-05:00

- Source URL: https://chatgpt.com/c/...
- Page title: ...
- Local checkpoint time: `2026-05-19T00:41:43.7506145-05:00`
- Response detection: latest assistant response detected and stable
```

4. Messenger response handling order is mandatory:
    - Detect any new assistant response after the submitted prompt.
    - Do not wait only for a predicted PASS or FAIL phrase.
    - Extract the full new assistant response into the active messenger response file first, such as `Codex_Tech_response.md`.
    - The active messenger response file must contain only the extracted messenger response/checkpoint fields and the format requested by the messenger. Do not add unrelated local command output, browser helper notes, speculation, diagnostics, or extra activity unless the messenger explicitly requested those fields.
    - For future messengers, use `<MessengerName>_response.md` unless the user specifies a different active response file.
    - Immediately commit the response file with a task-specific commit title/message, then push it to `origin codex_branch`.
    - Only after that push, process the response into the active instruction or progress file.

Each reasonable update to each messenger workflow file must be committed and pushed separately for tracking. For now, `codex_branch` is the only available branch for this workflow. A commit title/message is the Git commit message, not a required markdown heading inside the file. Use task-specific commit messages that clearly identify the file role and step, such as `Extract Codex_Tech STEP B response`, `Translate Codex_Tech STEP B instructions`, or `Record Codex_Tech STEP B progress`.

5. Do not analyze, summarize, classify, recommend fixes, choose cleanup, or decide the next action before the messenger response has been extracted into the response file and pushed. All analysis must come after extraction.

6. Translate the extracted messenger response into the active instruction file only when it creates real executable next steps. For this messenger, use `Codex_Tech_INSTRUCTIONS.md`. For future messengers, use `<MessengerName>_INSTRUCTIONS.md` unless the user specifies a different active instruction file. Immediately commit the instruction file with a task-specific commit title/message, then push it after editing it.

7. Write executable steps clearly and separately. Each patch, validation, cleanup, diagnostic, and follow-up must be its own STEP. Use this label style: `STEP 1 - PATCH_12J1 - Allow Flow adapter to receive a shared browser adapter`.

8. Update the active progress file after each STEP or diagnostic. For this messenger, use `Codex_Tech_Progress.md`. For future messengers, use `<MessengerName>_Progress.md` unless the user specifies a different active progress file. The progress file must contain only what the messenger explicitly requested, in the same format the messenger requested. Do not add unrelated local browser notes, helper-command notes, speculation, or extra local activity that may confuse the messenger. Immediately commit the progress file with a task-specific commit title/message, then push it after editing it.

9. Composer prompts to the messenger must be short, normally 1 or 2 lines. Put requested diagnostic details in the progress file, attach the progress file, allow upload to complete, then ask the messenger to review the attached progress file and confirm the next action.

10. If the messenger asks for a specific response format, follow that exact format. If the messenger asks for diagnostic fields, provide only those fields unless the messenger asks for more.

11. Every STEP in the instruction file must be completed and confirmed before the next workflow task or patch set can proceed. If a step is not confirmed, the next step is blocked.

12. If a failure, mismatch, timeout, missing confirmation, or troubleshooting request occurs, immediately state `NEXT STEP BLOCKED` and `No future-step edits/proceeding` in the report/progress file. Do not edit future steps. Focus only on the current blocked step.

13. When blocked or failed, report to the messenger with the requested artifacts/logs only, and explicitly ask: `Do you need any additional files/logs for troubleshooting?`

14. Do not recommend fixes, cleanup, next diagnostics, or future edits yourself. Recommendations, cleanup instructions, and next diagnostic actions must come from the messenger after the extracted response is processed.

15. Do not cleanup temporary files, generated artifacts, caches, logs, screenshots, or troubleshooting evidence unless the messenger or user confirms cleanup. For messenger workflows, preservation wins over generic cleanup rules until cleanup is explicitly confirmed. If the user explicitly requests cleanup, clean only the confirmed artifacts and leave unrelated dirty worktree entries untouched. Ask the messenger for cleanup instructions before a new patch set or whenever artifacts may affect later steps.

16. If local PC, browser, network, or sandbox interruption stops a workflow, resume from the last local checkpoint. Record the interruption and local resume time in the appropriate response/progress file before continuing. If a local tool, browser, sandbox, filesystem, or environment issue blocks the assigned task and is not part of the current messenger troubleshooting task, report it directly to the user. If the issue is part of the current messenger task, record it in the active progress file using the blocked-state rules and ask the messenger whether additional files or logs are needed.

## PART 2 - Messenger Interaction Best Practices

These practices are learned from the Codex_Tech messenger task and should guide future messenger work. They do not replace PART 1. If there is any conflict, PART 1 controls.

1. Treat the browser as an unreliable observation surface until each state is confirmed from the active target. A visible browser reply is not enough by itself; confirm the selected ChatGPT tab URL, page title, transcript state, composer state, and latest message state from the same active page object.

2. Prefer exact active-tab selection over convenience. Before reading, attaching, typing, or submitting, list the available ChatGPT targets and bind the automation to the intended conversation URL or the intended new temporary conversation. Avoid acting on the first ChatGPT tab when multiple tabs exist.

3. Keep test conversations separate from production messenger conversations. Use a temporary new ChatGPT conversation for isolation tests, and only migrate to a new dedicated messenger conversation when the messenger or user confirms that the old target conversation is likely the issue.

4. Confirm attachments from composer-scoped signals, not page-wide text. The strongest confirmation is the active composer form showing the expected `Remove file N: <filename>` controls, stable attachment count, no active upload indicators, no pending state, no error alerts, and no real progress bars. Do not treat the word `Progress` inside a filename as an upload progress signal.

5. Expect ChatGPT to rename repeated uploads. A displayed name like `Codex_Tech_Progress(5).md` can still represent the correct local file. Record the displayed upload name when relevant, but keep local workflow references pointed at the real active file name.

6. Before typing into a new or reused composer, verify the composer is empty and has zero unintended attachments. If a draft exists, clear it and re-check the composer text, attachment count, and send-button state before attaching or typing.

7. Use short messenger prompts in the composer. Put diagnostic detail, logs, and step reports in the active progress file. The composer prompt should normally ask the messenger to review the attached file and confirm the next concrete action.

8. Type and submit carefully. Multiline prompts can be split into multiple user turns if Enter is interpreted as send. Prefer a short one-line or two-line prompt. If multiline text is required, verify the full prompt remains in one composer draft before submitting.

9. Scope send-button detection to the active composer form. Page-wide button searches can click sidebar or history controls. Use the send control nearest the active composer, and confirm submission only when a new user message appears in the transcript.

10. Do not classify a step as PASS only because the expected phrase appears somewhere on the page. Confirm it appears in a new assistant transcript message after the submitted user message, then extract that assistant message into the response file before any analysis.

11. Wait for any new assistant response, not only an expected PASS or FAIL phrase. The messenger may ask for more diagnostics, correct the procedure, or provide a conditional next action. Extract the full response first and process it afterward.

12. Use fallback transcript extraction whenever the primary wait misses a visible reply. A primary wait timeout is an observation failure until a scoped transcript check proves there is no new assistant message.

13. Keep blocked reports minimal and exact. If a step fails or cannot be confirmed, write the requested fields only, include `NEXT STEP BLOCKED`, include `No future-step edits/proceeding`, and ask whether additional files or logs are needed.

14. Do not mix local helper details into messenger-facing files unless explicitly requested. Browser scripts, internal command choices, and local troubleshooting notes can confuse the messenger when it asked only for diagnostic fields or a PASS/FAIL result.

15. Preserve evidence until cleanup is confirmed. Temporary diagnostic files, screenshots, logs, and generated artifacts may be needed later; do not delete them just because the immediate step passed.

## PART 3 - Usable Messenger Scripts And Commands

These command and script patterns are approved helpers for messenger workflow diagnostics. Adapt paths, target IDs, filenames, and prompt text to the active messenger. Do not paste long helper output into messenger-facing files unless the messenger explicitly asks for it.

### Local Checkpoint And Git Commands

Use these commands to capture local time, inspect the worktree, and push only the confirmed messenger files:

```powershell
Get-Date -Format o
git status --short
git diff -- WORKFLOW_RULES.md Codex_Tech_response.md Codex_Tech_INSTRUCTIONS.md Codex_Tech_Progress.md
git add -- Codex_Tech_response.md
git commit -m "Extract Codex_Tech messenger response"
git push origin codex_branch
```

Use this wait pattern for the required local-time pause. Replace the timestamp with the correct checkpoint plus at least 5 minutes:

```powershell
$target = Get-Date '2026-05-19T00:30:55-05:00'
$now = Get-Date
if ($now -lt $target) {
  $seconds = [int][Math]::Ceiling(($target - $now).TotalSeconds)
  Start-Sleep -Seconds $seconds
}
Get-Date -Format o
```

Use these read-only remote-debugging checks before browser work:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/version' -TimeoutSec 5 | ConvertTo-Json -Depth 4
Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/list' -TimeoutSec 5 | ConvertTo-Json -Depth 4
```

Use this placeholder dry-run check before replacing an initialized response file. Replace the messenger name and placeholder text as needed. If the count is not exactly `1`, do not use that replacement path; re-read the current file and choose a new exact target or rewrite the active response file with a confirmed full-file patch.

```powershell
(Select-String -LiteralPath 'D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\PROMPTS_GEN_response.md' -Pattern 'NOT EXTRACTED YET - active PROMPTS_GEN response file initialized.' -SimpleMatch).Count
```

Use this command to open a new temporary ChatGPT tab in the same remote-debugging browser session:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/new?https%3A%2F%2Fchatgpt.com%2F' -Method Put -TimeoutSec 10
```

### CDP Python Helper Skeleton

Use this skeleton when direct Chrome DevTools Protocol access is needed without extra Python packages. It connects to a known page target from `/json/list`, evaluates page state, and can be extended for attach/type/submit/extract steps.

```python
import base64
import json
import os
import socket
import struct
import time
import urllib.request

TARGET_ID = "REPLACE_WITH_PAGE_TARGET_ID"

def get_ws(target_id):
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=5))
    for tab in tabs:
        if tab.get("id") == target_id:
            return tab["webSocketDebuggerUrl"]
    raise SystemExit("target not found")

class CDP:
    def __init__(self, wsurl):
        rest = wsurl[5:]
        hostport, path = rest.split("/", 1)
        host, port = hostport.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {hostport}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode())
        response = b""
        while b"\r\n\r\n" not in response:
            response += self.sock.recv(4096)
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(response[:500])
        self.next_id = 1

    def send_frame(self, text):
        payload = text.encode("utf-8")
        header = bytearray([0x81])
        size = len(payload)
        if size < 126:
            header.append(0x80 | size)
        elif size < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", size))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", size))
        mask = os.urandom(4)
        header.extend(mask)
        self.sock.sendall(bytes(header) + bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload)))

    def recv_frame(self):
        head = self.sock.recv(2)
        b1, b2 = head
        size = b2 & 0x7F
        if size == 126:
            size = struct.unpack("!H", self.sock.recv(2))[0]
        elif size == 127:
            size = struct.unpack("!Q", self.sock.recv(8))[0]
        data = b""
        if b2 & 0x80:
            mask = self.sock.recv(4)
            while len(data) < size:
                data += self.sock.recv(size - len(data))
            data = bytes(byte ^ mask[i % 4] for i, byte in enumerate(data))
        else:
            while len(data) < size:
                data += self.sock.recv(size - len(data))
        opcode = b1 & 0x0F
        if opcode == 8:
            raise RuntimeError("websocket closed")
        if opcode == 9:
            return self.recv_frame()
        return data.decode("utf-8", "replace")

    def call(self, method, params=None, timeout=20):
        call_id = self.next_id
        self.next_id += 1
        self.send_frame(json.dumps({"id": call_id, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            self.sock.settimeout(max(0.1, end - time.time()))
            message = json.loads(self.recv_frame())
            if message.get("id") == call_id:
                return message
        raise TimeoutError(method)

def evaluate(cdp, expression, timeout=20):
    result = cdp.call(
        "Runtime.evaluate",
        {"expression": expression, "awaitPromise": True, "returnByValue": True},
        timeout=timeout,
    )
    return result.get("result", {}).get("result", {}).get("value")

cdp = CDP(get_ws(TARGET_ID))
for method in ["Page.enable", "Runtime.enable", "DOM.enable"]:
    cdp.call(method, timeout=5)
cdp.call("Page.bringToFront", timeout=5)
print(json.dumps(evaluate(cdp, "({ url: location.href, title: document.title })"), indent=2))
```

### Composer Readiness Probe

Use this page expression to confirm the active ChatGPT composer before attaching or typing:

```javascript
(() => {
  const composer = document.querySelector(
    '#prompt-textarea, div.ProseMirror[contenteditable="true"], [contenteditable="true"][data-lexical-editor="true"]'
  );
  const form = composer ? composer.closest("form") : null;
  const alerts = [...document.querySelectorAll('[role="alert"], [data-testid*="error" i]')]
    .map((element) => element.innerText)
    .filter(Boolean);
  return {
    url: location.href,
    title: document.title,
    readyState: document.readyState,
    composer_present: !!composer,
    composer_visible: composer ? !!(composer.offsetWidth || composer.offsetHeight || composer.getClientRects().length) : false,
    composer_enabled: composer ? !composer.closest('[aria-disabled="true"]') : false,
    composer_text: composer ? composer.innerText : null,
    composer_form_present: !!form,
    active_error_alerts: alerts,
  };
})()
```

### Attachment Confirmation Probe

Use this page expression after `DOM.setFileInputFiles`. It intentionally avoids treating filenames such as `Codex_Tech_Progress.md` as upload progress.

```javascript
(() => {
  const composer = document.querySelector(
    '#prompt-textarea, div.ProseMirror[contenteditable="true"], [contenteditable="true"][data-lexical-editor="true"]'
  );
  const scope = composer?.closest("form") || document;
  const remove = [...scope.querySelectorAll("button,[aria-label]")]
    .map((element) => element.getAttribute("aria-label") || element.innerText || "")
    .filter((text) => /^Remove file/i.test(text));
  const alerts = [...document.querySelectorAll('[role="alert"], [data-testid*="error" i]')]
    .map((element) => element.innerText)
    .filter(Boolean);
  const uploadingSignals = [...scope.querySelectorAll('[aria-label*="upload" i], [data-testid*="upload" i]')]
    .filter((element) => !/^Remove file/i.test(element.getAttribute("aria-label") || ""))
    .map((element) => element.getAttribute("aria-label") || element.innerText || "")
    .filter(Boolean);
  const progressBars = [...scope.querySelectorAll('[role="progressbar"], progress')].length;
  return {
    attachment_count: remove.length,
    remove_file_signals: remove,
    uploading: uploadingSignals.length > 0,
    pending: false,
    error: alerts.length > 0,
    progress: progressBars > 0,
    uploading_signals: uploadingSignals,
    progress_bars: progressBars,
    active_error_alerts: alerts,
  };
})()
```

### Transcript Extraction Probe

Use this page expression after submitting a messenger prompt. Treat `Thinking` as not final. Extract the latest assistant text into the active response file before analysis.

```javascript
(() => {
  const articles = [...document.querySelectorAll("article,[data-message-author-role]")]
    .map((element, index) => ({
      index,
      role: element.getAttribute("data-message-author-role") || "",
      text: (element.innerText || "").trim(),
    }));
  const users = articles.filter((message) => message.role === "user");
  const assistants = articles.filter(
    (message) => message.role === "assistant" && message.text && message.text !== "Thinking"
  );
  const thinking =
    (document.body.innerText || "").includes("Thinking") ||
    !!document.querySelector('[aria-label*="Stop"], button[aria-label*="Stop"]');
  return {
    url: location.href,
    title: document.title,
    user_count: users.length,
    assistant_count: assistants.length,
    latest_user: users.at(-1) || null,
    latest_assistant: assistants.at(-1) || null,
    thinking,
  };
})()
```

Use this full read-only PowerShell command when a messenger response is visible in ChatGPT and Codex needs to extract the active tab transcript through Chrome remote debugging. First get the correct `TARGET_ID` from `/json/list`, then replace `TARGET_ID` below with the page id for the intended messenger tab.

```powershell
@'
import urllib.request, json, socket, base64, os, struct, time
TARGET_ID='REPLACE_WITH_PAGE_TARGET_ID'

def get_ws(target_id):
    tabs=json.load(urllib.request.urlopen('http://127.0.0.1:9222/json/list', timeout=5))
    for t in tabs:
        if t.get('id')==target_id:
            return t['webSocketDebuggerUrl']
    raise SystemExit('target not found')

class CDP:
    def __init__(self, wsurl):
        rest=wsurl[5:]; hostport,path=rest.split('/',1); host,port=hostport.split(':')
        self.s=socket.create_connection((host,int(port)), timeout=10)
        key=base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        resp=b''
        while b'\r\n\r\n' not in resp: resp+=self.s.recv(4096)
        if b' 101 ' not in resp.split(b'\r\n',1)[0]: raise RuntimeError(resp[:500])
        self.next_id=1

    def sf(self,t):
        p=t.encode('utf-8'); h=bytearray([0x81]); n=len(p)
        if n<126: h.append(0x80|n)
        elif n<65536: h.append(0x80|126); h.extend(struct.pack('!H',n))
        else: h.append(0x80|127); h.extend(struct.pack('!Q',n))
        m=os.urandom(4); h.extend(m); self.s.sendall(bytes(h)+bytes(b^m[i%4] for i,b in enumerate(p)))

    def rf(self):
        h=self.s.recv(2); b1,b2=h; n=b2&0x7f
        if n==126: n=struct.unpack('!H', self.s.recv(2))[0]
        elif n==127: n=struct.unpack('!Q', self.s.recv(8))[0]
        data=b''
        if b2&0x80:
            m=self.s.recv(4)
            while len(data)<n: data+=self.s.recv(n-len(data))
            data=bytes(x^m[i%4] for i,x in enumerate(data))
        else:
            while len(data)<n: data+=self.s.recv(n-len(data))
        if (b1&0xf)==8: raise RuntimeError('websocket closed')
        if (b1&0xf)==9: return self.rf()
        return data.decode('utf-8','replace')

    def call(self, method, params=None, timeout=20):
        cid=self.next_id; self.next_id+=1
        self.sf(json.dumps({'id':cid,'method':method,'params':params or {}}))
        end=time.time()+timeout
        while time.time()<end:
            self.s.settimeout(max(.1,end-time.time()))
            msg=json.loads(self.rf())
            if msg.get('id')==cid: return msg
        raise TimeoutError(method)

def ev(cdp, expr, timeout=20):
    return cdp.call('Runtime.evaluate', {'expression':expr,'awaitPromise':True,'returnByValue':True}, timeout=timeout).get('result',{}).get('result',{}).get('value')

cdp=CDP(get_ws(TARGET_ID))
for m in ['Runtime.enable','DOM.enable','Page.enable']: cdp.call(m, timeout=5)
cdp.call('Page.bringToFront', timeout=5)
expr=r'''(() => {
  const articles = [...document.querySelectorAll('article,[data-message-author-role]')]
    .map((element, index) => ({
      index,
      role: element.getAttribute('data-message-author-role') || '',
      text: (element.innerText || '').trim(),
    }));
  const users = articles.filter((message) => message.role === 'user');
  const assistants = articles.filter((message) => message.role === 'assistant' && message.text && message.text !== 'Thinking');
  const thinking = (document.body.innerText || '').includes('Thinking') || !!document.querySelector('[aria-label*="Stop"], button[aria-label*="Stop"]');
  return {
    url: location.href,
    title: document.title,
    user_count: users.length,
    assistant_count: assistants.length,
    latest_user: users.at(-1) || null,
    latest_assistant: assistants.at(-1) || null,
    thinking,
    articles: articles.slice(-8),
  };
})()'''
state=ev(cdp,expr,timeout=20)
print(json.dumps(state, indent=2))
'@ | python -
```
