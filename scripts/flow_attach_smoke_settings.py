def open_composer_settings(page):
    print("Open composer settings")

    prompt_box, _ = first_visible(
        page,
        [
            "textarea",
            "[contenteditable='true']",
            "div[role='textbox']",
            "[role='textbox']",
        ],
    )

    prompt_rect = None
    if prompt_box:
        try:
            prompt_rect = prompt_box.bounding_box()
        except Exception:
            prompt_rect = None

    # Prefer the exact composer pill shown in your screenshot.
    direct_selectors = [
        "button:has-text('Agent')",
        "[role='button']:has-text('Agent')",
        "button[aria-label*='Agent']",
        "[role='button'][aria-label*='Agent']",
    ]

    for sel in direct_selectors:
        try:
            locs = page.locator(sel)
            for i in range(min(locs.count(), 10)):
                btn = locs.nth(i)
                if not btn.is_visible() or not btn.is_enabled():
                    continue

                if prompt_rect:
                    box = btn.bounding_box() or {}
                    cx = box["x"] + box["width"] / 2
                    cy = box["y"] + box["height"] / 2

                    near_composer = (
                        prompt_rect["x"] - 120 <= cx <= prompt_rect["x"] + prompt_rect["width"] + 160
                        and prompt_rect["y"] - 160 <= cy <= prompt_rect["y"] + prompt_rect["height"] + 160
                    )

                    if not near_composer:
                        continue

                print(f"Click composer settings: {sel}")
                btn.click(force=True, timeout=10000)
                page.wait_for_timeout(1500)
                return True
        except Exception:
            pass

    # Fallback: click small button near the composer, but reject Add Media/+.
    controls = page.locator("button, [role='button']")
    for i in range(min(controls.count(), 120)):
        try:
            btn = controls.nth(i)
            if not btn.is_visible() or not btn.is_enabled():
                continue

            text = (btn.inner_text(timeout=500) or "").strip()
            aria = btn.get_attribute("aria-label") or ""
            label = f"{text} {aria}".strip().lower()

            if any(bad in label for bad in ["add media", "upload", "attach", "view settings", "more", "trash"]):
                continue

            if not any(good in label for good in ["agent", "settings", "model", "image", "video"]):
                continue

            box = btn.bounding_box() or {}
            if not box or not prompt_rect:
                continue

            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2

            near_composer = (
                prompt_rect["x"] - 120 <= cx <= prompt_rect["x"] + prompt_rect["width"] + 160
                and prompt_rect["y"] - 160 <= cy <= prompt_rect["y"] + prompt_rect["height"] + 160
            )

            if not near_composer:
                continue

            print(f"Click composer settings fallback: {text or aria}")
            btn.click(force=True, timeout=10000)
            page.wait_for_timeout(1500)
            return True

        except Exception:
            pass

    print("Composer settings button not found.")
    return False


def select_image_mode(page):
    print("Selecting Image mode")

    for sel in [
        "button:has-text('Image')",
        "[role='button']:has-text('Image')",
        "[role='tab']:has-text('Image')",
        "text=Image",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                print(f"Click Image mode: {sel}")
                loc.click(force=True, timeout=10000)
                page.wait_for_timeout(800)
                return True
        except Exception:
            pass

    print("Image mode not confirmed.")
    return False


def select_aspect_ratio(page):
    print(f"Selecting aspect ratio: {FLOW_ASPECT_RATIO}")

    for sel in [
        f"button:has-text('{FLOW_ASPECT_RATIO}')",
        f"[role='button']:has-text('{FLOW_ASPECT_RATIO}')",
        f"[role='option']:has-text('{FLOW_ASPECT_RATIO}')",
        f"text={FLOW_ASPECT_RATIO}",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                print(f"Click aspect ratio: {sel}")
                loc.click(force=True, timeout=10000)
                page.wait_for_timeout(800)
                return True
        except Exception:
            pass

    print(f"Aspect ratio not confirmed: {FLOW_ASPECT_RATIO}")
    return False


def select_model(page):
    print(f"Selecting model: {FLOW_IMAGE_MODEL}")

    # Open model dropdown from the settings popover.
    for sel in [
        "button:has-text('Nano Banana')",
        "[role='button']:has-text('Nano Banana')",
        "button:has-text('Imagen')",
        "[role='button']:has-text('Imagen')",
        "button[aria-haspopup='listbox']",
        "[role='button'][aria-haspopup='listbox']",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                print(f"Click model dropdown: {sel}")
                loc.click(force=True, timeout=10000)
                page.wait_for_timeout(1000)
                break
        except Exception:
            pass

    for sel in [
        f"button:has-text('{FLOW_IMAGE_MODEL}')",
        f"[role='button']:has-text('{FLOW_IMAGE_MODEL}')",
        f"[role='option']:has-text('{FLOW_IMAGE_MODEL}')",
        f"text={FLOW_IMAGE_MODEL}",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                print(f"Click model option: {sel}")
                loc.click(force=True, timeout=10000)
                page.wait_for_timeout(1000)
                return True
        except Exception:
            pass

    print(f"Model not confirmed: {FLOW_IMAGE_MODEL}")
    return False


def set_flow_generation_settings(page):
    print("Setting Flow generation settings from composer settings")

    opened = open_composer_settings(page)
    if not opened:
        return False, False

    image_ok = select_image_mode(page)
    aspect_ok = select_aspect_ratio(page)
    model_ok = select_model(page)

    page.keyboard.press("Escape")
    page.wait_for_timeout(700)

    print(f"Settings result: image_ok={image_ok}, model_ok={model_ok}, aspect_ok={aspect_ok}")
    return model_ok, aspect_ok
