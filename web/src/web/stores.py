"""
Use for slowly updating API calls that can be shared between pages and
applications
"""

import orjson
from dash import Input, Output, callback, dcc, html
from typing import Optional

from models.beds import Bed, Department, Room
from models.electives import MergedData
from models.sitrep import SitrepRow
from models.hymind import IcuDischarge
from web import ids, SITREP_DEPT2WARD_MAPPING
from web.logger import logger, logger_timeit

from web.celery import redis_client
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
    ]
)
