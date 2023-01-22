"""
Serve the PERRT endpoints
- raw data in long form from EMAP visit observation table
- wrangled data at the route
"""

import datetime as dt
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from api.convert import parse_to_data_frame, to_data_frame
from api.db import get_star_session
from api.mock import _get_json_rows, _parse_query
from api.perrt.wrangle import wrangle
from models.perrt import EmapConsults, EmapCpr, EmapVitalsLong, EmapVitalsWide

router = APIRouter(prefix="/perrt")
mock_router = APIRouter(prefix="/perrt")
_this_file = Path(__file__)


@router.get("/cpr", response_model=list[EmapCpr])
def get_emap_cpr(
    session: Session = Depends(get_star_session),
    encounter_ids: list[str] = Query(default=[]),
):
    """
    Return advance decisions about CPR
    :type session: Session object from sqlmodel
    """
    params = {"encounter_ids": encounter_ids}
    res = _parse_query(_this_file, "live_cpr.sql", session, EmapCpr, params)
    return res


@mock_router.get("/cpr", response_model=list[EmapCpr])
def get_mock_emap_cpr():
    """
    Return mock consults to PERRT or ICU
    :return:
    """
    rows = _get_json_rows(_this_file, "mock_cpr.json")
    return rows


@router.get("/consults", response_model=list[EmapConsults])
def get_emap_perrt_consults(
    session: Session = Depends(get_star_session),
    encounter_ids: list[str] = Query(default=[]),
    horizon_dt: dt.datetime = dt.datetime.now() - dt.timedelta(days=7),
):
    """
    Return consults to PERRT or ICU
    :type session: Session object from sqlmodel
    :type horizon_dt: datetime remember to diff this from 'now'
    """
    params = {"encounter_ids": encounter_ids, "horizon_dt": horizon_dt}
    res = _parse_query(_this_file, "live_consults.sql", session, EmapConsults, params)
    return res


@mock_router.get("/consults", response_model=list[EmapConsults])
def get_mock_emap_perrt_consults():
    """
    Return mock consults to PERRT or ICU
    :return:
    """
    rows = _get_json_rows(_this_file, "mock_consults.json")
    return rows


@router.get("/vitals/long", response_model=list[EmapVitalsLong])
def get_emap_vitals_long(
    session: Session = Depends(get_star_session),
    encounter_ids: list[str] = Query(default=[]),
    horizon_dt: dt.datetime = dt.datetime.now() - dt.timedelta(hours=6),
):
    """
    Return vital signs
    :type session: Session object from sqlmodel
    :type horizon_dt: datetime remember to diff this from 'now'
    """
    params = {"encounter_ids": encounter_ids, "horizon_dt": horizon_dt}
    res = _parse_query(_this_file, "live_vitals.sql", session, EmapVitalsLong, params)
    return res


@mock_router.get("/vitals/long", response_model=list[EmapVitalsLong])
def get_mock_emap_vitals_long():
    """
    returns mock of emap query for vital signs
    :return:
    """
    rows = _get_json_rows(_this_file, "mock_vitals.json")
    return rows


# TODO: 2022-12-06 rather than prepare the vitals and the patients together;
#  leave that to the front end which can use census itself and instead you
#  will need a query for perrt consults and a wrangle to return one row per
#  encounter for the vitals
@router.get("/vitals/wide", response_model=list[EmapVitalsWide])
def get_emap_vitals_wide(
    session: Session = Depends(get_star_session),
    encounter_ids: list[str] = Query(default=[]),
    horizon_dt: dt.datetime = dt.datetime.now() - dt.timedelta(hours=6),
):
    """
    Return vital signs as a wide table after wrangling
    :type horizon_dt: datetime remember to diff this from 'now'
    """
    params = {"encounter_ids": encounter_ids, "horizon_dt": horizon_dt}
    rows = _parse_query(_this_file, "live_vitals.sql", session, EmapVitalsLong, params)
    df = to_data_frame(rows, EmapVitalsLong)
    df_wide = wrangle(df)

    return [EmapVitalsWide.parse_obj(row) for row in df_wide.to_dict(orient="records")]


@mock_router.get("/vitals/wide")
def get_mock_emap_vitals_wide():
    """
    returns mock of emap query after wrangling
    :return:
    """
    rows = _get_json_rows(_this_file, "mock_vitals.json")
    df = parse_to_data_frame(rows, EmapVitalsLong)
    df_wide = wrangle(df)

    return [EmapVitalsWide.parse_obj(row) for row in df_wide.to_dict(orient="records")]


