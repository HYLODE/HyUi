import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from pathlib import Path

from api.baserow import get_fields, get_rows, post_row
from api.config import Settings, get_settings
from api.wards import (
    CAMPUSES,
    MISSING_DEPARTMENT_LOCATIONS,
)
from models.beds import Bed, Department, DischargeStatus

router = APIRouter(
    prefix="/beds",
)

mock_router = APIRouter(
    prefix="/beds",
)


@mock_router.get("/departments", response_model=list[Department])
def get_mock_departments() -> list[Department]:
    with open(Path(__file__).parent / "department_defaults.json", "r") as f:
        rows = json.load(f)
    return [Department.parse_obj(row) for row in rows]


@router.get("/departments", response_model=list[Department])
def get_departments(settings: Settings = Depends(get_settings)) -> list[Department]:
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    rows = get_rows(baserow_url, email, password, "hyui", "departments", params)

    # drop baserow id and order fields
    for row in rows:
        row.pop("id")
        row.pop("order")

    return [Department.parse_obj(row) for row in rows]


@mock_router.get("/beds", response_model=list[Bed])
def get_mock_beds(
    departments: list[str] = Query(default=[]),
    locations: list[str] = Query(default=[]),
) -> list[Bed]:
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
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    field_ids = get_fields(baserow_url, email, password, "hyui", "beds")
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    if len(departments) or len(locations):
        rows = []
        for department in departments:
            department_field_id = field_ids["department"]
            params[f"filter__field_{department_field_id}__equal"] = department
            rows.extend(get_rows(baserow_url, email, password, "hyui", "beds", params))
            params.pop(f"filter__field_{department_field_id}__equal")

        for location in locations:
            location_string_field_id = field_ids["location_string"]
            params[f"filter__field_{location_string_field_id}__equal"] = location
            rows.extend(get_rows(baserow_url, email, password, "hyui", "beds", params))
            params.pop(f"filter__field_{location_string_field_id}__equal")

    else:
        # get everything
        rows = get_rows(baserow_url, email, password, "hyui", "beds", params)

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
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    departments: list = []
    for campus in campuses:
        departments.extend(CAMPUSES.get(campus, []))

    locations: list = []
    for department in departments:
        if missing_locations := MISSING_DEPARTMENT_LOCATIONS.get(department):
            locations.extend(missing_locations)

    field_ids = get_fields(baserow_url, email, password, "hyui", "beds")
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    if len(departments) or len(locations):
        rows = []
        for department in departments:
            department_field_id = field_ids["department"]
            params[f"filter__field_{department_field_id}__equal"] = department
            rows.extend(get_rows(baserow_url, email, password, "hyui", "beds", params))
            params.pop(f"filter__field_{department_field_id}__equal")

        for location in locations:
            location_string_field_id = field_ids["location_string"]
            params[f"filter__field_{location_string_field_id}__equal"] = location
            rows.extend(get_rows(baserow_url, email, password, "hyui", "beds", params))
            params.pop(f"filter__field_{location_string_field_id}__equal")

    else:
        # get everything
        rows = get_rows(baserow_url, email, password, "hyui", "beds", params)

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
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()

    field_ids = get_fields(baserow_url, email, password, "hyui", "beds")

    closed_field_id = field_ids["closed"]

    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{closed_field_id}__boolean": True,
    }

    rows = get_rows(baserow_url, email, password, "hyui", "beds", params)
    return [Bed.parse_obj(row) for row in rows]


@mock_router.post("/discharge_status/", response_model=DischargeStatus)
def post_mock_discharge_status(
    csn: int, status: str, settings: Settings = Depends(get_settings)
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
    output = DischargeStatus.parse_obj(result)  # type: DischargeStatus
    return output


@router.post("/discharge_status/", response_model=DischargeStatus)
def post_discharge_status(
    csn: int, status: str, settings: Settings = Depends(get_settings)
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

    output = DischargeStatus.parse_obj(result)  # type: DischargeStatus
    return output


@mock_router.get("/discharge_status/", response_model=list[DischargeStatus])
def get_mock_discharge_status(
    delta_hours: int = 72, settings: Settings = Depends(get_settings)
) -> list[DischargeStatus]:
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()
    _table = "discharge_statuses"

    field_ids = get_fields(baserow_url, email, password, "hyui", _table)

    modified_at_field_id = field_ids["modified_at"]
    horizon = (datetime.utcnow() - timedelta(hours=float(delta_hours))).isoformat()

    params = {
        "size": 200,
        # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{modified_at_field_id}__date_after": horizon,
    }

    rows = get_rows(baserow_url, email, password, "hyui", _table, params)
    return [DischargeStatus.parse_obj(row) for row in rows]


@router.get("/discharge_status/", response_model=list[DischargeStatus])
def get_discharge_status(
    delta_hours: int = 72, settings: Settings = Depends(get_settings)
) -> list[DischargeStatus]:
    baserow_url = settings.baserow_url
    email = settings.baserow_email
    password = settings.baserow_password.get_secret_value()
    _table = "discharge_statuses"

    field_ids = get_fields(baserow_url, email, password, "hyui", _table)

    modified_at_field_id = field_ids["modified_at"]
    horizon = (datetime.utcnow() - timedelta(hours=float(delta_hours))).isoformat()

    params = {
        "size": 200,
        # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{modified_at_field_id}__date_after": horizon,
    }

    rows = get_rows(baserow_url, email, password, "hyui", _table, params)
    return [DischargeStatus.parse_obj(row) for row in rows]
