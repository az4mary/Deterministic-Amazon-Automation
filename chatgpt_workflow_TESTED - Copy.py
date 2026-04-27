from playwright.sync_api import sync_playwright
import time

GPT_URL = "https://chatgpt.com/g/g-B3hgivKK9-write-for-me"

PROMPT1 = "List the top 5 trending news topics in the United States today (March 11, 2026). Return only the topic titles as a numbered list."

PROMPT2 = "For each of the 5 topics above, write a concise 100-word summary explaining what happened and why it matters."

PROMPT3 = "Write an engaging social media article about the FIRST topic above. 150–200 words. Conversational tone with a strong hook and strong closing."


def send_prompt(page, prompt):

    print("Waiting for ChatGPT input box...")

    box = page.locator('[contenteditable="true"]').first
    box.wait_for(timeout=60000)

    box.click()

    print("Typing prompt...")
    box.type(prompt, delay=40)

    time.sleep(1)

    page.keyboard.press("Enter")

    print("Prompt sent")


with sync_playwright() as p:

    print("Connecting to Chrome...")

    browser = p.chromium.connect_over_cdp("http://localhost:9222")

    context = browser.contexts[0]

    page = context.new_page()

    print("Opening custom GPT...")

    page.goto(GPT_URL)

    time.sleep(12)

    print("Sending prompt 1...")
    send_prompt(page, PROMPT1)

    print("Waiting 5 minutes...")
    time.sleep(300)

    print("Sending prompt 2...")
    send_prompt(page, PROMPT2)

    print("Waiting 10 minutes...")
    time.sleep(600)

    print("Sending prompt 3...")
    send_prompt(page, PROMPT3)

    print("Workflow completed successfully")