import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Response
from pathlib import Path

from api.baserow import BaserowAuthenticator
from api.config import Settings, get_settings
from api.utils import Timer
from api.wards import (
    CAMPUSES,
    MISSING_DEPARTMENT_LOCATIONS,
)
from models.beds import Bed, Department, DischargeStatus, Room

router = APIRouter(
    prefix="/baserow",
)

mock_router = APIRouter(
    prefix="/baserow",
)


@mock_router.get("/departments", response_model=list[Department])
def get_mock_departments() -> list[Department]:
    with open(Path(__file__).parent / "department_defaults.json", "r") as f:
        rows = json.load(f)
    return [Department.parse_obj(row) for row in rows]


@router.get("/departments", response_model=list[Department])
def get_departments(settings: Settings = Depends(get_settings)) -> list[Department]:
    baserow_auth = BaserowAuthenticator(
        settings.baserow_url,
        settings.baserow_email,
        settings.baserow_password.get_secret_value(),
    )
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    rows = baserow_auth.get_rows("hyui", "departments", params)

    # drop baserow id and order fields
    for row in rows:
        row.pop("id")
        row.pop("order")

    return [Department.parse_obj(row) for row in rows]


@mock_router.get("/rooms", response_model=list[Room])
def get_mock_rooms() -> list[Room]:
    with open(Path(__file__).parent / "room_defaults.json", "r") as f:
        rows = json.load(f)
    return [Room.parse_obj(row) for row in rows]


@router.get("/rooms", response_model=list[Room])
def get_rooms(settings: Settings = Depends(get_settings)) -> list[Room]:
    baserow_auth = BaserowAuthenticator(
        settings.baserow_url,
        settings.baserow_email,
        settings.baserow_password.get_secret_value(),
    )
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    rows = baserow_auth.get_rows("hyui", "rooms", params)

    # drop baserow id and order fields
    for row in rows:
        row.pop("id")
        row.pop("order")

    return [Room.parse_obj(row) for row in rows]


@mock_router.get("/beds", response_model=list[Bed])
def get_mock_beds(
    response: Response,
    departments: list[str] = Query(default=[]),
    locations: list[str] = Query(default=[]),
) -> list[Bed]:
    response.headers["Cache-Control"] = "public, max-age=300"
    with open(Path(__file__).parent / "bed_defaults.json", "r") as f:
        rows = json.load(f)

    if len(departments):
        rows = [row for row in rows if row.get("department") in departments]
    if len(locations):
        rows = [row for row in rows if row.get("location_string") in locations]

    return [Bed.parse_obj(row) for row in rows]


@router.get("/beds", response_model=list[Bed])
def get_beds(
    departments: list[str] = Query(default=[]),
    locations: list[str] = Query(default=[]),
    settings: Settings = Depends(get_settings),
) -> list[Bed]:
    baserow_auth = BaserowAuthenticator(
        settings.baserow_url,
        settings.baserow_email,
        settings.baserow_password.get_secret_value(),
    )
    field_ids = baserow_auth.get_fields("hyui", "beds")
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    if len(departments) or len(locations):
        rows = []
        for department in departments:
            department_field_id = field_ids["department"]
            params[f"filter__field_{department_field_id}__equal"] = department
            rows.extend(baserow_auth.get_rows("hyui", "beds", params))
            params.pop(f"filter__field_{department_field_id}__equal")

        for location in locations:
            location_string_field_id = field_ids["location_string"]
            params[f"filter__field_{location_string_field_id}__equal"] = location
            rows.extend(baserow_auth.get_rows("hyui", "beds", params))
            params.pop(f"filter__field_{location_string_field_id}__equal")

    else:
        # get everything
        rows = baserow_auth.get_rows("hyui", "beds", params)

    # drop baserow id and order fields
    for row in rows:
        row.pop("id")
        row.pop("order")

    return [Bed.parse_obj(row) for row in rows]


@mock_router.get("/campus", response_model=list[Bed])
def get_mock_campus(
    campuses: list[str] = Query(default=[]),
) -> list[Bed]:
    departments: list = []
    for campus in campuses:
        departments.extend(CAMPUSES.get(campus, []))

    locations: list = []
    for department in departments:
        if missing_locations := MISSING_DEPARTMENT_LOCATIONS.get(department):
            locations.extend(missing_locations)

    with open(Path(__file__).parent / "bed_defaults.json", "r") as f:
        rows = json.load(f)

    all_rows = []
    if len(departments):
        drows = [row for row in rows if row.get("department") in departments]
        all_rows.extend(drows)
    if len(locations):
        lrows = [row for row in rows if row.get("location_string") in locations]
        all_rows.extend(lrows)

    return [Bed.parse_obj(row) for row in all_rows]


