from playwright.sync_api import Page, expect


def test_app_exists(page: Page):
    page.goto("http://127.0.0.1:8093/")
    assert page.title() == "HyUi"
    # Now click and go 'no where'
    page.locator('a:has-text("UCLH Critical Care Sitrep")').click()
    assert page.url == "http://127.0.0.1:8093/"
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
    assert (
        page.locator(".navbar :text('Sitrep')").inner_text(timeout=1000)
        == "UCLH Critical Care Sitrep"
    )

    page.locator('a:has-text("UCLH Critical Care Sitrep")').click()
    expect(page).to_have_url("http://127.0.0.1:8093_XXX/")
