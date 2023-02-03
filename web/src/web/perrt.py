from datetime import datetime

import requests

from models.perrt import EmapConsults, EmapCpr, EmapVitalsWide
from web.config import get_settings


def get_cpr_status(encounter_ids: list[str]) -> list[EmapCpr]:
    """
    get cpr status for encounters provided
    :param encounter_ids:
    :return:
    """
    response = requests.get(
        f"{get_settings().api_url}/perrt/cpr", params={"encounter_ids": encounter_ids}
    )
    return [EmapCpr.parse_obj(row) for row in response.json()]


def get_perrt_consults(
    encounter_ids: list[str], horizon_dt: datetime
) -> list[EmapConsults]:
    """
    get cpr status for encounters provided
    :param horizon_dt:
    :param encounter_ids:
    :return:
    """
    response = requests.get(
        f"{get_settings().api_url}/perrt/consults",
        params={"encounter_ids": encounter_ids, "horizon_dt": horizon_dt},
    )
    return [EmapConsults.parse_obj(row) for row in response.json()]


def get_perrt_wide(
    encounter_ids: list[str], horizon_dt: datetime
) -> list[EmapVitalsWide]:
    """
    get news scores
    :param horizon_dt:
    :param encounter_ids:
    :return:
    """
    response = requests.get(
        f"{get_settings().api_url}/perrt/vitals/wide",
        params={"encounter_ids": encounter_ids, "horizon_dt": horizon_dt},
    )
    return [EmapVitalsWide.parse_obj(row) for row in response.json()]