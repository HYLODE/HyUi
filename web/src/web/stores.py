"""
Use for slowly updating API calls that can be shared between pages and
applications
"""

import requests
import orjson
from dash import Input, Output, callback, dcc, html
from typing import Optional

import pandas as pd

# from web import SITREP_DEPT2WARD_MAPPING

from models.beds import Bed, Department, Room
from models.electives import MergedData
from models.sitrep import SitrepRow, Abacus
from models.hymind import IcuDischarge
from web import ids, SITREP_DEPT2WARD_MAPPING
from web.logger import logger, logger_timeit
from web.convert import parse_to_data_frame
import numpy as np
from web.celery import redis_client
from web.config import get_settings

from web.celery_tasks import get_response
from web.celery_config import beat_schedule  # single source of truth for tasks

# TODO: add a refresh button as an input to the store functions pulling from
#  baserow so that changes from baserow edits can be brought through (
#  although a page refresh may do the same thing?)


def _get_or_refresh_cache(
    task: str, url: Optional[str] = None, expires: Optional[int] = None
) -> list[dict]:
    """
    Get or refresh a store using the task defined in beat_schedule

    Parameters
    ----------
    task : str - as defined in beat_schedule
    url : str - if you wish to override
    (i.e. when need to build for a specific endpoint)
    expires : int

    Returns
    -------
    list[dict]

    """
    if not url:
        url, cache_key = beat_schedule[task]["args"]  # tuple unpacking
    else:
        _, cache_key = beat_schedule[task]["args"]  # tuple unpacking

    if not expires:
        expires = beat_schedule.get(task).get("kwargs").get("expires")  # type: ignore

    cached_data = redis_client.get(cache_key)

    if cached_data is None:
        logger.info(f"Fetching {task} from API")
        fetch_data_task = get_response.delay(url, cache_key, expires)
        data = fetch_data_task.get()  # type: list[dict]
    else:
        logger.info(f"Fetching {task} from cached data")
        data = orjson.loads(cached_data)  # type: ignore

    return data


