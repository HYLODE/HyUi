"""
End-to-End testing for the Sitrep page
"""
import pytest
from playwright.sync_api import Page, expect

from config.settings import settings

# import pdb; pdb.set_trace()
SITREP_URL = f"{settings.APP_URL}/sitrep"


@pytest.mark.smoke
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
