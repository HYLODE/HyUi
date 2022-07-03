import os
import pytest
from playwright.sync_api import Page, expect

# Designed only to run effectively _within_ docker
# will fail if run from the command line with pytest
if os.getenv("DOCKER", "False") == "True":
    HOMEPAGE_URL = "http://apps:8095/"
else:
    # Assume no docker at all so using local dev
    HOMEPAGE_URL = "http://localhost:8093/"


@pytest.mark.e2e
def test_app_exists(page: Page):
    page.goto(HOMEPAGE_URL)
    assert page.title() == "HYLODE"
    # Now click and go 'no where'
    page.locator('a:has-text("Home")').click()
    assert page.url == HOMEPAGE_URL
    # use inspector tools and copy as selector to define the locator
    # assert (
    #     page.locator(
    #         "#page-content > div > div:nth-child(1) > div > div > nav > div > a"
    #     ).inner_text(timeout=5000)
    #     == "UCLH Critical Care Sitrep"
    # )
    # css selector
    assert page.locator(".navbar-brand").inner_text(timeout=5000) == "HYLODE"
    # css and text selector
    # assert (
    #     page.locator(".navbar-brand :text('Sitrep')").inner_text(timeout=5000)
    #     == "UCLH Critical Care Sitrep"
    # )

    # page.locator('a:has-text("UCLH Critical Care Sitrep")').click()
    # expect(page).to_have_url(HOMEPAGE_URL)
