"""
End-to-End testing for the Sitrep page
"""
import os
import pytest
from playwright.sync_api import Page, expect

if os.getenv("DOCKER", "False") == "True":
    SITREP_URL = "http://apps:8095/sitrep/sitrep"
else:
    # Assume no docker at all so using local dev
    SITREP_URL = "http://localhost:8093/sitrep/sitrep"


@pytest.mark.e2e
def test_sitrep_page_loads(page: Page):
    page.goto(SITREP_URL, timeout=5000)
    expect(page).to_have_title("Sitrep", timeout=5000)
    expect(page).to_have_url(SITREP_URL, timeout=5000)


@pytest.mark.e2e
def test_sitrep_page_has_content(page: Page):
    page.goto(SITREP_URL, timeout=5000)
    expect(page.locator("#sit_fancy_table")).to_be_visible(timeout=2000)
    loc = page.locator('[id="_pages_content"]')
    expect(loc).to_contain_text("Sitrep details", timeout=2000)
