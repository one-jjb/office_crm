from playwright.sync_api import sync_playwright
import os
import re

os.makedirs("capture", exist_ok=True)

BASE_URL = "http://localhost:8501"

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page(
        viewport={
            "width": 1920,
            "height": 1080
        }
    )

    print("로그인 페이지 접속")

    page.goto(
        BASE_URL,
        wait_until="networkidle"
    )

    page.wait_for_timeout(2000)

    print("로그인 시도")

    page.locator(
        'input[aria-label="아이디"]'
    ).fill("admin")

    page.locator(
        'input[aria-label="비밀번호"]'
    ).fill("1234")

    page.locator(
        'button[data-testid="stBaseButton-secondaryFormSubmit"]'
    ).click()

    page.wait_for_timeout(5000)

    print("로그인 완료")

    links = page.locator(
        'a[data-testid="stSidebarNavLink"]'
    )

    menu_urls = []

    for i in range(links.count()):

        href = links.nth(i).get_attribute("href")

        if href:
            menu_urls.append(href)

    print("\n===== 메뉴 목록 =====")

    for url in menu_urls:
        print(url)

    print("====================\n")

    for url in menu_urls:

        try:

            print(f"수집 시작 : {url}")

            page.goto(
                url,
                wait_until="networkidle",
                timeout=60000
            )

            page.wait_for_timeout(3000)

            name = url.split("/")[-1]

            if not name:
                name = "app"

            name = re.sub(
                r'[\\/:*?"<>|]',
                "_",
                name
            )

            page.screenshot(
                path=f"capture/{name}.png",
                full_page=True
            )

            with open(
                f"capture/{name}.html",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(page.content())

            print(f"완료 : {name}")

        except Exception as e:

            print(
                f"실패 : {url}"
            )

            print(e)

    print("\n모든 페이지 수집 완료")

    input(
        "\n엔터 누르면 종료"
    )

    browser.close()