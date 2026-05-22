from pathlib import Path
import os
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
CDP_URL = os.getenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
FLOW_URL = os.getenv(
    "FLOW_URL",
    "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28",
)

TEST_PROMPT = "Test prompt: generate a simple product image using the attached reference image."

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
image_candidates = [
    p for p in (ROOT / "data" / "images").glob("*")
    if p.is_file() and p.suffix.lower() in IMAGE_EXTS
]

if not image_candidates:
    raise SystemExit("No image found in data/images/")

image_path = image_candidates[0].resolve()
print(f"Using image: {image_path}")

def first_visible(page, selectors):
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

    add_media, sel = first_visible(page, [
        "button:has-text('Add Media')",
        "[role='button']:has-text('Add Media')",
        "button[aria-label*='Add Media']",
        "[aria-label*='Add Media']",
    ])

    if add_media:
        print("Click:", sel)
        add_media.click(force=True)
        page.wait_for_timeout(1500)

    file_input = page.locator("input[type=file]").last
    if not file_input.count():
        raise SystemExit("No input[type=file] found.")

    print("Uploading image...")
    file_input.set_input_files(str(image_path))
    page.wait_for_timeout(5000)

    uploaded_media, sel = first_visible(page, [
        "button:has-text('View uploaded media')",
        "[role='button']:has-text('View uploaded media')",
        "[aria-label*='View uploaded media']",
        "button:has-text('All Media')",
        "[role='button']:has-text('All Media')",
        "button:has-text('Uploaded media')",
        "[role='button']:has-text('Uploaded media')",
    ])

    if uploaded_media:
        print("Click:", sel)
        uploaded_media.click(force=True)
        page.wait_for_timeout(2000)

    clicked_asset = False
    for sel in [
        "[role='button'] img",
        "button img",
        "[data-testid*='asset'] img",
        "[data-testid*='media'] img",
        "[data-testid*='thumbnail'] img",
        "main img",
    ]:
        locs = page.locator(sel)
        for i in range(min(locs.count(), 40)):
            img = locs.nth(i)
            try:
                if not img.is_visible():
                    continue
                box = img.bounding_box() or {}
                if box.get("width", 0) < 48 or box.get("height", 0) < 48:
                    continue
                print("Click asset:", sel, i)
                img.click(force=True)
                clicked_asset = True
                page.wait_for_timeout(2000)
                break
            except Exception:
                pass
        if clicked_asset:
            break

    if not clicked_asset:
        raise SystemExit("No clickable uploaded media asset found.")

    add_to_prompt, sel = first_visible(page, [
        "button:has-text('Add to Prompt')",
        "[role='button']:has-text('Add to Prompt')",
        "button:has-text('Add to prompt')",
        "[role='button']:has-text('Add to prompt')",
        "button[aria-label*='Add to Prompt']",
        "[aria-label*='Add to Prompt']",
    ])

    if not add_to_prompt:
        raise SystemExit("No Add to Prompt button found.")

    print("Click:", sel)
    add_to_prompt.click(force=True)
    page.wait_for_timeout(2500)

    prompt_box, sel = first_visible(page, [
        "textarea",
        "[contenteditable='true']",
        "div[role='textbox']",
        "[role='textbox']",
        "input[type='text']",
    ])

    if not prompt_box:
        raise SystemExit("No prompt composer found.")

    print("Fill prompt:", sel)
    prompt_box.click(force=True)

    try:
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        prompt_box.fill(TEST_PROMPT)
    except Exception:
        page.keyboard.insert_text(TEST_PROMPT)

    page.wait_for_timeout(1000)

    generate, sel = first_visible(page, [
        "button:has-text('Generate')",
        "[role='button']:has-text('Generate')",
        "button[aria-label*='Generate']",
        "button:has-text('Create')",
        "[role='button']:has-text('Create')",
        "button[aria-label*='Create']",
    ])

    if generate:
        print("Click submit:", sel)
        generate.click(force=True)
    else:
        print("No Generate button found; pressing Control+Enter")
        page.keyboard.press("Control+Enter")

    print("Submitted test prompt.")
    time.sleep(3)
