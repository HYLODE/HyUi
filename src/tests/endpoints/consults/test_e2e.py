"""
End-to-End testing for the Consults page
"""
import os
import pytest
from playwright.sync_api import Page, expect

if os.getenv("DOCKER", "False") == "True":
    CONSULTS_URL = "http://apps:8095/consults"
else:
    # Assume no docker at all so using local dev
    CONSULTS_URL = "http://localhost:8093/consults"


@pytest.mark.smoke
def test_consults_page_loads(page: Page):
    page.goto(CONSULTS_URL, timeout=30 * 1000)
    expect(page).to_have_title("HyUi", timeout=5000)
    expect(page).to_have_url(CONSULTS_URL, timeout=5000)
