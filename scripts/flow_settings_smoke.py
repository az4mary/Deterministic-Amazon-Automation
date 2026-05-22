import os
from playwright.sync_api import sync_playwright

CDP_URL = os.getenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
FLOW_URL = os.getenv(
    "FLOW_URL",
    "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28",
)

FLOW_IMAGE_MODEL = os.getenv("FLOW_IMAGE_MODEL", "Nano Banana 2")
FLOW_ASPECT_RATIO = os.getenv("FLOW_ASPECT_RATIO", "9:16")
FLOW_OUTPUT_COUNT = os.getenv("FLOW_OUTPUT_COUNT", "1")  # 1, 2, 3, or 4


def first_visible(page, selectors):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                return loc, sel
        except Exception:
            pass
    return None, None


def click_first(page, selectors, label, wait_ms=800):
    loc, sel = first_visible(page, selectors)
    if not loc:
        print(f"Not found: {label}")
        return False

    print(f"Click {label}: {sel}")
    loc.click(force=True, timeout=10000)
    page.wait_for_timeout(wait_ms)
    return True


def open_composer_settings(page):
    return click_first(
        page,
        [
            "button:has-text('Agent')",
            "[role='button']:has-text('Agent')",
            "button[aria-label*='Agent']",
            "[role='button'][aria-label*='Agent']",
        ],
        "Composer Agent/settings",
        wait_ms=1200,
    )


def select_image_mode(page):
    return click_first(
        page,
        [
            "button:has-text('Image')",
            "[role='button']:has-text('Image')",
            "[role='tab']:has-text('Image')",
            "text=Image",
        ],
        "Image mode",
    )


def select_aspect_ratio(page):
    return click_first(
        page,
        [
            f"button:has-text('{FLOW_ASPECT_RATIO}')",
            f"[role='button']:has-text('{FLOW_ASPECT_RATIO}')",
            f"[role='option']:has-text('{FLOW_ASPECT_RATIO}')",
            f"text={FLOW_ASPECT_RATIO}",
        ],
        f"Aspect ratio {FLOW_ASPECT_RATIO}",
    )


def select_quantity(page):
    value = f"{FLOW_OUTPUT_COUNT}x"
    return click_first(
        page,
        [
            f"button:has-text('{value}')",
            f"[role='button']:has-text('{value}')",
            f"[role='option']:has-text('{value}')",
            f"text={value}",
        ],
        f"Quantity {value}",
    )


def select_model(page):
    # Open model dropdown if current model/pro model row is visible.
    click_first(
        page,
        [
            "button:has-text('Nano Banana')",
            "[role='button']:has-text('Nano Banana')",
            "button:has-text('Imagen')",
            "[role='button']:has-text('Imagen')",
            "button[aria-haspopup='listbox']",
            "[role='button'][aria-haspopup='listbox']",
        ],
        "Model dropdown",
        wait_ms=1000,
    )

    return click_first(
        page,
        [
            f"button:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='button']:has-text('{FLOW_IMAGE_MODEL}')",
            f"[role='option']:has-text('{FLOW_IMAGE_MODEL}')",
            f"text={FLOW_IMAGE_MODEL}",
        ],
        f"Model {FLOW_IMAGE_MODEL}",
        wait_ms=1200,
    )


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

    opened = open_composer_settings(page)
    if not opened:
        raise SystemExit("Composer Agent/settings button not found.")

    image_ok = select_image_mode(page)
    aspect_ok = select_aspect_ratio(page)
    quantity_ok = select_quantity(page)
    model_ok = select_model(page)

    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    print(
        {
            "image_ok": image_ok,
            "aspect_ok": aspect_ok,
            "quantity_ok": quantity_ok,
            "model_ok": model_ok,
            "model": FLOW_IMAGE_MODEL,
            "aspect_ratio": FLOW_ASPECT_RATIO,
            "output_count": FLOW_OUTPUT_COUNT,
        }
    )
