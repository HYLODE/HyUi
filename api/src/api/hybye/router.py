from pathlib import Path
import random
from typing import List
import datetime

from fastapi import APIRouter, Depends, Response, Query
from sqlalchemy import text
from sqlmodel import Session

from api.wards import CAMPUSES
from api.db import get_star_session
from models.hybye import HospitalFlowRow

router = APIRouter(prefix="/hybye")

mock_router = APIRouter(prefix="/hybye")


@mock_router.get(
    "/discharge/n_days/{number_of_days}", response_model=List[HospitalFlowRow]
)
def get_mock_discharges_for_last_n_days(
    number_of_days: int, campuses: list[str] = Query(default=[])
) -> List[HospitalFlowRow]:
    today = datetime.datetime.now().date()
    last_n_days = [today - datetime.timedelta(days=i) for i in range(number_of_days)]

    # Return nothing if no campuses queried
    if len(campuses) < 1:
        return []

    # If not given any valid campus names raise error
    if not any(campus in campuses for campus in CAMPUSES):
        raise KeyError("Invalid campus name")

    mock_discharge_rows: List[HospitalFlowRow] = []

    for day in last_n_days:
        mock_discharge_rows.append(
            HospitalFlowRow(discharge_date=day, count=random.randint(20, 200))
        )

    return mock_discharge_rows


@router.get("/discharge/n_days/{number_of_days}", response_model=List[HospitalFlowRow])
def get_discharges_for_last_n_days(
    number_of_days: int,
    response: Response,
    session: Session = Depends(get_star_session),
    campuses: list[str] = Query(default=[]),
) -> List[HospitalFlowRow]:
    """
    Parameters
    ----------
    campuses: str, campus code as per the dictionary in api.wards.CAMPUSES
    number_of_days: int, number of days to look retrospectively for
    response: Response - leave as default
    session: Session - leave as default

    Returns
    -------
    List of HospitalFlowRow objects (datetime.date, int)
    """
    departments: list = []
    # Get all the wards for a given campus using api.wards collections
    for campus in campuses:
        departments.extend(CAMPUSES.get(campus, []))

    response.headers["Cache-Control"] = "public, max-age=300"
    query = text((Path(__file__).parent / "get_inpatient_discharges.sql").read_text())
    result = session.execute(
        query, {"days": number_of_days, "departments": departments}
    )

    discharge_rows: List[HospitalFlowRow] = []

    for row in result:
        discharge_rows.append(HospitalFlowRow.parse_obj(row))

    return discharge_rows


@router.get("/admitted/n_days/{number_of_days}", response_model=List[HospitalFlowRow])
def get_admissions_for_last_n_days(
    number_of_days: int,
    response: Response,
    session: Session = Depends(get_star_session),
    campuses: list[str] = Query(default=[]),
) -> List[HospitalFlowRow]:
    """
    Parameters
    ----------
    campuses: str, campus code as per the dictionary in api.wards.CAMPUSES
    number_of_days: int, number of days to look retrospectively for
    response: Response - leave as default
    session: Session - leave as default

    Returns
    -------
    List of HospitalFlowRow objects (datetime.date, int) for admissions for last n days
    """
    departments: list = []
    # Get all the wards for a given campus using api.wards collections
    for campus in campuses:
        departments.extend(CAMPUSES.get(campus, []))

    response.headers["Cache-Control"] = "public, max-age=300"
    query = text((Path(__file__).parent / "get_inpatient_admissions.sql").read_text())
    result = session.execute(
        query, {"days": number_of_days, "departments": departments}
    )

    admission_rows: List[HospitalFlowRow] = []

    for row in result:
        admission_rows.append(HospitalFlowRow.parse_obj(row))
        
    print(admission_rows)

    return admission_rows
