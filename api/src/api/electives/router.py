import json
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from api.db import get_caboodle_session, get_clarity_session
from api.electives.wrangle import prepare_electives
from models.electives import (
    CaboodleCaseBooking,
    CaboodlePreassessment,
    ClarityPostopDestination,
    ElectiveSurgCase,
)

router = APIRouter(
    prefix="/electives",
)

mock_router = APIRouter(prefix="/electives")


def _get_json_rows(filename: str):
    """
    Return mock data from adjacent mock.json file
    Assumes that data in nested object 'rows'
    """
    with open(Path(__file__).parent / filename, "r") as f:
        mock_json = json.load(f)
    mock_table = mock_json["rows"]
    return mock_table


# @router.get("/", response_model=List[GetElectiveRow])
# def get_electives(
#     days_ahead: int = 3,
#     settings: Settings = Depends(get_settings),
#     session_caboodle: Session = Depends(get_caboodle_session),
#     session_clarity: Session = Depends(get_clarity_session),
# ):
#     """
#     Returns Electives data class populated by query-live/mock
#     Includes
#     - post op destination info
#     """
#     # TODO: Fix this.
#     # query = read_query("live_case.sql", "electivesmock", settings.env)
#     # qtext = sa.text(query)
#     # params = {"days_ahead": days_ahead}
#     # dfcases = pd.read_sql(qtext, session_caboodle.connection(), params=params)
#     # dfcases = pydantic_dataframe(dfcases, ElectivesRead)
#     #
#     # query = read_query("live_pod.sql", "electivespodmock", settings.env)
#     # qtext = sa.text(query)
#     # params = {"days_ahead": days_ahead}
#     # dfpod = pd.read_sql(qtext, session_clarity.connection(), params=params)
#     # dfpod = pydantic_dataframe(dfpod, ElectivesPod)
#     #
#     # query = read_query("live_preassess.sql", "electivespreassessmock", settings.env)
#     # qtext = sa.text(query)
#     # params = {"days_ahead": days_ahead}
#     # dfpreassess = pd.read_sql(qtext, session_caboodle.connection(), params=params)
#     # dfpreassess = pydantic_dataframe(dfpreassess, ElectivesPreassess)
#     #
#     # df = prepare_electives(dfcases, dfpod, dfpreassess)
#     #
#     # if settings.VERBOSE:
#     #     print(df["pod_orc"].value_counts())
#     # return df.to_dict(orient="records")
#     return []


@router.get("/case_booking", response_model=list[CaboodleCaseBooking])
def get_caboodle_cases(
    session: Session = Depends(get_caboodle_session), days_ahead: int = 1
):
    """
    Return caboodle case booking data
    """
    query = text((Path(__file__).parent / "live_case.sql").read_text())
    params = {"days_ahead": days_ahead}
    df = pd.read_sql(query, session.connection(), params=params)
    return [CaboodleCaseBooking.parse_obj(row) for row in df.to_dict(orient="records")]


@mock_router.get("/case_booking", response_model=list[CaboodleCaseBooking])
def get_mock_caboodle_cases():
    """
    returns mock of caboodle query for elective cases
    :return:
    """
    rows = _get_json_rows("mock_case.json")
    return rows


@router.get("/postop_destination", response_model=list[ClarityPostopDestination])
def get_clarity_pod(
    session: Session = Depends(get_clarity_session), days_ahead: int = 1
):
    """
    Return clarity post op destination
    """
    query = text((Path(__file__).parent / "live_pod.sql").read_text())
    params = {"days_ahead": days_ahead}
    df = pd.read_sql(query, session.connection(), params=params)
    return [
        ClarityPostopDestination.parse_obj(row) for row in df.to_dict(orient="records")
    ]


@mock_router.get("/postop_destination", response_model=list[ClarityPostopDestination])
def get_mock_clarity_pod():
    """
    returns mock of caboodle query for preassessment
    """
    rows = _get_json_rows("mock_pod.json")
    return rows


@router.get("/preassessment", response_model=list[CaboodlePreassessment])
def get_caboodle_preassess(
    session: Session = Depends(get_caboodle_session), days_ahead: int = 1
):
    """
    Return caboodle preassessment data
    """
    query = text((Path(__file__).parent / "live_preassess.sql").read_text())
    params = {"days_ahead": days_ahead}
    df = pd.read_sql(query, session.connection(), params=params)
    return [
        CaboodlePreassessment.parse_obj(row) for row in df.to_dict(orient="records")
    ]


@mock_router.get("/preassessment", response_model=list[CaboodlePreassessment])
def get_mock_caboodle_preassess():
    """
    returns mock of caboodle query for preassessment
    :return:
    """
    rows = _get_json_rows("mock_preassess.json")
    return rows


@mock_router.get("/", response_model=list[ElectiveSurgCase])
def get_mock_electives(
    days_ahead: int = 3,
):
    """
    Returns Electives data class populated by query-live/mock
    Includes
    - post op destination info
    """

    _case = _get_json_rows("mock_case.json")
    _pod = _get_json_rows("mock_pod.json")
    _preassess = _get_json_rows("mock_preassess.json")

    df = prepare_electives(_case, _pod, _preassess)
    df = df.replace({np.nan: None})
    return [ElectiveSurgCase.parse_obj(row) for row in df.to_dict(orient="records")]


# @router.get("/cases/", response_model=list[ElectiveRow])
# def get_cases(
#     settings: Settings = Depends(get_settings),
#     session: Session = Depends(get_caboodle_session),
# ):
#     """
#     Returns Electives data class populated by query-live/mock
#     Limited to just surgical case info
#     """
#     # TODO: Fix this.
#     # query = read_query("live_case.sql", "electives", settings.dev)
#     # results = session.exec(query)
#     # Record = namedtuple("Record", results.keys())  # type: ignore
#     # records = [Record(*r) for r in results.fetchall()]\
#     # return records
#     return []


# @router.get("/pod", response_model=list[ElectivePostOpDestinationRow])
# def get_pod(
#     settings: Settings = Depends(get_settings),
#     session: Session = Depends(get_clarity_session),
# ):
#     """
#     Returns clarity periop destination query
#     """
#     # TODO: Fix this.
#     # query = read_query("live_pod.sql", "electivespod", settings.dev)
#     # results = session.exec(query)
#     # Record = namedtuple("Record", results.keys())  # type: ignore
#     # records = [Record(*r) for r in results.fetchall()]
#     # return records
#     return []


# @router.get("/preassess/", response_model=list[ElectivePreassessRow])
# def get_preassess(
#     settings: Settings = Depends(get_settings),
#     session: Session = Depends(get_caboodle_session),
# ):
#     """
#     Returns pre-assesment caboodle query
#     """
#     # TODO: Fix this.
#     # query = read_query("live_preassess.sql", "electivespreassessmock", settings.dev)
#     # results = session.exec(query)
#     # Record = namedtuple("Record", results.keys())  # type: ignore
#     # records = [Record(*r) for r in results.fetchall()]
#     # return records
#     return []
