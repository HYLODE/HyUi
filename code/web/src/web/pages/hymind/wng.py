"""
Wrangling
"""
from web.pages.hymind import HYMIND_ENV
from config.settings import settings


def build_emergency_tap_url(env: str = None) -> str:
    """Construct API based on environment and requested ward"""

    # over-ride sitrep maturity if working in dev environment
    if settings.ENV == "dev":
        env = settings.ENV
    else:
        env = HYMIND_ENV

    if env == "prod":
        raise NotImplementedError
        # API_PORT = "5006"
        # url = f"{settings.BASE_URL_PROD}:{API_PORT}/live/icu/{ward}/ui"
    elif env == "test":
        # http://uclvlddpragae08:5230/predict/
        url = "http://uclvlddpragae08:5230/predict/"
    elif env == "dev":
        url = f"{settings.API_URL}/hymind/icu/tap/emergency"
    else:
        raise ValueError

    return url


def build_elective_tap_url(env: str = None) -> str:
    """Construct API based on environment and requested ward"""

    # over-ride sitrep maturity if working in dev environment
    if settings.ENV == "dev":
        env = settings.ENV
    else:
        env = HYMIND_ENV

    if env == "prod":
        raise NotImplementedError
        # API_PORT = "5006"
        # url = f"{settings.BASE_URL_PROD}:{API_PORT}/live/icu/{ward}/ui"
    elif env == "test":
        # http://uclvlddpragae08:5219/predict/
        url = "http://uclvlddpragae08:5219/predict/"
    elif env == "dev":
        url = f"{settings.API_URL}/hymind/icu/tap/electives"
    else:
        raise ValueError

    return url
