# src/apps/pages/sitrep/wng.py
# wrangling and other functions for the sitrep page
# just so the logic in the main page is clearer
from apps.pages.sitrep import SITREP_ENV
from config.settings import settings


def build_sitrep_url(ward: str = None, env: str = None) -> str:
    """Construct API based on environment and requested ward"""

    ward = ward.upper() if ward else "TO3"

    # over-ride sitrep maturity if working in dev environment
    if settings.ENV == "dev":
        env = settings.ENV
    else:
        env = SITREP_ENV

    if env == "prod":
        API_PORT = "5006"
        SITREP_URL = f"{settings.BASE_URL_PROD}:{API_PORT}/live/icu/{ward}/ui"
    elif env == "test":
        API_PORT = "5207"
        SITREP_URL = f"{settings.BASE_URL_TEST}:{API_PORT}/live/icu/{ward}/ui"
    elif env == "dev":
        SITREP_URL = f"{settings.API_URL}/sitrep/"
    else:
        raise ValueError

    return SITREP_URL


def build_hymind_icu_discharge_url(ward: str = None, env: str = None) -> str:
    """
    Construct API based on environment and requested ward
    e.g.
    prod
    http://uclvlddpragae07:5007/predictions/icu/discharge?ward=T03
    test
    http://uclvlddpragae08:5907/predictions/icu/discharge?ward=T03 
    """

    ward = ward.upper() if ward else "TO3"

    # over-ride sitrep maturity if working in dev environment
    if settings.ENV == "dev":
        env = settings.ENV
    else:
        env = SITREP_ENV

    if env == "prod":
        API_PORT = "5007"
        HYMIND_URL = f"{settings.BASE_URL_PROD}:{API_PORT}/icu/discharge"
    elif env == "test":
        API_PORT = "5907"
        HYMIND_URL = f"{settings.BASE_URL_TEST}:{API_PORT}/icu/discharge"
    elif env == "dev":
        HYMIND_URL = f"{settings.API_URL}/hymind/icu/discharge"
    else:
        raise ValueError

    return HYMIND_URL