@router.get("/campus", response_model=list[Bed])
def get_campus(
    campuses: list[str] = Query(default=[]),
    settings: Settings = Depends(get_settings),
) -> list[Bed]:
    baserow_auth = BaserowAuthenticator(
        settings.baserow_url,
        settings.baserow_email,
        settings.baserow_password.get_secret_value(),
    )
    departments: list = []
    for campus in campuses:
        departments.extend(CAMPUSES.get(campus, []))

    locations: list = []
    for department in departments:
        if missing_locations := MISSING_DEPARTMENT_LOCATIONS.get(department):
            locations.extend(missing_locations)

    field_ids = baserow_auth.get_fields("hyui", "beds")
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    if len(departments) or len(locations):
        rows = []
        for department in departments:
            department_field_id = field_ids["department"]
            params[f"filter__field_{department_field_id}__equal"] = department
            rows.extend(baserow_auth.get_rows("hyui", "beds", params))
            params.pop(f"filter__field_{department_field_id}__equal")

        for location in locations:
            location_string_field_id = field_ids["location_string"]
            params[f"filter__field_{location_string_field_id}__equal"] = location
            rows.extend(baserow_auth.get_rows("hyui", "beds", params))
            params.pop(f"filter__field_{location_string_field_id}__equal")

    else:
        # get everything
        rows = baserow_auth.get_rows("hyui", "beds", params)

    # drop baserow id and order fields
    for row in rows:
        row.pop("id")
        row.pop("order")

    return [Bed.parse_obj(row) for row in rows]


@mock_router.get("/closed/", response_model=list[Bed])
def get_mock_closed_beds() -> list[Bed]:
    return [
        Bed(location_string="LOC1", closed=True, covid=True, xpos=100, ypos=100),
        Bed(location_string="LOC1", closed=True, covid=False, xpos=100, ypos=100),
    ]


@router.get("/closed/", response_model=list[Bed])
def get_closed_beds(settings: Settings = Depends(get_settings)) -> list[Bed]:
    baserow_auth = BaserowAuthenticator(
        settings.baserow_url,
        settings.baserow_email,
        settings.baserow_password.get_secret_value(),
    )
    field_ids = baserow_auth.get_fields("hyui", "beds")

    closed_field_id = field_ids["closed"]

    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{closed_field_id}__boolean": True,
    }

    rows = baserow_auth.get_rows("hyui", "beds", params)
    return [Bed.parse_obj(row) for row in rows]


@mock_router.post("/discharge_status/", response_model=DischargeStatus)
def post_mock_discharge_status(
    csn: int, status: str, settings: Settings = Depends(get_settings)
) -> DischargeStatus:
    csn = 123 if not csn else csn
    status = "ready" if not status else status

    return DischargeStatus(
        id=1,
        order=1,
        csn=csn,
        modified_at=datetime.fromisoformat("2023-01-21t23:55:41"),
        status=status,
    )


@router.post("/discharge_status/", response_model=DischargeStatus)
def post_discharge_status(
    csn: int, status: str, settings: Settings = Depends(get_settings)
) -> DischargeStatus:
    baserow_auth = BaserowAuthenticator(
        settings.baserow_url,
        settings.baserow_email,
        settings.baserow_password.get_secret_value(),
    )
    params = {"user_field_names": True}

    payload = {
        "csn": csn,
        "status": status,
        "modified_at": datetime.utcnow().isoformat(),
    }

    result = baserow_auth.post_row(
        "hyui",
        "discharge_statuses",
        params=params,
        payload=payload,
    )

    output = DischargeStatus.parse_obj(result)  # type: DischargeStatus
    return output


@mock_router.get("/discharge_status/", response_model=list[DischargeStatus])
@Timer(text="Get rows route: Elapsed time: {:.4f}")
def get_mock_discharge_status(
    delta_hours: int = 72, settings: Settings = Depends(get_settings)  # noqa  # noqa
) -> list[DischargeStatus]:
    rows = [
        DischargeStatus(
            id=1,
            order=1,
            csn=123,
            modified_at=datetime.fromisoformat("2023-01-21t23:55:41"),
            status="discharge",
        ),
        DischargeStatus(
            id=2,
            order=2,
            csn=456,
            modified_at=datetime.fromisoformat("2023-01-21t23:55:41"),
            status="review",
        ),
    ]
    return rows


@router.get("/discharge_status/", response_model=list[DischargeStatus])
def get_discharge_status(
    delta_hours: int = 72, settings: Settings = Depends(get_settings)
) -> list[DischargeStatus]:
    baserow_auth = BaserowAuthenticator(
        settings.baserow_url,
        settings.baserow_email,
        settings.baserow_password.get_secret_value(),
    )
    _table = "discharge_statuses"

    field_ids = baserow_auth.get_fields("hyui", _table)

    modified_at_field_id = field_ids["modified_at"]
    horizon = (datetime.utcnow() - timedelta(hours=float(delta_hours))).isoformat()

    params = {
        "size": 200,
        # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{modified_at_field_id}__date_after": horizon,
    }

    rows = baserow_auth.get_rows("hyui", _table, params)
    return [DischargeStatus.parse_obj(row) for row in rows]
