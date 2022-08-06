# src/apps/pages/sitrep/wng.py
# wrangling and other functions for the sitrep page
# just so the logic in the main page is clearer
from config.settings import settings

# NB: the order of this list determines the order of the table
def build_sitrep_url(ward: str = None) -> str:
    """Construct API based on environment and requested ward"""
    if settings.ENV == "prod":
        ward = ward.upper() if ward else "TO3"
        API_URL = f"{settings.BASE_URL}:5006/live/icu/{ward}/ui"
    else:
        API_URL = f"{settings.API_URL}/sitrep/"
    return API_URL
