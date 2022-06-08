from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()

    # Open new page
    page = context.new_page()

    # Go to http://127.0.0.1:8093/
    page.goto("http://127.0.0.1:8093/")

    # Click text=CONSULTS
    page.locator("text=CONSULTS").click()
    # expect(page).to_have_url("http://127.0.0.1:8093/consults")

    # Click text=Select...
    page.locator("text=Select...").click()

    # Click text=GWB L02 NORTH (L02N)
    page.locator("text=GWB L02 NORTH (L02N)").click()
    page.screenshot(path="example.png")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
