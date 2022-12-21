from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, Query

from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.orm import Session

from api.wards import MISSING_LOCATION_DEPARTMENTS, MISSING_DEPARTMENT_LOCATIONS
from models.census import CensusDepartment, CensusRow
from api.db import get_star_session

from api.census.wrangle import aggregate_by_department
from api import wards

router = APIRouter(
    prefix="/census",
)

mock_router = APIRouter(
    prefix="/census",
)


def _fetch_census(
    session: Session, query: Any, departments: list[str], locations: list[str]
) -> list[CensusRow]:
    all_locations = locations.copy()

    # Some departments have locations (beds) that are missing. This adds them
    # in.
    for department in departments:
        if missing_locations := MISSING_DEPARTMENT_LOCATIONS.get(department):
            all_locations.extend(missing_locations)

    census_rows: list[CensusRow] = []

    result = session.execute(
        query, {"departments": departments, "locations": all_locations}
    )
    for row in result:
        census_row = CensusRow.parse_obj(row)

        # Add erroneously missing departments.
        if not census_row.department:
            census_row.department = MISSING_LOCATION_DEPARTMENTS.get(
                census_row.location_string
            )

        census_rows.append(census_row)

    return census_rows


def _fetch_mock_census(departments: list[str], locations: list[str]) -> list[CensusRow]:
    engine = create_engine(f"sqlite:///{Path(__file__).parent}/mock.db", future=True)

    query = text(
        """SELECT *
        FROM census
        WHERE department IN :departments
        OR location_string IN :locations"""
    ).bindparams(  # type: ignore
        bindparam("departments", expanding=True),
        bindparam("locations", expanding=True),
    )

    with Session(engine) as session:
        return _fetch_census(session, query, departments, locations)


@mock_router.get("/departments/", response_model=list[CensusDepartment])
def get_mock_departments() -> list[CensusDepartment]:
    census_rows = _fetch_mock_census(list(wards.ALL), [])
    census_df = pd.DataFrame((row.dict() for row in census_rows))
    departments_df = aggregate_by_department(census_df)

    return [
        CensusDepartment.parse_obj(row)
        for row in departments_df.to_dict(orient="records")
    ]


@router.get("/departments/", response_model=list[CensusDepartment])
def get_departments(
    session: Session = Depends(get_star_session),
) -> list[CensusDepartment]:
    query = text((Path(__file__).parent / "live.sql").read_text())
    census_rows = _fetch_census(session, query, list(wards.ALL), [])
    census_df = pd.DataFrame((row.dict() for row in census_rows))
    departments_df = aggregate_by_department(census_df)

    return [
        CensusDepartment.parse_obj(row)
        for row in departments_df.to_dict(orient="records")
    ]


@mock_router.get("/", response_model=list[CensusRow])
def get_mock_census(
    departments: list[str] = Query(default=[]),
    locations: list[str] = Query(default=[]),
) -> list[CensusRow]:
    return _fetch_mock_census(departments, locations)


@router.get("/", response_model=list[CensusRow])
def get_census(
    session: Session = Depends(get_star_session),
    departments: list[str] = Query(default=[]),
    locations: list[str] = Query(default=[]),
) -> list[CensusRow]:
    query = text((Path(__file__).parent / "live.sql").read_text())
    return _fetch_census(session, query, departments, locations)
