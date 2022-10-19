from collections import namedtuple
from typing import Any

import pandas as pd
import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query
from pydantic import parse_obj_as
from sqlmodel import Session

from models.census import CensusRead, CensusDepartments
from api.db import prepare_query, get_emap_session

from api.census.wrangle import aggregate_by_department
from api import wards

router = APIRouter(
    prefix="/census",
)


@router.get("/beds", response_model=list[CensusRead])
def read_beds(
    session: Session = Depends(get_emap_session),
    departments: list[str] = Query(default=wards.ALL),
    locations: list[str] = Query(default=[]),
):
    """
    Returns beds data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    for d in departments:
        if d in wards.DEPARTMENTS_MISSING_BEDS.keys():
            locations_to_add = wards.DEPARTMENTS_MISSING_BEDS[d]
            locations.extend(locations_to_add)

    qtext = prepare_query("census")
    qtext = sa.text(qtext)
    # necessary if working with mock data from sqlite rather than postgres
    if session.get_bind().name == "sqlite":
        # as per https://stackoverflow.com/a/56382828/992999
        qtext = qtext.bindparams(  # type: ignore
            sa.bindparam("departments", expanding=True),
            sa.bindparam("locations", expanding=True),
        )

    params = {"departments": departments, "locations": locations}
    # NOTE: this fails with sqlmodel.exec / works with sa.execute
    # import pdb; pdb.set_trace()
    results = session.execute(qtext, params)

    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


@router.get("/beds/closed", response_model=dict)
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


@router.get("/departments", response_model=list[CensusDepartments])
def read_departments(session: Session = Depends(get_emap_session)):
    """
    Run the beds query then aggregate
    """
    locations: list[str] = []
    # this 'duplicates' functionality above but the alternative is to swap out
    # Query/Depends etc from the function b/c when called directly without the
    # decorator then all the types are wrong

    # add in locations without departments
    # TODO: need to use this info to add the department into the results
    for d in wards.ALL:
        if d in wards.DEPARTMENTS_MISSING_BEDS.keys():
            locations_to_add = wards.DEPARTMENTS_MISSING_BEDS[d]
            locations.extend(locations_to_add)

    qtext = prepare_query("census")
    qtext = sa.text(qtext)
    # necessary if working with mock data from sqlite rather than postgres
    if session.get_bind().name == "sqlite":
        # as per https://stackoverflow.com/a/56382828/992999
        qtext = qtext.bindparams(  # type: ignore
            sa.bindparam("departments", expanding=True),
            sa.bindparam("locations", expanding=True),
        )

    params = {"departments": wards.ALL, "locations": locations}

    df = pd.read_sql(qtext, session.connection(), params=params)

    # round trip from dataframe to dictionary to records back to dataframe
    # just to use the data validation properties of pydantic!
    l_of_d = df.to_dict(orient="records")
    l_of_r = parse_obj_as(list[CensusRead], l_of_d)
    df = pd.DataFrame.from_dict([r.dict() for r in l_of_r])

    res = aggregate_by_department(df).to_dict(orient="records")
    return res
