from datetime import datetime

from dash import Input, Output, callback
from web.celery_tasks import requests_try_cache

from models.census import CensusRow
from web import SITREP_DEPT2WARD_MAPPING
from web.config import get_settings
from web.logger import logger_timeit
from web.pages.sitrep import CAMPUSES, ids


@callback(
    Output(ids.CENSUS_STORE, "data"),
    Input(ids.DEPT_GROUPER, "value"),
    Input(ids.DEPTS_OPEN_STORE_NAMES, "data"),
)
@logger_timeit(level="DEBUG")
def _store_census(
    dept_grouper: str,
    depts_open_names: list[str],
) -> list[dict]:
    """
    Store CensusRow as list of dictionaries after filtering out closed
    departments for that building
    Args:
        dept_grouper: one of UCH/WMS/GWB/NHNN
        depts_open_names: list of departments that are open

    Returns:
        Filtered list of CensusRow dictionaries

    """
    if dept_grouper == "ALL_ICUS":
        url = f"{get_settings().api_url}/census/"
        params = {"departments": SITREP_DEPT2WARD_MAPPING.keys()}
        data = requests_try_cache(url, params=params)
    else:
        campus_short_name = next(
            i.get("label") for i in CAMPUSES if i.get("value") == dept_grouper
        )
        url = f"{get_settings().api_url}/census/campus/"
        params = {"campuses": campus_short_name}  # type: ignore
        data = requests_try_cache(url, params=params)

    res = [CensusRow.parse_obj(row).dict() for row in data]
    # filter out closed departments
    res = [row for row in res if row.get("department") in depts_open_names]
    return res


def format_census(census: dict) -> dict:
    """Given a census object return a suitably formatted dictionary"""
    mrn = census.get("mrn", "")
    encounter = str(census.get("encounter", ""))
    lastname = census.get("lastname", "").upper()
    firstname = census.get("firstname", "").title()
    initials = (
        f"{census.get('firstname', '?')[0]}"
        f""
        f""
        f""
        f"{census.get('lastname', '?')[0]}"
    )
    date_of_birth = census.get("date_of_birth", "1900-01-01")  # default dob
    dob = datetime.fromisoformat(date_of_birth)
    dob_fshort = datetime.strftime(dob, "%d-%m-%Y")
    dob_flong = datetime.strftime(dob, "%d %b %Y")
    age = int((datetime.utcnow() - dob).days / 365.25)
    sex = census.get("sex")
    if sex is None:
        sex = ""
    else:
        sex = "M" if sex.lower() == "m" else "F"

    return dict(
        mrn=mrn,
        encounter=encounter,
        lastname=lastname,
        firstname=firstname,
        initials=initials,
        dob=dob,
        dob_fshort=dob_fshort,
        dob_flong=dob_flong,
        age=age,
        sex=sex,
        demographic_slug=f"{firstname} {lastname} | {age}{sex} | MRN {mrn}",
    )
