from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine
from sqlmodel import Session

from api.config import get_settings

from api.baserow import get_fields, get_rows

# TODO: Give sitrep its own CensusRow model so we do not have interdependencies.
from models.census import CensusRow
from models.sitrep import (
    SitrepRow,
    IndividualDischargePrediction,
    BedRow,
)

CORE_FIELDS = [
    "department",
    "room",
    "bed",
    "unit_order",
    "closed",
    "covid",
    "bed_functional",
    "bed_physical",
    "DischargeReady",
    "location_id",
    "location_string",
]

router = APIRouter(
    prefix="/sitrep",
)

mock_router = APIRouter(
    prefix="/sitrep",
)


@router.get("/beds/", response_model=list[BedRow])
def get_beds(department: str, settings=Depends(get_settings)):

    baserow_url = settings.baserow_url
    token = settings.baserow_read_write_token
    beds_table_id = settings.baserow_beds_table_id

    field_ids = get_fields(baserow_url, token, beds_table_id)

    department_field_id = field_ids["department"]

    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{department_field_id}__equal": department,
    }

    rows = get_rows(baserow_url, token, beds_table_id, params)
    return [BedRow.parse_obj(row) for row in rows]


@mock_router.get("/beds/", response_model=list[BedRow])
def get_mock_beds(department: str) -> list[BedRow]:
    return [
        BedRow(
            location_string="location_a",
            bed_functional=[],
            bed_physical=[],
            unit_order=3,
            closed=False,
            bed="a-b",
            bed_label="1bed-2label",
            room="SR-room",
            covid=False,
        )
    ]


@router.get("/census/", response_class=RedirectResponse)
def get_census(department: str) -> str:
    params = urlencode({"department": department})
    return f"/census/?{params}"


@mock_router.get("/census/", response_model=list[CensusRow])
def get_mock_census(department: str) -> list[CensusRow]:
    return [
        CensusRow(
            encounter=1,
            location_string="location_a",
            date_of_birth=date(2001, 2, 3),
            mrn="abc",
            firstname="Firstname",
            lastname="Lastname",
            modified_at=datetime(2022, 1, 2, 3, 4),
            location_id=2,
            department="My Department",
        )
    ]


@mock_router.get("/live/{ward}/ui", response_model=list[SitrepRow])
def get_mock_live_ui(ward: str) -> list[SitrepRow]:
    engine = create_engine(f"sqlite:///{Path(__file__).parent}/mock.db", future=True)

    with Session(engine) as session:
        result = session.execute("SELECT * FROM sitrep")
        return [SitrepRow.parse_obj(row) for row in result]


@router.get("/live/{ward}/ui", response_model=list[SitrepRow])
def get_live_ui(ward: str, settings=Depends(get_settings)) -> list[SitrepRow]:
    response = requests.get(f"{settings.hycastle_url}/live/icu/{ward}/ui")
    return [SitrepRow.parse_obj(row) for row in response.json()]


@router.patch("/beds")
def update_bed_row(
    table_id: int, row_id: int, data: dict, settings=Depends(get_settings)
):
    url = f"{settings.baserow_url}/api/database/rows/table/{table_id}/"

    # TODO: Need to get working.
    requests.patch(
        url=f"{url}{row_id}/?user_field_names=true",
        headers={
            "Authorization": f"Token {settings.BASEROW_READWRITE_TOKEN}",
            "Content-Type": "application/json",
        },
        json=data,
    )


@router.get(
    "/predictions/discharge/individual/{ward}",
    response_model=list[IndividualDischargePrediction],
)
def get_individual_discharge_predictions(
    ward: str,
) -> list[IndividualDischargePrediction]:
    raise NotImplementedError("Need to call API endpoint.")


@mock_router.get(
    "/predictions/discharge/individual/{ward}",
    response_model=list[IndividualDischargePrediction],
)
def get_mock_individual_discharge_predictions(
    ward: str,
) -> list[IndividualDischargePrediction]:
    return [IndividualDischargePrediction(episode_slice_id=1, prediction=0.4)]
