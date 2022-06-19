"""
End-to-End testing for the Sitrep page
"""
import os
import pytest
from playwright.sync_api import Page, expect

if os.getenv("DOCKER", "False") == "True":
    SITREP_URL = "http://apps:8095/sitrep"
else:
    # Assume no docker at all so using local dev
    SITREP_URL = "http://localhost:8093/sitrep"


@pytest.mark.e2e
def test_sitrep_page_loads(page: Page):
    page.goto(SITREP_URL, timeout=5000)
    expect(page).to_have_title("HyUi", timeout=5000)
    expect(page).to_have_url(SITREP_URL, timeout=5000)
    # once the page loads then check that it has the correct title
    assert (
        page.locator(
            "#page-content > div > div:nth-child(1) > div > div.card-header"
        ).inner_text(timeout=5000)
        == "Sitrep details"
    )
