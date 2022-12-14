import json
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text, create_engine
from sqlmodel import Session

from api.db import get_caboodle_session, get_clarity_session
from api.electives.wrangle import prepare_draft, prepare_electives
from models.electives import (
    CaboodleCaseBooking,
    CaboodlePreassessment,
    ClarityPostopDestination,
    ElectiveSurgCase,
    SurgData,
    PreassessData,
    MergedData,
    LabData,
    EchoData,
    ObsData,
)

router = APIRouter(
    prefix="/electives",
)

mock_router = APIRouter(prefix="/electives")


def _get_json_rows(filename: str) -> list[dict]:
    """
    Return mock data from adjacent mock.json file
    Assumes that data in nested object 'rows'
    """
    with open(Path(__file__).parent / filename, "r") as f:
        mock_json = json.load(f)
        return cast(list[dict], mock_json["rows"])


def _get_mock_sql_rows(table: str, model: type[BaseModel]) -> list[type[BaseModel]]:

    engine = create_engine(f"sqlite:///{Path(__file__).parent}/mock.db", future=True)

    with Session(engine) as session:
        query = text(f"SELECT * FROM {table}")
        result = session.execute(query)
        return [model.parse_obj(row) for row in result]


def _parse_query(
    query_file: str, session: Session, model: BaseModel, params: dict
) -> list[BaseModel]:
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


@router.get("/case_booking/", response_model=list[CaboodleCaseBooking])
def get_caboodle_cases(
    session: Session = Depends(get_caboodle_session), days_ahead: int = 1
) -> list[CaboodleCaseBooking]:
    """
    Return caboodle case booking data
    """
    params = {"days_ahead": days_ahead}
    return _parse_query("live_case.sql", session, CaboodleCaseBooking, params)


@mock_router.get("/case_booking/", response_model=list[SurgData])
def get_mock_caboodle_cases() -> list[SurgData]:
    """
    returns mock of caboodle query for elective cases
    :return:
    """
    return _get_mock_sql_rows("surg", SurgData)


@router.get("/postop_destination/", response_model=list[ClarityPostopDestination])
def get_clarity_pod(
    session: Session = Depends(get_clarity_session), days_ahead: int = 1
) -> list[ClarityPostopDestination]:
    """
    Return clarity post op destination
    """
    params = {"days_ahead": days_ahead}
    return _parse_query("live_pod.sql", session, ClarityPostopDestination, params)


@mock_router.get("/postop_destination/", response_model=list[ClarityPostopDestination])
def get_mock_clarity_pod() -> list[ClarityPostopDestination]:
    """
    returns mock of caboodle query for preassessment
    """
    return _get_json_rows("mock_pod.json")


@router.get("/preassessment/", response_model=list[CaboodlePreassessment])
def get_caboodle_preassess(
    session: Session = Depends(get_caboodle_session), days_ahead: int = 1
) -> list[CaboodlePreassessment]:
    """
    Return caboodle preassessment data
    """
    params = {"days_ahead": days_ahead}
    return _parse_query("live_preassess.sql", session, CaboodlePreassessment, params)


@mock_router.get("/preassessment/", response_model=list[PreassessData])
def get_mock_caboodle_preassess() -> list[PreassessData]:
    return _get_mock_sql_rows("preassess", PreassessData)


@mock_router.get("/labs/", response_model=list[LabData])
def get_mock_labs() -> list[LabData]:
    return _get_mock_sql_rows("labs", LabData)


@router.get("/", response_model=list[ElectiveSurgCase])
def get_electives(
    s_caboodle: Session = Depends(get_caboodle_session),
    s_clarity: Session = Depends(get_clarity_session),
    days_ahead: int = 3,
) -> list[ElectiveSurgCase]:
    """
    Returns elective surgical cases by wrangling together the three components
    """
    params = {"days_ahead": days_ahead}
    case = _parse_query("live_case.sql", s_caboodle, CaboodleCaseBooking, params)
    preassess = _parse_query(
        "live_preassess.sql", s_caboodle, CaboodlePreassessment, params
    )
    pod = _parse_query("live_pod.sql", s_clarity, ClarityPostopDestination, params)

    df = prepare_electives(case, pod, preassess)
    df = df.replace({np.nan: None})
    return [ElectiveSurgCase.parse_obj(row) for row in df.to_dict(orient="records")]


@mock_router.get("/echo/", response_model=list[EchoData])
def get_mock_echo() -> list[EchoData]:
    return _get_mock_sql_rows("echo", EchoData)


@mock_router.get("/obs/", response_model=list[ObsData])
def get_mock_obs() -> list[ObsData]:
    return _get_mock_sql_rows("obs", ObsData)


@mock_router.get("/", response_model=list[MergedData])
def get_mock_electives(
    #   days_ahead: int = 100,
) -> list[MergedData]:

    case = _get_mock_sql_rows("surg", SurgData)
    preassess = _get_mock_sql_rows("preassess", PreassessData)
    labs = _get_mock_sql_rows("labs", LabData)
    echo = _get_mock_sql_rows("echo", EchoData)
    obs = _get_mock_sql_rows("obs", ObsData)

    df = prepare_draft(case, preassess, labs, echo, obs)
    df = df.replace({np.nan: None})
    return [MergedData.parse_obj(row) for row in df.to_dict(orient="records")]
