from collections import namedtuple
from pathlib import Path
from typing import List

import pandas as pd
import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlmodel import Session

from config.settings import settings
from models.electives import ElectivesRead, ElectivesPod, ElectivesPreassess
from utils.api import (
    get_caboodle_session,
    get_clarity_session,
    pydantic_dataframe,
)

from .wrangle import prepare_electives

router = APIRouter(
    prefix="/electives",
)


def read_query(file_live: str, table_mock: str):
    """
    generates a query based on the environment

    :param      file_live:   The file live
                             e.g. live_case.sql
    :param      table_mock:  The table mock
                             e.g. electivesmock
    returns a string containing a SQL query
    """
    if settings.ENV == "dev":
        query = f"SELECT * FROM {table_mock}"
    else:
        sql_file = Path(__file__).resolve().parent / file_live
        query = Path(sql_file).read_text()
    return query


@router.get("/", response_model=List[ElectivesRead])
def read_electives(
    days_ahead: int = 3,
    session_caboodle: Session = Depends(get_caboodle_session),
    session_clarity: Session = Depends(get_clarity_session),
):
    """
    Returns Electives data class populated by query-live/mock
    Includes
    - post op destination info
    """
    query = read_query("live_case.sql", "electivesmock")
    qtext = sa.text(query)
    params = {"days_ahead": days_ahead}
    dfcases = pd.read_sql(qtext, session_caboodle.connection(), params=params)
    dfcases = pydantic_dataframe(dfcases, ElectivesRead)

    query = read_query("live_pod.sql", "electivespodmock")
    qtext = sa.text(query)
    params = {"days_ahead": days_ahead}
    dfpod = pd.read_sql(qtext, session_clarity.connection(), params=params)
    dfpod = pydantic_dataframe(dfpod, ElectivesPod)

    query = read_query("live_preassess.sql", "electivespreassessmock")
    qtext = sa.text(query)
    params = {"days_ahead": days_ahead}
    dfpreassess = pd.read_sql(qtext, session_caboodle.connection(), params=params)
    dfpreassess = pydantic_dataframe(dfpreassess, ElectivesPreassess)

    df = prepare_electives(dfcases, dfpod, dfpreassess)

    if settings.VERBOSE:
        print(df["pod_orc"].value_counts())
    return df.to_dict(orient="records")


@router.get("/cases", response_model=List[ElectivesRead])
def read_cases(session: Session = Depends(get_caboodle_session)):
    """
    Returns Electives data class populated by query-live/mock
    Limited to just surgical case info
    """
    query = read_query("live_case.sql", "electivesmock")
    results = session.exec(query)
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


@router.get("/pod", response_model=List[ElectivesPod])
def read_pod(session: Session = Depends(get_clarity_session)):
    """
    Returns clarity periop destination query
    """
    query = read_query("live_pod.sql", "electivespodmock")
    results = session.exec(query)
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


@router.get("/preassess", response_model=List[ElectivesPreassess])
def read_preassess(session: Session = Depends(get_caboodle_session)):
    """
    Returns pre-assesment caboodle query
    """
    query = read_query("live_preassess.sql", "electivespreassessmock")
    results = session.exec(query)
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
