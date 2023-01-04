from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine
from sqlmodel import Session

from api.config import Settings, get_settings

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
def get_beds(
    department: str, settings: Settings = Depends(get_settings)
) -> list[BedRow]:

    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    field_ids = get_fields(baserow_url, email, password, "hyui", "beds")

    department_field_id = field_ids["department"]

    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{department_field_id}__equal": department,
    }

    rows = get_rows(baserow_url, email, password, "hyui", "beds", params)
    return [BedRow.parse_obj(row) for row in rows]


@mock_router.get("/beds/", response_model=list[BedRow])
def get_mock_beds(department: str) -> list[BedRow]:
    return [
        BedRow(
            location_string="location_a",
            bed_functional=[{"id": 1, "value": "Option", "color": "light-blue"}],
            bed_physical=[{"id": 1, "value": "Option", "color": "light-blue"}],
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
    params = urlencode({"departments": department})
    return f"/census/?{params}"


@mock_router.get("/census/", response_model=list[CensusRow])
def get_mock_census(department: str) -> list[CensusRow]:
    return [
        CensusRow(
            encounter=1013378594,
            location_string="location_a",
            date_of_birth=date(2001, 2, 3),
            mrn="abc",
            firstname="Santa",
            lastname="Claus",
            modified_at=datetime(2022, 1, 2, 3, 4),
            location_id=2,
            department="My Department",
        )
    ]


@mock_router.get("/live/{ward}/ui/", response_model=list[SitrepRow])
def get_mock_live_ui(ward: str) -> list[SitrepRow]:
    engine = create_engine(f"sqlite:///{Path(__file__).parent}/mock.db", future=True)

    with Session(engine) as session:
        result = session.execute("SELECT * FROM sitrep")
        return [SitrepRow.parse_obj(row) for row in result]


@router.get("/live/{ward}/ui/", response_model=list[SitrepRow])
def get_live_ui(
    ward: str, settings: Settings = Depends(get_settings)
) -> list[SitrepRow]:
    response = requests.get(f"{settings.hycastle_url}/live/icu/{ward}/ui")
    rows = response.json()["data"]
    return [SitrepRow.parse_obj(row) for row in rows]


@router.patch("/beds")
def update_bed_row(
    table_id: int, row_id: int, data: dict, settings: Settings = Depends(get_settings)
) -> None:
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
    "/predictions/discharge/individual/{ward}/",
    response_model=list[IndividualDischargePrediction],
)
def get_individual_discharge_predictions(
    ward: str, settings: Settings = Depends(get_settings)
) -> list[IndividualDischargePrediction]:
    response = requests.get(
        f"{settings.hymind_url}/predictions/icu/discharge", params={"ward": ward}
    )
    rows = response.json()["data"]
    return [IndividualDischargePrediction.parse_obj(row) for row in rows]


@mock_router.get(
    "/predictions/discharge/individual/{ward}/",
    response_model=list[IndividualDischargePrediction],
)
def get_mock_individual_discharge_predictions(
    ward: str,
) -> list[IndividualDischargePrediction]:
    return [IndividualDischargePrediction(episode_slice_id=1, prediction_as_real=0.4)]