@callback(
    Output(ids.DEPT_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
)
@logger_timeit()
def _store_departments(_: int) -> list[dict]:
    """Store all open departments"""
    task = ids.DEPT_STORE
    data = _get_or_refresh_cache(task)
    depts = [Department.parse_obj(row).dict() for row in data]
    return [d for d in depts if not d.get("closed_perm_01")]


@callback(
    Output(ids.ROOM_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
)
@logger_timeit()
def _store_rooms(_: int) -> list[dict]:
    """Store all rooms with beds"""
    task = ids.ROOM_STORE
    data = _get_or_refresh_cache(task)
    rooms = [Room.parse_obj(row).dict() for row in data]
    return [r for r in rooms if r.get("has_beds")]


@callback(
    Output(ids.BEDS_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
)
@logger_timeit()
def _store_beds(_: int) -> list[dict]:
    task = ids.BEDS_STORE
    data = _get_or_refresh_cache(task)
    return [Bed.parse_obj(row).dict() for row in data]


@callback(
    Output(ids.ELECTIVES_STORE, "data"),
    Input(ids.STORE_TIMER_6H, "n_intervals"),
)
@logger_timeit()
def _store_electives(_: int) -> list[dict]:
    task = ids.ELECTIVES_STORE
    data = _get_or_refresh_cache(task)
    return [MergedData.parse_obj(row).dict() for row in data]


@callback(
    Output(ids.SITREP_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
)
@logger_timeit()
def _store_all_sitreps(_: int) -> dict:
    """
    Return sitrep status for all critical care areas
    Uses the beat_schedule defined in web.celery_config to hold urls
    """
    sitreps = {}
    for task, conf in beat_schedule.items():
        if not task.startswith(ids.SITREP_STORE):
            continue
        data = _get_or_refresh_cache(task)
        # FIXME: hacky way to get sitrep ICU b/c we know the 2nd arg (the key)
        # is the icu url and the last component is the icu
        # kkey = f"{web_ids.SITREP_STORE}-{icu}"
        icu = conf.get("args")[1].split("-")[-1]  # type: ignore
        assert icu in SITREP_DEPT2WARD_MAPPING.values()
        sitreps[icu] = [SitrepRow.parse_obj(row).dict() for row in data]

    return sitreps


@callback(
    Output(ids.ABACUS_STORE, "data"),
    Input(ids.STORE_TIMER_6H, "n_intervals"),
    Input(ids.SITREP_STORE, "data"),
    background=True,
)
def _store_all_abacus(_: int, sitrep_store: dict) -> list[dict]:
    # if get_settings().api_url.split("/")[-1] == "mock":
    #     num_beds = 24
    #     num_days = 7
    #     p, d, c = [], [], []
    #     for campus in ["UCH", "GWB", "WMS", "NHNN"]:
    #         for i in range(num_days):
    #             histogram, _ = np.histogram(np.random.randn(num_beds), bins=num_beds)
    #             probs = np.divide(np.flip(np.cumsum(histogram)), num_beds)
    #             probs[: np.random.randint(5, 15)] = 1
    #             p.append(probs.tolist())
    #             d.append((date.today() + timedelta(days=i)).strftime("%Y-%m-%d"))
    #             c.append(campus)
    #     return [
    #         Abacus.parse_obj(row).dict()
    #         for row in pd.DataFrame(
    #             columns=["campus", "date", "probabilities"], data=zip(c, d, p)
    #         ).to_dict(orient="records")
    #     ]
    #     #  I'm not sure why this stopped working...
    #     #  output.append(
    #     #     Abacus(
    #     #         date=(date.today() + timedelta(days=d)).strftime("%Y-%m-%d"),
    #     #         probabilities=probs.tolist(),
    #     #         campus="UCH",
    #     #     ),
    # #     # )

    # else:
    grouped_stores = {
        "UCH": sitrep_store["T03"] + sitrep_store["T06"],
        "WMS": sitrep_store["WMS"],
        "GWB": sitrep_store["GWB"],
        "NHNN": sitrep_store["NHNNC1"] + sitrep_store["NHNNC0"],
    }

    all_elective_pmf = parse_to_data_frame(
        requests.get(url=f"{get_settings().api_url}/electives/aggregate/").json(),
        Abacus,
    )

    pf, df, cf = [], [], []

    for d in all_elective_pmf["date"].unique():
        for campus_short, sitrep_data in grouped_stores.items():
            occupied_beds = len(sitrep_data)
            discharge_ready = len(
                [a for a in sitrep_data if a["discharge_ready_1_4h"] == "Yes"]
            )

            occupied_pmf = np.zeros(occupied_beds + 1)
            occupied_pmf[occupied_beds] = 1

            # TODO: placeholder -  using "discharge ready" rather than modelled
            #  - unsure best place to get from?
            discharge_pmf = np.zeros(discharge_ready + 1)
            discharge_pmf[discharge_ready] = -1
            # ?? are these bits the right parts of the census store?

            elective_df = all_elective_pmf[
                (all_elective_pmf["campus"] == campus_short)
                & (all_elective_pmf["date"] == d)
            ]
            if elective_df.empty:
                elective_pmf = np.zeros(10)
            else:
                elective_pmf = np.array(elective_df["probabilities"].values[0])
            # TODO: placeholder non-electives code - poisson
            # around manually entered lambda
            # should be an api call to aggregate part of bournville?

            lam = 2
            repts = 1000
            n_beds = 20
            non_elective_pmf, _ = np.histogram(
                np.random.poisson(lam, repts), bins=range(0, n_beds, 1), density=True
            )

            # combine pmfs (per date per campus)
            abacus_pmf = np.convolve(
                np.convolve(np.convolve(occupied_pmf, discharge_pmf), elective_pmf),
                non_elective_pmf,
            )

            # make cumulative function
            abacus_cmf = np.cumsum(abacus_pmf)
            if np.sum(abacus_cmf) < 0:
                abacus_cmf = abacus_cmf + 1

            pf.append(abacus_cmf.tolist())
            df.append(d)
            cf.append(campus_short)

            # abaci.append(
            #     Abacus(
            #         date=d,
            #         probabilities=abacus_cmf.tolist(),
            #         campus=campus_short,
            #     )
            # )

    return [
        Abacus.parse_obj(row).dict()
        for row in pd.DataFrame(
            columns=["campus", "date", "probabilities"], data=zip(cf, df, pf)
        ).to_dict(orient="records")
    ]


# [Abacus.parse_obj(row).dict() for row in abaci.to_dict(orient="records")]


@callback(
    Output(ids.HYMIND_ICU_DC_STORE, "data"),
    Input(ids.STORE_TIMER_1H, "n_intervals"),
)
def _store_all_hymind_dc_predictions(_: int) -> dict:
    """Return hymind predictions for all areas"""
    yhats = {}

    for task, conf in beat_schedule.items():
        if not task.startswith(ids.HYMIND_ICU_DC_STORE):
            continue
        data = _get_or_refresh_cache(task)
        # FIXME: hacky way to get sitrep ICU b/c we know the 2nd arg (the key)
        # is the icu url and the last component is the icu
        # kkey = f"{web_ids.SITREP_STORE}-{icu}"
        icu = conf.get("args")[1].split("-")[-1]  # type: ignore
        assert icu in SITREP_DEPT2WARD_MAPPING.values()
        yhats[icu] = [IcuDischarge.parse_obj(row).dict() for row in data]

    return yhats


web_stores = html.Div(
    [
        dcc.Store(id=ids.DEPT_STORE),
        dcc.Store(id=ids.ROOM_STORE),
        dcc.Store(id=ids.BEDS_STORE),
        dcc.Store(id=ids.ELECTIVES_STORE),
        dcc.Store(id=ids.SITREP_STORE),
        dcc.Store(id=ids.HYMIND_ICU_DC_STORE),
        dcc.Store(id=ids.ABACUS_STORE),
    ]
)
