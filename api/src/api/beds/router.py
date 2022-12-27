import json
from datetime import datetime
from fastapi import APIRouter, Depends
from pathlib import Path

from api.baserow import get_fields, get_rows, post_row
from api.config import Settings, get_settings
from models.beds import Bed, DischargeStatus

router = APIRouter(
    prefix="/beds",
)

mock_router = APIRouter(
    prefix="/beds",
)


@mock_router.get("/", response_model=list[Bed])
def get_mock_beds(department: str) -> list[Bed]:
    # FIXME: dependency between initialise and api modules
    with open(
        Path(__file__).parents[4]
        / "initialise"
        / "src"
        / "initialise"
        / "bed_defaults.json",
        "r",
    ) as f:
        rows = json.load(f)
    # mock return just T03 beds
    _FILTER = "T03"
    rows = [row for row in rows if _FILTER in row["location_string"]]
    return [Bed.parse_obj(row).dict() for row in rows]


@router.get("/", response_model=list[Bed])
def get_beds(department: str, settings: Settings = Depends(get_settings)) -> list[Bed]:
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    field_ids = get_fields(baserow_url, email, password, "hyui", "beds")

    department_field_id = field_ids["department"]

    params = {
        "size": 200,
        # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{department_field_id}__equal": department,
    }

    rows = get_rows(baserow_url, email, password, "hyui", "beds", params)
    return [Bed.parse_obj(row) for row in rows]


@mock_router.get("/closed/", response_model=list[Bed])
def get_mock_closed_beds() -> list[Bed]:
    return [
        Bed(location_string="LOC1", closed=True, covid=True, xpos=100, ypos=100),
        Bed(location_string="LOC1", closed=True, covid=False, xpos=100, ypos=100),
    ]


@router.get("/closed/", response_model=list[Bed])
def get_closed_beds(settings=Depends(get_settings)) -> list[Bed]:
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    field_ids = get_fields(baserow_url, email, password, "hyui", "beds")

    closed_field_id = field_ids["closed"]

    params = {
        "size": 200,
        # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{closed_field_id}__boolean": True,
    }

    rows = get_rows(baserow_url, email, password, "hyui", "beds", params)
    return [Bed.parse_obj(row) for row in rows]


@mock_router.post("/discharge_status/", response_model=DischargeStatus)
def post_mock_discharge_status(
    csn: int, status: str, settings=Depends(get_settings)
) -> DischargeStatus:
    # this function depends on having a local instance of baserow running
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    params = {"user_field_names": True}

    csn = 123 if not csn else csn
    status = "ready" if not status else status

    payload = {
        "csn": csn,
        "status": status,
        "modified_at": datetime.utcnow().isoformat(),
    }

    result = post_row(
        baserow_url,
        email,
        password,
        "hyui",
        "discharge_statuses",
        params=params,
        payload=payload,
    )

    return DischargeStatus.parse_obj(result)


@router.post("/discharge_status/", response_model=DischargeStatus)
def post_discharge_status(
    csn: int, status: str, settings=Depends(get_settings)
) -> DischargeStatus:
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    params = {"user_field_names": True}

    payload = {
        "csn": csn,
        "status": status,
        "modified_at": datetime.utcnow().isoformat(),
    }

    result = post_row(
        baserow_url,
        email,
        password,
        "hyui",
        "discharge_statuses",
        params=params,
        payload=payload,
    )

    return DischargeStatus.parse_obj(result)
