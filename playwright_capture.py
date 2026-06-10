from playwright.sync_api import sync_playwright
import os

OUTPUT_DIR = "playwright_dump"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto(
        "http://localhost:8501",
        wait_until="networkidle"
    )

    page.wait_for_timeout(5000)

    html = page.content()

    with open(
        f"{OUTPUT_DIR}/page.html",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(html)

    page.screenshot(
        path=f"{OUTPUT_DIR}/screen.png",
        full_page=True
    )

    print("저장 완료")

    browser.close()