# src/api/electives/router.py
from collections import namedtuple
from pathlib import Path
from typing import List

import pandas as pd
import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import parse_obj_as
from sqlmodel import Session

from config.settings import settings
from utils import get_model_from_route, prepare_query
from utils.api import (
    get_caboodle_session,
    get_clarity_session,
    pydantic_dataframe,
)

from .wrangle import prepare_electives

router = APIRouter(
    prefix="/electives",
)

CasesRead = get_model_from_route("Electives", "Read")
PodRead = get_model_from_route("Electives", "Pod")  # pod=post-op destination


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


@router.get("/", response_model=List[CasesRead])  # type: ignore
def read_cases(
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
    dfcases = pd.read_sql(qtext, session_caboodle.connection())
    dfcases = pydantic_dataframe(dfcases, CasesRead)

    query = read_query("live_pod.sql", "electivespodmock")
    qtext = sa.text(query)
    dfpod = pd.read_sql(qtext, session_clarity.connection())
    dfpod = pydantic_dataframe(dfpod, PodRead)

    df = prepare_electives(dfcases, dfpod)
    if settings.VERBOSE:
        print(df['PostOperativeDestination'].value_counts())
    records = df.to_dict(orient="records")
    return records


@router.get("/cases", response_model=List[CasesRead])  # type: ignore
def read_cases(session: Session = Depends(get_caboodle_session)):
    """
    Returns Electives data class populated by query-live/mock
    Limited to just surgical case info
    """
    query = read_query("live_case.sql", "electivesmock")
    results = session.exec(query)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


@router.get("/pod", response_model=List[PodRead])  # type: ignore
def read_pod(session: Session = Depends(get_clarity_session)):
    """
    Returns clarity periop destination query
    """
    # TODO: abstract this out
    query = read_query("live_pod.sql", "electivespodmock")
    results = session.exec(query)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
