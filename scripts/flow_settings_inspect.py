import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP_URL = os.getenv("BROWSER_CDP_URL", "http://127.0.0.1:9222")
FLOW_URL = os.getenv(
    "FLOW_URL",
    "https://labs.google/fx/tools/flow/project/7b90caae-5286-48de-85d2-f7e5b112ee28",
)

OUT_DIR = Path("output/flow_inspect")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def first_visible(page, selectors):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                return loc, sel
        except Exception:
            pass
    return None, None


def open_settings_popover(page):
    loc, sel = first_visible(
        page,
        [
            "button:has-text('Nano Banana')",
            "[role='button']:has-text('Nano Banana')",
            "button:has-text('Imagen')",
            "[role='button']:has-text('Imagen')",
            "button:has-text('1x')",
            "[role='button']:has-text('1x')",
        ],
    )

    if not loc:
        raise SystemExit("Composer model/settings pill not found.")

    print(f"Click settings pill: {sel}")
    loc.click(force=True, timeout=10000)
    page.wait_for_timeout(1500)


def inspect_open_popover(page):
    result = page.evaluate(
        """
        () => {
          const roots = Array.from(document.querySelectorAll(
            '[data-radix-popper-content-wrapper], [data-radix-menu-content], [role="menu"], [role="dialog"], [role="listbox"]'
          ));

          const visible = (el) => {
            const r = el.getBoundingClientRect();
            const s = window.getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
          };

          const cssPath = (el) => {
            if (!el || !el.tagName) return '';
            const parts = [];
            let node = el;
            while (node && node.nodeType === 1 && parts.length < 6) {
              let part = node.tagName.toLowerCase();
              if (node.id) {
                part += '#' + CSS.escape(node.id);
                parts.unshift(part);
                break;
              }
              const role = node.getAttribute('role');
              const aria = node.getAttribute('aria-label');
              if (role) part += `[role="${role}"]`;
              if (aria) part += `[aria-label="${aria.replace(/"/g, '\\\\\\"')}"]`;
              const parent = node.parentElement;
              if (parent) {
                const same = Array.from(parent.children).filter(x => x.tagName === node.tagName);
                if (same.length > 1) {
                  part += `:nth-of-type(${same.indexOf(node) + 1})`;
                }
              }
              parts.unshift(part);
              node = parent;
            }
            return parts.join(' > ');
          };

          const output = [];

          roots.forEach((root, rootIndex) => {
            if (!visible(root)) return;

            const candidates = Array.from(root.querySelectorAll(
              'button, [role="button"], [role="option"], [role="menuitem"], [role="radio"], [role="tab"], [aria-label], div, span'
            ));

            candidates.forEach((el, index) => {
              if (!visible(el)) return;

              const r = el.getBoundingClientRect();
              const text = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
              const aria = el.getAttribute('aria-label') || '';
              const role = el.getAttribute('role') || '';
              const selected = el.getAttribute('aria-selected') || '';
              const checked = el.getAttribute('aria-checked') || '';
              const pressed = el.getAttribute('aria-pressed') || '';
              const disabled = el.getAttribute('aria-disabled') || el.getAttribute('disabled') || '';

              if (!text && !aria && !role) return;

              output.push({
                rootIndex,
                index,
                tag: el.tagName.toLowerCase(),
                role,
                text,
                aria,
                selected,
                checked,
                pressed,
                disabled,
                rect: {
                  x: Math.round(r.x),
                  y: Math.round(r.y),
                  width: Math.round(r.width),
                  height: Math.round(r.height)
                },
                cssPath: cssPath(el),
                outerHTML: el.outerHTML.slice(0, 700)
              });
            });
          });

          return output;
        }
        """
    )

    html = page.evaluate(
        """
        () => Array.from(document.querySelectorAll(
          '[data-radix-popper-content-wrapper], [data-radix-menu-content], [role="menu"], [role="dialog"], [role="listbox"]'
        ))
        .map((el, i) => `<!-- ROOT ${i} -->\\n` + el.outerHTML)
        .join('\\n\\n')
        """
    )

    json_path = OUT_DIR / "flow_settings_elements.json"
    html_path = OUT_DIR / "flow_settings_popover.html"
    screenshot_path = OUT_DIR / "flow_settings_popover.png"

    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    page.screenshot(path=str(screenshot_path), full_page=True)

    print(f"\nSaved JSON: {json_path}")
    print(f"Saved HTML: {html_path}")
    print(f"Saved screenshot: {screenshot_path}")

    print("\nVisible popover candidates:")
    for item in result:
        label = item["text"] or item["aria"] or item["role"]
        print(
            f"[{item['index']}] "
            f"tag={item['tag']} role={item['role']!r} "
            f"text={label!r} "
            f"rect={item['rect']} "
            f"selected={item['selected']!r} checked={item['checked']!r}"
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

    open_settings_popover(page)
    inspect_open_popover(page)
