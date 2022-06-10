"""
End-to-End testing for the Consults page
"""
import pytest
from playwright.sync_api import Page, expect

from config.settings import settings

# import pdb; pdb.set_trace()
CONSULTS_URL = f"{settings.APP_URL}/consults"


@pytest.mark.smoke
def test_consults_page_loads(page: Page):
    page.goto(CONSULTS_URL, timeout=5000)
    expect(page).to_have_title("HyUi", timeout=5000)
    expect(page).to_have_url(CONSULTS_URL, timeout=5000)
