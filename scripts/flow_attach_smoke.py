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

TARGET_IMAGE_NAME_HINTS = [
    "Dashcam_road_facing_view",
    "Dashcam_road_facing",
    "road_facing",
]

TEST_PROMPT = (
    "Test prompt: create a simple commercial product image of the dashcam "
    "using the attached reference image."
)

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
    click_first(
        page,
        [
            "text=Add Media",
            "button:has-text('Add Media')",
            "[role='button']:has-text('Add Media')",
            "[aria-label*='Add Media']",
            "button[aria-label*='Add']",
        ],
        "Add Media",
        wait_ms=1500,
    )

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

            fc.value.set_files(DASHCAM_IMAGES)
            print("Uploaded via file chooser.")
            page.wait_for_timeout(7000)
            return

        except PlaywrightTimeoutError:
            continue
        except Exception as exc:
            print(f"Upload selector skipped: {sel} | {str(exc)[:200]}")

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

    raise SystemExit("Upload failed: no file chooser or input[type=file] found.")


def open_uploaded_media(page):
    click_first(
        page,
        [
            "text=View uploaded media",
            "[aria-label*='View uploaded media']",
            "button:has-text('View uploaded media')",
            "[role='button']:has-text('View uploaded media')",
            "text=All Media",
            "button:has-text('All Media')",
            "[role='button']:has-text('All Media')",
        ],
        "Uploaded Media",
        wait_ms=2500,
    )


def get_card_text(card):
    try:
        return (card.inner_text(timeout=700) or "").strip()
    except Exception:
        return ""


def get_card_box(card):
    try:
        return card.bounding_box() or {}
    except Exception:
        return {}


def card_is_usable(card):
    try:
        if not card.is_visible():
            return False
        box = get_card_box(card)
        return box.get("width", 0) >= 100 and box.get("height", 0) >= 100
    except Exception:
        return False


def find_target_gallery_cards(page):
    cards = []

    target_selectors = []
    for hint in TARGET_IMAGE_NAME_HINTS:
        target_selectors.extend(
            [
                f"[role='button']:has-text('{hint}')",
                f"button:has-text('{hint}')",
                f"[data-testid*='asset']:has-text('{hint}')",
                f"[data-testid*='media']:has-text('{hint}')",
                f"main [role='button']:has-text('{hint}')",
                f"main div:has-text('{hint}')",
            ]
        )

    fallback_selectors = [
        "[role='button']:has(img)",
        "button:has(img)",
        "[data-testid*='asset']:has(img)",
        "[data-testid*='media']:has(img)",
        "main [role='button']:has(img)",
    ]

    for sel in target_selectors + fallback_selectors:
        try:
            locs = page.locator(sel)
            for i in range(min(locs.count(), 50)):
                card = locs.nth(i)
                if not card_is_usable(card):
                    continue

                text = get_card_text(card)
                box = get_card_box(card)
                cards.append((card, sel, i, text, box))
        except Exception:
            pass

    # Prefer road-facing filename/card; otherwise first usable large card.
    preferred = []
    fallback = []

    for item in cards:
        _card, _sel, _i, text, _box = item
        normalized = text.lower()
        if any(h.lower() in normalized for h in TARGET_IMAGE_NAME_HINTS):
            preferred.append(item)
        else:
            fallback.append(item)

    return preferred + fallback


