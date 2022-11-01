from collections import namedtuple
from datetime import date
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from api.config import get_settings
from models.sitrep import (
    SitrepRead,
    SitrepRow,
    IndividualDischargePrediction,
    BedRow,
    CensusRow,
)
from api.db import prepare_query, get_star_session

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


@router.get("/beds/", response_model=list[dict])
def get_beds():
    # TODO: Add these to settings.
    table_id = "261"
    department_field_id = "2041"
    ward = "UCH T03 INTENSIVE CARE"

    return requests.get(
        f"{get_settings().baserow_url}/api/database/rows/table/{table_id}/",
        headers={"Authorization": f"Token {get_settings().baserow_read_write_token}"},
        params={
            "user_field_names": "true",
            f"filter__field_{department_field_id}__equal": ward,
            "include": ",".join(CORE_FIELDS),
        },
    ).json()["results"]


@mock_router.get("/beds/", response_model=list[BedRow])
def get_mock_beds() -> list[BedRow]:
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
        )
    ]


@mock_router.get("/live/{ward}/ui", response_model=list[SitrepRow])
def get_mock_live_ward_ui(ward: str) -> list[SitrepRow]:
    return [
        SitrepRow(
            csn=1,
            episode_slice_id=1,
            n_inotropes_1_4h=2,
            had_rrt_1_4h=True,
            vent_type_1_4h="oxygen",
        )
    ]
    # engine = create_engine(f"sqlite:///{Path(__file__).parent}/mock.db", future=True)
    #
    # query = text("SELECT * FROM sitrep")
    #
    # with Session(engine) as session:
    #     result = session.exec(query)
    #     return [SitrepRow.parse_obj(row) for row in result]


@router.get("/live/{ward}/ui", response_model=list[SitrepRow])
def get_live_ward_ui(ward: str) -> list[SitrepRow]:
    return []


@router.get("/", response_model=list[SitrepRead])
def read_sitrep(session: Session = Depends(get_star_session)):
    """
    Returns Sitrep data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    """
    # TODO: Fix this. Ideally remove prepare_query.
    q = prepare_query("sitrep", "FIX")
    results = session.exec(q)
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


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
