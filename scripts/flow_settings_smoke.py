import os
import re
from playwright.sync_api import sync_playwright

CDP_URL = os.getenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
FLOW_URL = os.getenv(
    "FLOW_URL",
    "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28",
)

FLOW_IMAGE_MODEL = os.getenv("FLOW_IMAGE_MODEL", "Nano Banana 2")
FLOW_ASPECT_RATIO = os.getenv("FLOW_ASPECT_RATIO", "9:16")
FLOW_OUTPUT_COUNT = os.getenv("FLOW_OUTPUT_COUNT", "1")


def open_flow_page(browser):
    for ctx in browser.contexts:
        for page in ctx.pages:
            if "labs.google/fx/tools/flow" in (page.url or ""):
                page.bring_to_front()
                return page

    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.new_page()
    page.goto(FLOW_URL, wait_until="domcontentloaded")
    page.bring_to_front()
    return page


def click_composer_settings_pill(page):
    for sel in [
        "button:has-text('Nano Banana')",
        "[role='button']:has-text('Nano Banana')",
        "button:has-text('Imagen')",
        "[role='button']:has-text('Imagen')",
        "button:has-text('1x')",
        "[role='button']:has-text('1x')",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                print(f"Click composer settings pill: {sel}")
                loc.click(force=True, timeout=10000)
                page.wait_for_timeout(1000)
                return
        except Exception:
            pass

    raise SystemExit("Composer settings/model pill not found.")


def open_menu(page):
    menu = page.locator("[data-radix-menu-content][data-state='open'], [role='menu'][data-state='open']").last
    if not menu.count() or not menu.is_visible():
        raise SystemExit("Open composer settings menu not found.")
    return menu


def norm(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def click_menu_button_containing(page, wanted, label):
    menu = open_menu(page)
    buttons = menu.locator("button, [role='tab'], [role='button'], [role='menuitem'], [role='option']")

    wanted_l = wanted.lower()

    for i in range(min(buttons.count(), 80)):
        try:
            btn = buttons.nth(i)
            if not btn.is_visible() or not btn.is_enabled():
                continue

            text = norm(btn.inner_text(timeout=500))
            if wanted_l not in text.lower():
                continue

            print(f"Click {label}: {text!r}")
            btn.click(force=True, timeout=10000)
            page.wait_for_timeout(700)
            return True

        except Exception:
            pass

    print(f"Not found: {label} -> {wanted!r}")
    return False


def select_image_mode(page):
    return click_menu_button_containing(page, "Image", "Image mode")


def select_aspect_ratio(page):
    return click_menu_button_containing(page, FLOW_ASPECT_RATIO, f"Aspect ratio {FLOW_ASPECT_RATIO}")


def select_quantity(page):
    # Flow labels are: 1x, x2, x3, x4
    count = str(FLOW_OUTPUT_COUNT).strip()
    label = "1x" if count == "1" else f"x{count}"
    return click_menu_button_containing(page, label, f"Quantity {label}")


def select_model(page):
    menu = open_menu(page)

    # The current model row is already a button in the same menu.
    model_button = None
    buttons = menu.locator("button, [role='button']")
    for i in range(min(buttons.count(), 80)):
        try:
            btn = buttons.nth(i)
            if not btn.is_visible() or not btn.is_enabled():
                continue
            text = norm(btn.inner_text(timeout=500))
            if "Nano Banana" in text or "Imagen" in text:
                model_button = btn
                if FLOW_IMAGE_MODEL.lower() in text.lower():
                    print(f"Model already selected: {text!r}")
                    return True
                print(f"Click model dropdown: {text!r}")
                btn.click(force=True, timeout=10000)
                page.wait_for_timeout(1000)
                break
        except Exception:
            pass

    if model_button is None:
        print("Model dropdown not found.")
        return False

    # After clicking, a nested Radix menu/list may open.
    for sel in [
        f"text={FLOW_IMAGE_MODEL}",
        f"button:has-text('{FLOW_IMAGE_MODEL}')",
        f"[role='menuitem']:has-text('{FLOW_IMAGE_MODEL}')",
        f"[role='option']:has-text('{FLOW_IMAGE_MODEL}')",
        f"[role='button']:has-text('{FLOW_IMAGE_MODEL}')",
    ]:
        try:
            loc = page.locator(sel).last
            if loc.count() and loc.is_visible():
                print(f"Click model option: {sel}")
                loc.click(force=True, timeout=10000)
                page.wait_for_timeout(800)
                return True
        except Exception:
            pass

    print(f"Model option not found: {FLOW_IMAGE_MODEL}")
    return False


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    page = open_flow_page(browser)

    page.wait_for_timeout(1500)
    print("Flow page:", page.url)

    click_composer_settings_pill(page)

    image_ok = select_image_mode(page)
    aspect_ok = select_aspect_ratio(page)
    quantity_ok = select_quantity(page)
    model_ok = select_model(page)

    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    print({
        "image_ok": image_ok,
        "aspect_ok": aspect_ok,
        "quantity_ok": quantity_ok,
        "model_ok": model_ok,
        "model": FLOW_IMAGE_MODEL,
        "aspect_ratio": FLOW_ASPECT_RATIO,
        "output_count": FLOW_OUTPUT_COUNT,
    })
