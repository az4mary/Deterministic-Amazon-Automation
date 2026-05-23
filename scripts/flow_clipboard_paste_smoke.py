from pathlib import Path
import os
import subprocess
import time
from playwright.sync_api import sync_playwright

CDP_URL = os.getenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
FLOW_URL = os.getenv(
    "FLOW_URL",
    "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28",
)

DASHCAM_IMAGES = [
    r"D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\data\images\Dashcam_driver_facing_view.png",
    r"D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\data\images\Dashcam_road_facing_view.png",
]

TEST_PROMPT = "Test prompt: create a simple commercial dashcam product image using the pasted reference images."

for image in DASHCAM_IMAGES:
    if not Path(image).exists():
        raise SystemExit(f"Missing image: {image}")


def copy_image_to_windows_clipboard(image_path):
    ps = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Path = @'
{image_path}
'@

$img = [System.Drawing.Image]::FromFile($Path)
$bmp = New-Object System.Drawing.Bitmap $img
$img.Dispose()

[System.Windows.Forms.Clipboard]::SetImage($bmp)
Start-Sleep -Milliseconds 300
"""

    subprocess.run(
        [
            "powershell.exe",
            "-STA",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps,
        ],
        check=True,
    )


def first_visible(page, selectors):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                return loc, sel
        except Exception:
            pass
    return None, None


def get_prompt_box(page):
    prompt_box, sel = first_visible(
        page,
        [
            "textarea",
            "[contenteditable='true']",
            "div[role='textbox']",
            "[role='textbox']",
        ],
    )
    if not prompt_box:
        raise SystemExit("No Flow composer prompt box found.")
    return prompt_box, sel


def paste_images_into_composer(page):
    prompt_box, sel = get_prompt_box(page)
    print(f"Composer found: {sel}")

    prompt_box.click(force=True)
    page.wait_for_timeout(500)

    # Type prompt first. Do not Ctrl+A after images are pasted.
    print("Typing prompt")
    try:
        prompt_box.fill(TEST_PROMPT)
    except Exception:
        page.keyboard.insert_text(TEST_PROMPT)

    page.wait_for_timeout(700)

    for image_path in DASHCAM_IMAGES:
        print(f"Copy image to clipboard: {image_path}")
        copy_image_to_windows_clipboard(image_path)

        print("Paste image into composer: Ctrl+V")
        prompt_box.click(force=True)
        page.keyboard.press("Control+V")

        # Give Flow time to render the pasted attachment/chip.
        page.wait_for_timeout(5000)


def click_submit_arrow(page):
    prompt_box, _ = get_prompt_box(page)
    rect = prompt_box.bounding_box() or {}

    print("Click submit button")

    # Prefer an actual visible submit/arrow button near the composer.
    buttons = page.locator("button, [role='button']")
    for i in range(min(buttons.count(), 120)):
        try:
            btn = buttons.nth(i)
            if not btn.is_visible() or not btn.is_enabled():
                continue

            text = (btn.inner_text(timeout=500) or "").strip()
            aria = btn.get_attribute("aria-label") or ""
            label = f"{text} {aria}".strip()
            norm = label.lower()

            if any(bad in norm for bad in ["add", "add_2", "media", "upload", "attach", "agent", "nano banana", "imagen"]):
                continue

            if not any(good in norm for good in ["submit", "send", "generate", "create", "arrow_forward"]):
                continue

            box = btn.bounding_box() or {}
            if not box:
                continue

            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2

            near_composer = (
                rect["x"] - 80 <= cx <= rect["x"] + rect["width"] + 180
                and rect["y"] - 120 <= cy <= rect["y"] + rect["height"] + 160
            )

            if not near_composer:
                continue

            print(f"Click submit: {label!r}")
            btn.click(force=True, timeout=10000)
            page.wait_for_timeout(3000)
            print("Submitted.")
            return

        except Exception:
            pass

    # Fallback: click the right-side composer arrow area.
    x = rect["x"] + rect["width"] + 36
    y = rect["y"] + rect["height"] / 2
    print("Submit selector not found; clicking right-side composer arrow fallback")
    page.mouse.click(x, y)
    page.wait_for_timeout(3000)
    print("Submitted by coordinate fallback.")


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)

    page = None
    for ctx in browser.contexts:
        for candidate in ctx.pages:
            if "labs.google/fx/tools/flow" in (candidate.url or ""):
                page = candidate
                break
        if page:
            break

    if page is None:
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()
        page.goto(FLOW_URL, wait_until="domcontentloaded")

    page.bring_to_front()
    page.wait_for_timeout(1500)

    print("Flow page:", page.url)

    paste_images_into_composer(page)
    click_submit_arrow(page)

    time.sleep(3)
