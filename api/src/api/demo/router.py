import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends
from sqlmodel import Session
from sqlalchemy import text

from api.db import get_clarity_session
from models.demo import ClarityOrCase

router = APIRouter(prefix="/demo")

mock_router = APIRouter(prefix="/demo")


@mock_router.get("/", response_model=list[ClarityOrCase])
def get_mock_demo_rows():
    """
    Return mock data from adjacent mock.json file
    """
    with open(Path(__file__).parent / "mock.json", "r") as f:
        mock_json = json.load(f)
        mock_table = mock_json["rows"]
    return [ClarityOrCase.parse_obj(row) for row in mock_table]


@router.get("/", response_model=list[ClarityOrCase])
def get_demo_rows(session: Session = Depends(get_clarity_session), days_ahead: int = 1):
    """
    Return mock data by running query in anger
    response_model defines the data type (model) of the response
    """
    query = text((Path(__file__).parent / "live.sql").read_text())
    params = {"days_ahead": days_ahead}
    df = pd.read_sql(query, session.connection(), params=params)
    return [ClarityOrCase.parse_obj(row) for row in df.to_dict(orient="records")]
