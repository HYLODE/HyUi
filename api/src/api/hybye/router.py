from pathlib import Path
import random
from typing import List

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlmodel import Session

from api.db import get_star_session
from models.hybye import DischargeRow

router = APIRouter(prefix="/hybye")

mock_router = APIRouter(prefix="/hybye")


@mock_router.get("/discharge/n_days/{number_of_days}", response_model=list[int])
def get_mock_discharges_for_last_n_days(number_of_days: int) -> list[int]:
    return [random.randint(2, 200) for num in range(number_of_days)]


@router.get("/discharge/n_days/{number_of_days}", response_model=List[DischargeRow])
def get_discharges_for_last_n_days(
        number_of_days: int,
        response: Response,
        session: Session = Depends(get_star_session),
) -> List[DischargeRow]:
    """
    Parameters
    ----------
    number_of_days: int, number of days to look back at
    response: Response - default
    session: Session - default

    Returns
    -------
    List of DischargeRow objects (datetime.date, int)
    """
    response.headers["Cache-Control"] = "public, max-age=300"
    query = text((Path(__file__).parent / "get_inpatient_discharges.sql").read_text())
    result = session.execute(query, {"days": number_of_days})

    discharge_rows: List[DischargeRow] = []

    for row in result:
        discharge_rows.append(DischargeRow.parse_obj(row))

    return discharge_rows
