from playwright.sync_api import Page, expect
from config.settings import settings

HOMEPAGE_URL = f"{settings.APP_URL}/"


def test_app_exists(page: Page):
    page.goto(HOMEPAGE_URL)
    assert page.title() == "HyUi"
    # Now click and go 'no where'
    page.locator('a:has-text("UCLH Critical Care Sitrep")').click()
    assert page.url == HOMEPAGE_URL
    # use inspector tools and copy as selector to define the locator
    assert (
        page.locator(
            "#page-content > div > div:nth-child(1) > div > div > nav > div > a"
        ).inner_text(timeout=1000)
        == "UCLH Critical Care Sitrep"
    )
    # css selector
    assert (
        page.locator(".navbar-brand").inner_text(timeout=1000)
        == "UCLH Critical Care Sitrep"
    )
    # css and text selector
    # assert (
    #     page.locator(".navbar-brand :text('Sitrep')").inner_text(timeout=5000)
    #     == "UCLH Critical Care Sitrep"
    # )

    page.locator('a:has-text("UCLH Critical Care Sitrep")').click()
    expect(page).to_have_url(HOMEPAGE_URL)
