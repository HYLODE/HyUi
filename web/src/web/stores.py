"""
Use for slowly updating API calls that can be shared between pages and
applications
"""

import requests
import warnings
from dash import Input, Output, callback, dcc, html

import pandas as pd

# from web import SITREP_DEPT2WARD_MAPPING

from models.beds import Bed, Department, Room
from models.electives import MergedData
from models.sitrep import SitrepRow, Abacus
from web import ids
from web.config import get_settings
from web.convert import parse_to_data_frame

from datetime import date, timedelta

import numpy as np


# TODO: add a refresh button as an input to the store functions pulling from
#  baserow so that changes from baserow edits can be brought through (
#  although a page refresh may do the same thing?)


@callback(
    Output(ids.DEPT_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
    background=True,
)
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
def _store_beds(_: int) -> list[dict]:
    response = requests.get(
        f"{get_settings().api_url}/baserow/beds/",
    )
    return [Bed.parse_obj(row).dict() for row in response.json()]


@callback(
    Output(ids.ELECTIVES_STORE, "data"),
    Input(ids.STORE_TIMER_6H, "n_intervals"),
    background=True,
)
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


@callback(
    Output(ids.ABACUS_STORE, "data"),
    Input(ids.STORE_TIMER_6H, "n_intervals"),
    Input(ids.SITREP_STORE, "data"),
    background=True,
)
def _store_all_abacus(_: int, sitrep_store: dict) -> list[dict]:
    if get_settings().api_url.split("/")[-1] == "mock":
        num_beds = 24
        num_days = 7
        p, d, c = [], [], []
        for campus in ["UCH", "GWB", "WMS", "NHNN"]:
            for i in range(num_days):
                histogram, _ = np.histogram(np.random.randn(num_beds), bins=num_beds)
                probs = np.divide(np.flip(np.cumsum(histogram)), num_beds)
                probs[: np.random.randint(5, 15)] = 1
                p.append(probs.tolist())
                d.append((date.today() + timedelta(days=i)).strftime("%Y-%m-%d"))
                c.append(campus)
        return [
            Abacus.parse_obj(row).dict()
            for row in pd.DataFrame(
                columns=["campus", "date", "probabilities"], data=zip(c, d, p)
            ).to_dict(orient="records")
        ]
        #  I'm not sure why this stopped working...
        #  output.append(
        #     Abacus(
        #         date=(date.today() + timedelta(days=d)).strftime("%Y-%m-%d"),
        #         probabilities=probs.tolist(),
        #         campus="UCH",
        #     ),
        # )

    else:
        UCH = sitrep_store["T03"] + sitrep_store["T06"]
        WMS = sitrep_store["WMS"]
        GWB = sitrep_store["GWB"]
        NHNN = sitrep_store["NHNNC1"] + sitrep_store["NHNNC0"]

        # get current number of occupied beds
        for dept in [UCH, WMS, GWB, NHNN]:
            occupied_beds = len(dept)
            discharge_ready = len(
                [a for a in dept if a["discharge_ready_1_4h"] == "Yes"]
            )
            occupied_pmf = np.zeros(occupied_beds + 1)
            occupied_pmf[occupied_beds] = 1

            discharge_pmf = np.zeros(discharge_ready + 1)
            discharge_pmf[discharge_ready] = -1
            # ?? are these bits the right parts of the census store?

        # placeholder non-electives code - poisson around manually entered lambda
        # should be a api call to aggregate part of bournville?
        lam = 3
        repts = 1000
        non_elective_pmf, _ = np.histogram(
            np.random.poisson(lam, repts), bins=range(0, 20, 1), density=True
        )

        # electives aggregate
        elective_pmf = parse_to_data_frame(
            requests.get(url=f"{get_settings().api_url}/electives/aggregate/").json(),
            Abacus,
        )
        # combine pmfs
        abacus_pmf = np.convolve(
            np.convolve(np.convolve(occupied_pmf, discharge_pmf), elective_pmf),
            non_elective_pmf,
        )
        # temporary combination when just one value
        # abacus_pmf = elective_pmf

        # cumulative distribution function
        abacus_cmf = abacus_pmf.copy()
        abacus_cmf["probabilities"] = (
            abacus_pmf["probabilities"].apply(lambda x: (1 - np.cumsum(x))).tolist()
        )

        return [
            Abacus.parse_obj(row).dict() for row in abacus_cmf.to_dict(orient="records")
        ]


stores = html.Div(
    [
        dcc.Store(id=ids.DEPT_STORE),
        dcc.Store(id=ids.ROOM_STORE),
        dcc.Store(id=ids.BEDS_STORE),
        dcc.Store(id=ids.ELECTIVES_STORE),
        dcc.Store(id=ids.SITREP_STORE),
        dcc.Store(id=ids.ABACUS_STORE),
    ]
)
