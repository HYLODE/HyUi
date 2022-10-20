from collections import namedtuple
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, Query

from sqlalchemy import create_engine, text, bindparam
from sqlmodel import Session

from models.census import CensusRead, CensusDepartments
from api.db import get_star_session

from api.census.wrangle import aggregate_by_department
from api import wards

router = APIRouter(
    prefix="/census",
)

mock_router = APIRouter(
    prefix="/census",
)


def _mock_census_query_text():
    query_text = text(
        """SELECT *
        FROM census
        WHERE department IN :departments
        OR location_string IN :locations"""
    )

    return query_text.bindparams(  # type: ignore
        bindparam("departments", expanding=True),
        bindparam("locations", expanding=True),
    )


@mock_router.get("/beds", response_model=list[CensusRead])
def read_mock_beds(
    departments: list[str] = Query(default=wards.ALL),
    locations: list[str] = Query(default=[]),
):
    for d in departments:
        if missing_locations := wards.DEPARTMENTS_MISSING_BEDS.get(d):
            locations.extend(missing_locations)

    engine = create_engine(f"sqlite:///{Path(__file__).parent}/mock.db")
    query_text = _mock_census_query_text()

    params = {"departments": departments, "locations": locations}

    results = engine.execute(query_text, params)

    Record = namedtuple("Record", results.keys())  # type: ignore
    return [Record(*r) for r in results.fetchall()]


@router.get("/beds", response_model=list[CensusRead])
def read_beds(
    session: Session = Depends(get_star_session),
    departments: list[str] = Query(default=wards.ALL),
    locations: list[str] = Query(default=[]),
):
    """
    Returns beds data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    for d in departments:
        if missing_locations := wards.DEPARTMENTS_MISSING_BEDS.get(d):
            locations.extend(missing_locations)

    query_text = text((Path(__file__).parent / "live.sql").read_text())
    params = {"departments": departments, "locations": locations}
    # NOTE: this fails with sqlmodel.exec / works with sa.execute
    # import pdb; pdb.set_trace()
    results = session.execute(query_text, params)

    Record = namedtuple("Record", results.keys())  # type: ignore
    return [Record(*r) for r in results.fetchall()]


@mock_router.get("/beds/closed", response_model=dict)
def read_closed_beds():
    return {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "department": "UCH T01 ACUTE MEDICAL",
                "closed": False,
            },
            {
                "department": "UCH T01 ACUTE MEDICAL",
                "closed": True,
            },
        ],
    }


@router.get("/beds/list", response_model=dict[str, Any])
def read_bed_list():
    return {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "BedEpicId": "6959",
                "BedInCensus": "0",
                "BedName": "Lounge",
                "DepartmentExternalName": "UCH Tower 6th Floor Gynaecology (T06G)",
                "DepartmentKey": "31146",
                "DepartmentLevelOfCareGrouper": "Surgical",
                "DepartmentName": "UCH T06 GYNAE (T06G)",
                "DepartmentServiceGrouper": "Gynaecology",
                "DepartmentSpecialty": "Gynaecology - General",
                "DepartmentType": "HOD",
                "DischargeReady": "No",
                "IsBed": "1",
                "IsCareArea": "0",
                "IsDepartment": "0",
                "IsRoom": "0",
                "LocationName": "UNIVERSITY COLLEGE HOSPITAL CAMPUS",
                "Name": "Lounge",
                "ParentLocationName": "UCLH PARENT HOSPITAL",
                "RoomName": "Patient Lounge",
                "_CreationInstant": "47:26.0",
                "_LastUpdatedInstant": "06:27.0",
                "_merge": "both",
                "bed": "Lounge",
                "bed_functional": [],
                "bed_id": "332107431",
                "bed_physical": [],
                "closed": False,
                "covid": False,
                "department": "UCH T06 GYNAE (T06G)",
                "department_id": "331969463",
                "dept": "T06G",
                "id": 1,
                "loc2merge": (
                    "gynaecology - general __ uch t06 "
                    "gynae (t06g) __ patient lounge __ lounge"
                ),
                "location_id": "332107428",
                "location_string": "T06G^PATIENT LOUNGE^Lounge",
                "order": "1.00000000000000000000",
                "room": "Patient Lounge",
                "room_hl7": "PATIENT LOUNGE",
                "room_id": "332107429",
                "speciality": "Gynaecology - General",
                "unit_order": None,
            },
        ],
    }


def read_mock_census(departments: list[str], beds: list[str]) -> pd.DataFrame:
    engine = create_engine(f"sqlite:///{Path(__file__).parent}/mock.db")

    query_text = _mock_census_query_text()

    df = pd.read_sql(
        query_text,
        engine,
        params={
            "departments": departments,
            "locations": beds,
        },
    )

    # Correct types to aid further testing.
    df["cvl_admission"] = pd.to_datetime(df["cvl_admission"])
    df["cvl_discharge"] = pd.to_datetime(df["cvl_discharge"])
    df["modified_at"] = pd.to_datetime(df["modified_at"])

    return df


@mock_router.get("/departments", response_model=list[CensusDepartments])
def mock_read_departments():
    beds = tuple(wards.DEPARTMENTS_MISSING_BEDS.values())
    census_df = read_mock_census(wards.ALL, beds)
    return aggregate_by_department(census_df).to_dict(orient="records")


@router.get("/departments", response_model=list[CensusDepartments])
def read_departments(session: Session = Depends(get_star_session)):
    """
    Run the beds query then aggregate
    """
    query_text = text((Path(__file__).parent / "live.sql").read_text())

    params = {
        "departments": wards.ALL,
        "locations": tuple(wards.DEPARTMENTS_MISSING_BEDS.values()),
    }

    census_df = pd.read_sql(query_text, session.connection(), params=params)

    return aggregate_by_department(census_df).to_dict(orient="records")
