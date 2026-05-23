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

TEST_PROMPT = "Test prompt: create a simple commercial dashcam product image using the attached reference images."

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


def find_prompt_box(page):
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
        raise SystemExit("No composer prompt box found.")
    return prompt_box, sel


def is_near_prompt(btn_box, prompt_box):
    cx = btn_box["x"] + btn_box["width"] / 2
    cy = btn_box["y"] + btn_box["height"] / 2

    return (
        prompt_box["x"] - 120 <= cx <= prompt_box["x"] + prompt_box["width"] + 180
        and prompt_box["y"] - 140 <= cy <= prompt_box["y"] + prompt_box["height"] + 180
    )


def click_composer_plus_upload(page):
    prompt_box, prompt_sel = find_prompt_box(page)
    prompt_rect = prompt_box.bounding_box() or {}

    print(f"Composer found: {prompt_sel}")

    candidates = page.locator("button, [role='button']")
    plus_button = None
    plus_label = ""

    for i in range(min(candidates.count(), 120)):
        try:
            btn = candidates.nth(i)
            if not btn.is_visible() or not btn.is_enabled():
                continue

            text = (btn.inner_text(timeout=500) or "").strip()
            aria = btn.get_attribute("aria-label") or ""
            label = f"{text} {aria}".strip()
            norm = label.lower()

            if not any(x in norm for x in ["+", "add", "add_2", "media", "upload", "attach"]):
                continue

            if any(x in norm for x in ["view uploaded media", "all media", "trash", "settings", "more"]):
                continue

            box = btn.bounding_box() or {}
            if not box or not is_near_prompt(box, prompt_rect):
                continue

            plus_button = btn
            plus_label = label
            break

        except Exception:
            pass

    if not plus_button:
        raise SystemExit("Composer + upload button not found.")

    print(f"Click composer + upload button: {plus_label!r}")

    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            plus_button.click(force=True, timeout=10000)
        fc.value.set_files(DASHCAM_IMAGES)
        print("Uploaded via composer + file chooser.")
        page.wait_for_timeout(10000)
        return
    except PlaywrightTimeoutError:
        print("No file chooser from + button; trying input[type=file] fallback.")

    try:
        inputs = page.locator("input[type=file]")
        count = inputs.count()
        print(f"input[type=file] count: {count}")
        if count:
            inputs.last.set_input_files(DASHCAM_IMAGES)
            print("Uploaded via input[type=file] fallback.")
            page.wait_for_timeout(10000)
            return
    except Exception as exc:
        raise SystemExit(f"Composer + upload failed: {exc}")

    raise SystemExit("Composer + upload failed: no file chooser or input[type=file].")


def fill_prompt(page):
    prompt_box, sel = find_prompt_box(page)

    print(f"Fill prompt: {sel}")
    prompt_box.click(force=True)
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")

    try:
        prompt_box.fill(TEST_PROMPT)
    except Exception:
        page.keyboard.insert_text(TEST_PROMPT)

    page.wait_for_timeout(1000)


def click_submit_button(page):
    prompt_box, prompt_sel = find_prompt_box(page)
    prompt_rect = prompt_box.bounding_box() or {}

    print("Click submit button near composer")

    candidates = page.locator("button, [role='button']")
    submit_button = None
    submit_label = ""

    for i in range(min(candidates.count(), 140)):
        try:
            btn = candidates.nth(i)
            if not btn.is_visible() or not btn.is_enabled():
                continue

            text = (btn.inner_text(timeout=500) or "").strip()
            aria = btn.get_attribute("aria-label") or ""
            label = f"{text} {aria}".strip()
            norm = label.lower()

            if any(x in norm for x in ["add", "add_2", "media", "upload", "attach", "agent", "nano banana", "imagen"]):
                continue

            if not any(x in norm for x in ["submit", "send", "generate", "create", "arrow_forward"]):
                continue

            box = btn.bounding_box() or {}
            if not box or not is_near_prompt(box, prompt_rect):
                continue

            submit_button = btn
            submit_label = label
            break

        except Exception:
            pass

    if submit_button:
        print(f"Click submit: {submit_label!r}")
        submit_button.click(force=True, timeout=10000)
        page.wait_for_timeout(3000)
        print("Submitted by button click.")
        return

    # Last-resort coordinate click on the right-side composer arrow button.
    x = prompt_rect["x"] + prompt_rect["width"] + 36
    y = prompt_rect["y"] + prompt_rect["height"] / 2

    print("Submit button selector not found; clicking right-side composer arrow fallback.")
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

    click_composer_plus_upload(page)
    fill_prompt(page)
    click_submit_button(page)

    time.sleep(3)
