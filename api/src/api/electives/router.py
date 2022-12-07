import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text, create_engine  # , bindparam
from sqlmodel import Session

from api.db import get_caboodle_session, get_clarity_session
from api.electives.wrangle import prepare_draft  # prepare_electives
from models.electives import (
    CaboodleCaseBooking,
    CaboodlePreassessment,
    ClarityPostopDestination,
    # ElectiveSurgCase,
    SurgData,
    PreassessData,
    Merged_Preassess,
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


def _get_sql_rows(table: str, model):

    engine = create_engine(f"sqlite:///{Path(__file__).parent}/mock.db", future=True)
    query = text(f"""SELECT * FROM {table}""")

    with engine.connect() as conn:
        # result = conn.execute(query)
        #   result_as_json = json.dumps([dict(r) for r in result])
        df_result = pd.read_sql(query, conn)

        columns_with_datetimes = df_result.filter(
            regex="Date|date|Instant", axis=1
        ).columns
        for col in columns_with_datetimes:
            df_result[col] = pd.to_datetime(df_result[col])

    json_result = [model.parse_obj(row) for row in df_result.to_dict(orient="records")]
    return json_result


def _parse_query(
    query_file: str, session: Session, model: BaseModel, params: Dict = {}
) -> List[BaseModel]:
    """
    generic function that reads a text query from a file, handles parameters
    within the query and then returns after parsing through a pydantic model

    :param query_file:
    :param params:
    :param model:
    :return:
    """
    query = text((Path(__file__).parent / query_file).read_text())
    df = pd.read_sql(query, session.connection(), params=params)
    return [model.parse_obj(row) for row in df.to_dict(orient="records")]


@router.get("/case_booking", response_model=list[CaboodleCaseBooking])
def get_caboodle_cases(
    session: Session = Depends(get_caboodle_session), days_ahead: int = 1
):
    """
    Return caboodle case booking data
    """
    params = {"days_ahead": days_ahead}
    res = _parse_query("live_case.sql", session, CaboodleCaseBooking, params)
    return res


@mock_router.get(
    "/case_booking", response_model=list[SurgData]
)  # response_model=list[CaboodleCaseBooking])
def get_mock_caboodle_cases():
    """
    returns mock of caboodle query for elective cases
    :return:
    """
    # rows = _get_json_rows("mock_case.json")
    rows = _get_sql_rows("surg", SurgData)
    return rows


@router.get("/postop_destination", response_model=list[ClarityPostopDestination])
def get_clarity_pod(
    session: Session = Depends(get_clarity_session), days_ahead: int = 1
):
    """
    Return clarity post op destination
    """
    params = {"days_ahead": days_ahead}
    res = _parse_query("live_pod.sql", session, ClarityPostopDestination, params)
    return res


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
    params = {"days_ahead": days_ahead}
    res = _parse_query("live_preassess.sql", session, CaboodlePreassessment, params)
    return res


@mock_router.get(
    "/preassessment", response_model=list[PreassessData]
)  # response_model=list[CaboodlePreassessment])
def get_mock_caboodle_preassess():
    # rows = _get_json_rows("mock_preassess.json")
    rows = _get_sql_rows("preassess", PreassessData)

    return rows


@mock_router.get("/", response_model=list[Merged_Preassess])
def get_mock_electives(
    #   days_ahead: int = 100,
):
    """
    Returns Electives data class populated by query-live/mock
    Includes
    - post op destination info
    """
    _case = _get_sql_rows("surg", SurgData)
    _preassess = _get_sql_rows("preassess", PreassessData)

    df = prepare_draft(_case, _preassess)
    df = df.replace({np.nan: None})
    return [Merged_Preassess.parse_obj(row) for row in df.to_dict(orient="records")]


# @router.get("/", response_model=list[ElectiveSurgCase])
# def get_electives(
#     s_caboodle: Session = Depends(get_caboodle_session),
#     s_clarity: Session = Depends(get_clarity_session),
#     days_ahead: int = 3,
# ):
#     """
#     Returns elective surgical cases by wrangling together the three components
#     """
#     params = {"days_ahead": days_ahead}
#     _case = _parse_query("live_case.sql", s_caboodle, CaboodleCaseBooking, params)
#     _preassess = _parse_query(
#         "live_preassess.sql", s_caboodle, CaboodlePreassessment, params
#     )
#     _pod = _parse_query("live_pod.sql", s_clarity, ClarityPostopDestination, params)

#     df = prepare_electives(_case, _pod, _preassess)
#     df = df.replace({np.nan: None})
#     return [ElectiveSurgCase.parse_obj(row) for row in df.to_dict(orient="records")]
