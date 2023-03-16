"""
Use for slowly updating API calls that can be shared between pages and
applications
"""

import requests
import warnings
from dash import Input, Output, callback, dcc, html

from models.beds import Bed, Department, Room
from models.electives import MergedData
from models.sitrep import SitrepRow
from web import ids
from web.config import get_settings
from web.logger import logger, logger_timeit


# TODO: add a refresh button as an input to the store functions pulling from
#  baserow so that changes from baserow edits can be brought through (
#  although a page refresh may do the same thing?)


@callback(
    Output(ids.DEPT_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    background=True,
)
@logger_timeit()
def _store_departments(_: int) -> list[dict]:
    """Store all open departments"""
    response = requests.get(
        f"{get_settings().api_url}/baserow/departments/",
    )
    depts = [Department.parse_obj(row).dict() for row in response.json()]
    return [d for d in depts if not d.get("closed_perm_01")]


@callback(
    Output(ids.ROOM_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    background=True,
)
@logger_timeit()
def _store_rooms(_: int) -> list[dict]:
    """Store all rooms with beds"""
    response = requests.get(
        f"{get_settings().api_url}/baserow/rooms/",
    )
    rooms = [Room.parse_obj(row).dict() for row in response.json()]
    return [r for r in rooms if r.get("has_beds")]


@callback(
    Output(ids.BEDS_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    background=True,
)
@logger_timeit()
def _store_beds(_: int) -> list[dict]:
    logger.info("Collecting beds data on initial load")
    response = requests.get(
        f"{get_settings().api_url}/baserow/beds/",
    )
    return [Bed.parse_obj(row).dict() for row in response.json()]


@callback(
    Output(ids.ELECTIVES_STORE, "data"),
    Input(ids.STORE_TIMER_6H, "n_intervals"),
    background=True,
)
@logger_timeit()
def _store_electives(_: int) -> list[dict]:
    response = requests.get(
        f"{get_settings().api_url}/electives/",
    )
    return [MergedData.parse_obj(row).dict() for row in response.json()]


@callback(
    Output(ids.SITREP_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    background=True,
)
@logger_timeit()
def _store_all_sitreps(_: int) -> dict:
    """Return sitrep status for all critical care areas"""
    SITREP_DEPT2WARD_MAPPING: dict = {
        "UCH T03 INTENSIVE CARE": "T03",
        "UCH T06 SOUTH PACU": "T06",
        "GWB L01 CRITICAL CARE": "GWB",
        "WMS W01 CRITICAL CARE": "WMS",
        "NHNN C0 NCCU": "NHNNC0",
        "NHNN C1 NCCU": "NHNNC1",
    }
    icus = list(SITREP_DEPT2WARD_MAPPING.values())
    sitreps = {}
    for icu in icus:
        response = requests.get(f"{get_settings().api_url}/sitrep/live/{icu}/ui/")
        if response.status_code != 200:
            warnings.warn(f"Sitrep not available for {icu}")
            rows = []

        res = response.json()

        try:
            # assumes http://uclvlddpragae08:5201
            assert type(res) is list
            rows = res
        except AssertionError:
            warnings.warn(
                f"Sitrep endpoint at {get_settings().api_url} did not return list - "
                f"Retry list is keyed under 'data'"
            )
            # see https://github.com/HYLODE/HyUi/issues/179
            # where we switch to using http://172.16.149.202:5001/
            try:
                rows = res["data"]
            except KeyError as e:
                warnings.warn("No data returned for sitrep")
                print(repr(e))
                rows = []

        res = [SitrepRow.parse_obj(row).dict() for row in rows]
        sitreps[icu] = res

    return sitreps


web_stores = html.Div(
    [
        dcc.Store(id=ids.DEPT_STORE),
        dcc.Store(id=ids.ROOM_STORE),
        dcc.Store(id=ids.BEDS_STORE),
        dcc.Store(id=ids.ELECTIVES_STORE),
        dcc.Store(id=ids.SITREP_STORE),
    ]
)
