from pathlib import Path
import os
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

TEST_PROMPT = "Test prompt: create a simple dashcam product image using the attached reference image."

for p in DASHCAM_IMAGES:
    if not Path(p).exists():
        raise SystemExit(f"Missing image: {p}")

def click_first(page, selectors, label):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                print(f"Click {label}: {sel}")
                loc.click(force=True, timeout=10000)
                page.wait_for_timeout(1500)
                return True
        except Exception:
            pass
    return False

def find_first(page, selectors):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                return loc, sel
        except Exception:
            pass
    return None, None

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
    page.wait_for_timeout(2000)

    print("Flow page:", page.url)

    click_first(page, [
        "button:has-text('Add Media')",
        "[role='button']:has-text('Add Media')",
        "[aria-label*='Add Media']",
    ], "Add Media")

    file_input = page.locator("input[type=file]").last
    if not file_input.count():
        raise SystemExit("No input[type=file] found.")

    print("Uploading Dashcam images...")
    file_input.set_input_files(DASHCAM_IMAGES)
    page.wait_for_timeout(6000)

    click_first(page, [
        "[aria-label*='View uploaded media']",
        "button:has-text('View uploaded media')",
        "[role='button']:has-text('View uploaded media')",
        "button:has-text('All Media')",
        "[role='button']:has-text('All Media')",
    ], "Uploaded Media")

    # Click first visible uploaded/media asset to open preview/details.
    asset_clicked = False
    for sel in [
        "[role='button'] img",
        "[data-testid*='asset'] img",
        "[data-testid*='media'] img",
        "main img",
    ]:
        locs = page.locator(sel)
        for i in range(min(locs.count(), 30)):
            img = locs.nth(i)
            try:
                if not img.is_visible():
                    continue
                box = img.bounding_box() or {}
                if box.get("width", 0) < 48 or box.get("height", 0) < 48:
                    continue
                print(f"Click asset: {sel} [{i}]")
                img.click(force=True, timeout=10000)
                page.wait_for_timeout(2000)
                asset_clicked = True
                break
            except Exception:
                pass
        if asset_clicked:
            break

    if not asset_clicked:
        raise SystemExit("No visible uploaded asset clicked.")

    if not click_first(page, [
        "button:has-text('Add to Prompt')",
        "[role='button']:has-text('Add to Prompt')",
        "button:has-text('Add to prompt')",
        "[role='button']:has-text('Add to prompt')",
        "[aria-label*='Add to Prompt']",
    ], "Add to Prompt"):
        raise SystemExit("No Add to Prompt button found.")

    prompt_box, sel = find_first(page, [
        "textarea",
        "[contenteditable='true']",
        "div[role='textbox']",
        "[role='textbox']",
    ])

    if not prompt_box:
        raise SystemExit("No prompt composer found.")

    print(f"Fill prompt: {sel}")
    prompt_box.click(force=True)
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")

    try:
        prompt_box.fill(TEST_PROMPT)
    except Exception:
        page.keyboard.insert_text(TEST_PROMPT)

    page.wait_for_timeout(1000)

    if not click_first(page, [
        "button:has-text('Generate')",
        "[role='button']:has-text('Generate')",
        "[aria-label*='Generate']",
        "button:has-text('Create')",
        "[role='button']:has-text('Create')",
        "[aria-label*='Create']",
    ], "Generate"):
        print("No Generate button found; pressing Control+Enter")
        page.keyboard.press("Control+Enter")

    print("Submitted.")
    time.sleep(3)
