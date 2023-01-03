"""
Module to manage the initial load of data to the page
Callbacks that run requests to HyUi API only and STORE information on page
Exposes
- store_beds : dcc.Store of bed status
- store_census
- store_sitrep
"""
import requests
import warnings
from dash import Input, Output, callback, dcc

from models.beds import Bed
from models.census import CensusRow
from models.sitrep import SitrepRow
from web.config import get_settings
from . import BPID, SITREP_DEPT2WARD_MAPPING

from web.pages.abacus.dept import input_active_dept

store_beds = dcc.Store(id=f"{BPID}beds")
input_beds_data = Input(f"{BPID}beds", "data")

store_census = dcc.Store(id=f"{BPID}census")
input_census_data = Input(f"{BPID}census", "data")

store_sitrep = dcc.Store(id=f"{BPID}sitrep")
input_sitrep_data = Input(f"{BPID}sitrep", "data")


@callback(
    Output(f"{BPID}beds", "data"),
    input_active_dept,
    background=True,
)
def _store_beds(department: str) -> list[dict]:
    response = requests.get(
        f"{get_settings().api_url}/beds/", params={"department": department}
    )
    return [Bed.parse_obj(row).dict() for row in response.json()]


@callback(
    Output(f"{BPID}census", "data"),
    input_active_dept,
    background=True,
)
def _store_census(department: str) -> list[dict]:
    departments = [department]  # expects a list
    response = requests.get(
        f"{get_settings().api_url}/census/", params={"departments": departments}
    )
    return [CensusRow.parse_obj(row).dict() for row in response.json()]


@callback(
    Output(f"{BPID}sitrep", "data"),
    input_active_dept,
    prevent_initial_callback=True,
    background=True,
)
def _store_sitrep(department: str) -> list[dict]:
    """
    Use census to provide the CSNs that can be used to query additional data
    Args:
        department: the department

    Returns:
        additonal patient level data

    """
    department = SITREP_DEPT2WARD_MAPPING.get(department)
    if not department:
        warnings.warn(f"No sitrep data available for {department}")
        return [{}]

    # FIXME 2022-12-20 hack to keep this working whilst waiting on
    covid_sitrep = True

    if covid_sitrep:
        warnings.warn("Working from old hycastle sitrep", category=DeprecationWarning)
        if "mock" in str(get_settings().api_url):
            mock = True
            url = f"{get_settings().api_url}/sitrep/live/{department}/ui"
        else:
            mock = False
            url = f"http://uclvlddpragae07:5006/live/icu/{department}/ui"
    else:
        url = f"{get_settings().api_url}/sitrep/live/{department}/ui"

    response = requests.get(url).json()
    rows = response["data"] if covid_sitrep and not mock else response
    return [SitrepRow.parse_obj(row).dict() for row in rows]
