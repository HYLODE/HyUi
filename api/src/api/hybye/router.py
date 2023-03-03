from pathlib import Path
import random
from typing import List
import datetime

from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy import text
from sqlmodel import Session

from api.wards import CAMPUSES
from api.db import get_star_session
from models.hybye import DischargeRow

router = APIRouter(prefix="/hybye")

mock_router = APIRouter(prefix="/hybye")


@mock_router.get(
    "/discharge/n_days/{number_of_days}", response_model=List[DischargeRow]
)
def get_mock_discharges_for_last_n_days(number_of_days: int) -> List[DischargeRow]:
    today = datetime.datetime.now().date()
    last_n_days = [today - datetime.timedelta(days=i) for i in range(number_of_days)]

    mock_discharge_rows: List[DischargeRow] = []

    for day in last_n_days:
        mock_discharge_rows.append(
            DischargeRow(discharge_date=day, count=random.randint(20, 200))
        )

    return mock_discharge_rows


@router.get("/discharge/n_days/{number_of_days}", response_model=List[DischargeRow])
def get_discharges_for_last_n_days(
    number_of_days: int,
    response: Response,
    session: Session = Depends(get_star_session),
    campuses: list[str] = Query(default=[]),
) -> List[DischargeRow]:
    """
    Parameters
    ----------
    campuses: str, campus code as per the dictionary in api.wards.CAMPUSES
    number_of_days: int, number of days to look retrospectively for
    response: Response - leave as default
    session: Session - leave as default

    Returns
    -------
    List of DischargeRow objects (datetime.date, int)
    """
    departments: list = []
    for campus in campuses:
        departments.extend(CAMPUSES.get(campus, []))

    response.headers["Cache-Control"] = "public, max-age=300"
    query = text((Path(__file__).parent / "get_inpatient_discharges.sql").read_text())
    result = session.execute(
        query, {"days": number_of_days, "departments": departments}
    )

    discharge_rows: List[DischargeRow] = []

    for row in result:
        discharge_rows.append(DischargeRow.parse_obj(row))

    return discharge_rows