def add_target_image_to_prompt(page):
    cards = find_target_gallery_cards(page)

    if not cards:
        raise SystemExit("No usable gallery cards found.")

    for card, sel, idx, text, box in cards:
        try:
            print(f"Hover gallery card only: {sel} [{idx}] | text={text[:80]!r}")

            # IMPORTANT: hover only. Do not click the image/card.
            card.hover(timeout=10000)
            page.wait_for_timeout(1200)

            menu_clicked = False

            # Prefer menu inside hovered card.
            for menu_sel in [
                "button[aria-label*='More']",
                "[role='button'][aria-label*='More']",
                "button[aria-label*='more']",
                "[role='button'][aria-label*='more']",
                "button:has-text('more_vert')",
                "[role='button']:has-text('more_vert')",
            ]:
                try:
                    menu = card.locator(menu_sel).last
                    if menu.count() and menu.is_visible():
                        print(f"Click hovered-card menu: {menu_sel}")
                        menu.click(force=True, timeout=10000)
                        menu_clicked = True
                        page.wait_for_timeout(1000)
                        break
                except Exception:
                    pass

            # Coordinate fallback: click the top-right 3-dot area only.
            if not menu_clicked:
                x = box["x"] + box["width"] - 28
                y = box["y"] + 28
                print("Click hovered-card top-right menu fallback")
                page.mouse.click(x, y)
                page.wait_for_timeout(1000)

            add_to_prompt, add_sel = first_visible(
                page,
                [
                    "text=Add to prompt",
                    "text=Add to Prompt",
                    "[role='menuitem']:has-text('Add to prompt')",
                    "[role='menuitem']:has-text('Add to Prompt')",
                    "button:has-text('Add to prompt')",
                    "button:has-text('Add to Prompt')",
                    "[role='button']:has-text('Add to prompt')",
                    "[role='button']:has-text('Add to Prompt')",
                ],
            )

            if add_to_prompt:
                print(f"Click Add to prompt: {add_sel}")
                add_to_prompt.click(force=True, timeout=10000)
                page.wait_for_timeout(3000)
                return True

            print("Add to prompt not visible after menu; trying next card.")
            page.keyboard.press("Escape")
            page.wait_for_timeout(700)

        except Exception as exc:
            print(f"Card skipped: {str(exc)[:250]}")
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except Exception:
                pass

    raise SystemExit("No Add to prompt action found from hovered gallery card.")


def fill_prompt(page):
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





def submit_prompt(page):
    print("Submit: locating composer-scoped generate/create control")

    # Prefer keyboard submit first because it targets the focused composer.
    try:
        page.keyboard.press("Control+Enter")
        page.wait_for_timeout(2500)
    except Exception:
        pass

    # If keyboard did not start generation, click only a button near the composer area.
    prompt_box, _ = first_visible(
        page,
        [
            "textarea",
            "[contenteditable='true']",
            "div[role='textbox']",
            "[role='textbox']",
        ],
    )

    prompt_box_rect = None
    if prompt_box:
        try:
            prompt_box_rect = prompt_box.bounding_box()
        except Exception:
            prompt_box_rect = None

    candidates = page.locator("button, [role='button']")
    best = None
    best_label = ""

    for i in range(min(candidates.count(), 80)):
        try:
            btn = candidates.nth(i)
            if not btn.is_visible() or not btn.is_enabled():
                continue

            text = (btn.inner_text(timeout=500) or "").strip()
            aria = btn.get_attribute("aria-label") or ""
            label = f"{text} {aria}".strip()

            # Avoid broad/global Create controls unless they are near the prompt box.
            if not any(word in label.lower() for word in ["generate", "create", "submit", "send"]):
                continue

            box = btn.bounding_box() or {}
            if not box:
                continue

            if prompt_box_rect:
                btn_cx = box["x"] + box["width"] / 2
                btn_cy = box["y"] + box["height"] / 2

                prompt_x1 = prompt_box_rect["x"] - 80
                prompt_x2 = prompt_box_rect["x"] + prompt_box_rect["width"] + 160
                prompt_y1 = prompt_box_rect["y"] - 120
                prompt_y2 = prompt_box_rect["y"] + prompt_box_rect["height"] + 160

                near_prompt = (
                    prompt_x1 <= btn_cx <= prompt_x2
                    and prompt_y1 <= btn_cy <= prompt_y2
                )

                if not near_prompt:
                    continue

            best = btn
            best_label = label
            break

        except Exception:
            pass

    if best:
        print(f"Click composer-scoped submit: {best_label!r}")
        best.click(force=True, timeout=10000)
        page.wait_for_timeout(3000)
        print("Submitted.")
        return

    # Final fallback: focused composer + Enter.
    print("No composer-scoped submit button found; pressing Enter")
    try:
        if prompt_box:
            prompt_box.click(force=True)
        page.keyboard.press("Enter")
        page.wait_for_timeout(3000)
        print("Submitted via Enter fallback.")
        return
    except Exception as exc:
        raise SystemExit(f"Submit failed: {exc}")






