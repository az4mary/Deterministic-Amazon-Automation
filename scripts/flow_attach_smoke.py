from pathlib import Path
import os
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CDP_URL = os.getenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
FLOW_URL = os.getenv(
    "FLOW_URL",
    "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28",
)

DASHCAM_IMAGES = [
    r"D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\data\images\Dashcam_driver_facing_view.png",
    r"D:\PROJECTS\GITHUB\az4mary\Deterministic-Amazon-Automation-codex_branch\data\images\Dashcam_road_facing_view.png",
]

TEST_PROMPT = "Test prompt: create a simple dashcam product image using the attached reference images."

for image in DASHCAM_IMAGES:
    if not Path(image).exists():
        raise SystemExit(f"Missing image: {image}")


def first_visible(page, selectors):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                return loc, sel
        except Exception:
            pass
    return None, None


def click_first(page, selectors, label, wait_ms=1000):
    loc, sel = first_visible(page, selectors)
    if not loc:
        print(f"Not found: {label}")
        return False

    print(f"Click {label}: {sel}")
    loc.click(force=True, timeout=10000)
    page.wait_for_timeout(wait_ms)
    return True


def upload_images(page):
    # Step A: open Add Media menu.
    click_first(page, [
        "text=Add Media",
        "button:has-text('Add Media')",
        "[role='button']:has-text('Add Media')",
        "[aria-label*='Add Media']",
        "button[aria-label*='Add']",
    ], "Add Media", wait_ms=1500)

    # Step B: click the actual upload action and catch the file chooser.
    upload_selectors = [
        "text=Upload",
        "text=Upload files",
        "text=Upload file",
        "text=Upload from computer",
        "text=From computer",
        "button:has-text('Upload')",
        "[role='button']:has-text('Upload')",
        "[aria-label*='Upload']",
        "[aria-label*='upload']",
        "button:has-text('Add Media')",
        "[role='button']:has-text('Add Media')",
    ]

    for sel in upload_selectors:
        try:
            loc = page.locator(sel).first
            if not loc.count() or not loc.is_visible():
                continue

            print(f"Try file chooser via: {sel}")
            with page.expect_file_chooser(timeout=5000) as fc:
                loc.click(force=True, timeout=10000)

            chooser = fc.value
            chooser.set_files(DASHCAM_IMAGES)
            print("Uploaded via file chooser.")
            page.wait_for_timeout(7000)
            return

        except PlaywrightTimeoutError:
            continue
        except Exception as exc:
            print(f"Upload selector skipped: {sel} | {str(exc)[:200]}")

    # Step C: fallback to hidden/created file input.
    try:
        inputs = page.locator("input[type=file]")
        count = inputs.count()
        print(f"input[type=file] count: {count}")

        if count:
            inputs.last.set_input_files(DASHCAM_IMAGES)
            print("Uploaded via input[type=file].")
            page.wait_for_timeout(7000)
            return
    except Exception as exc:
        print(f"file input fallback failed: {exc}")

    # Debug print visible controls.
    print("\nVisible buttons/controls:")
    controls = page.locator("button, [role='button']")
    for i in range(min(controls.count(), 40)):
        try:
            c = controls.nth(i)
            if c.is_visible():
                txt = (c.inner_text(timeout=500) or "").strip()
                aria = c.get_attribute("aria-label") or ""
                label = txt or aria
                if label:
                    print("-", label[:120])
        except Exception:
            pass

    raise SystemExit("Upload failed: no file chooser or input[type=file] found.")


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

    upload_images(page)

    # Open uploaded media / gallery.
    click_first(page, [
        "text=View uploaded media",
        "[aria-label*='View uploaded media']",
        "button:has-text('View uploaded media')",
        "[role='button']:has-text('View uploaded media')",
        "text=All Media",
        "button:has-text('All Media')",
        "[role='button']:has-text('All Media')",
    ], "Uploaded Media", wait_ms=2000)

    # Click first large media asset.
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
        for i in range(min(locs.count(), 50)):
            try:
                img = locs.nth(i)
                if not img.is_visible():
                    continue
                box = img.bounding_box() or {}
                if box.get("width", 0) < 48 or box.get("height", 0) < 48:
                    continue

                print(f"Click asset: {sel} [{i}]")
                img.click(force=True, timeout=10000)
                page.wait_for_timeout(2500)
                clicked_asset = True
                break
            except Exception:
                pass
        if clicked_asset:
            break

    if not clicked_asset:
        raise SystemExit("No uploaded media asset clicked.")

    # Click Add to Prompt.
    if not click_first(page, [
        "text=Add to Prompt",
        "text=Add to prompt",
        "button:has-text('Add to Prompt')",
        "[role='button']:has-text('Add to Prompt')",
        "button:has-text('Add to prompt')",
        "[role='button']:has-text('Add to prompt')",
        "[aria-label*='Add to Prompt']",
    ], "Add to Prompt", wait_ms=2500):
        raise SystemExit("No Add to Prompt button found.")

    # Fill prompt.
    prompt_box, sel = first_visible(page, [
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

    # Submit.
    if not click_first(page, [
        "text=Generate",
        "button:has-text('Generate')",
        "[role='button']:has-text('Generate')",
        "[aria-label*='Generate']",
        "text=Create",
        "button:has-text('Create')",
        "[role='button']:has-text('Create')",
        "[aria-label*='Create']",
    ], "Generate", wait_ms=1000):
        print("No Generate button found; pressing Control+Enter")
        page.keyboard.press("Control+Enter")

    print("Submitted.")
    time.sleep(3)
