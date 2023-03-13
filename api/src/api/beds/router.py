import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Response
from pathlib import Path

from api.logger import logger, logger_timeit
from api.baserow import BaserowDB, get_baserow_db
from api.config import Settings, get_settings
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
@logger_timeit()
def get_departments(baserow: BaserowDB = Depends(get_baserow_db)) -> list[Department]:
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    rows = baserow.get_rows("departments", params)

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
@logger_timeit()
def get_rooms(baserow: BaserowDB = Depends(get_baserow_db)) -> list[Room]:
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    rows = baserow.get_rows("rooms", params)

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
@logger_timeit()
def get_beds(
    response: Response,
    departments: list[str] = Query(default=[]),
    locations: list[str] = Query(default=[]),
    baserow: BaserowDB = Depends(get_baserow_db),
) -> list[Bed]:
    response.headers["Cache-Control"] = "public, max-age=300"

    field_ids = baserow.get_fields("beds")
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    if len(departments) or len(locations):
        rows = []
        for department in departments:
            department_field_id = field_ids["department"]
            params[f"filter__field_{department_field_id}__equal"] = department
            rows.extend(baserow.get_rows("beds", params))
            params.pop(f"filter__field_{department_field_id}__equal")

        for location in locations:
            location_string_field_id = field_ids["location_string"]
            params[f"filter__field_{location_string_field_id}__equal"] = location
            rows.extend(baserow.get_rows("beds", params))
            params.pop(f"filter__field_{location_string_field_id}__equal")

    else:
        # get everything
        rows = baserow.get_rows("beds", params)

    # drop baserow id and order fields
    for row in rows:
        row.pop("id")
        row.pop("order")

    logger.info(f"Returning {len(rows)} beds")
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
@logger_timeit()
def get_campus(
    response: Response,
    campuses: list[str] = Query(default=[]),
    baserow: BaserowDB = Depends(get_baserow_db),
) -> list[Bed]:
    response.headers["Cache-Control"] = "public, max-age=300"
    departments: list = []
    for campus in campuses:
        departments.extend(CAMPUSES.get(campus, []))

    locations: list = []
    for department in departments:
        if missing_locations := MISSING_DEPARTMENT_LOCATIONS.get(department):
            locations.extend(missing_locations)

    field_ids = baserow.get_fields("beds")
    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
    }

    if len(departments) or len(locations):
        rows = []
        for department in departments:
            department_field_id = field_ids["department"]
            params[f"filter__field_{department_field_id}__equal"] = department
            rows.extend(baserow.get_rows("beds", params))
            params.pop(f"filter__field_{department_field_id}__equal")

        for location in locations:
            location_string_field_id = field_ids["location_string"]
            params[f"filter__field_{location_string_field_id}__equal"] = location
            rows.extend(baserow.get_rows("beds", params))
            params.pop(f"filter__field_{location_string_field_id}__equal")

    else:
        # get everything
        rows = baserow.get_rows("beds", params)

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
@logger_timeit()
def get_closed_beds(baserow: BaserowDB = Depends(get_baserow_db)) -> list[Bed]:
    field_ids = baserow.get_fields("beds")

    closed_field_id = field_ids["closed"]

    params = {
        "size": 200,  # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{closed_field_id}__boolean": True,
    }

    rows = baserow.get_rows("beds", params)
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
@logger_timeit()
def post_discharge_status(
    csn: int, status: str, baserow: BaserowDB = Depends(get_baserow_db)
) -> DischargeStatus:
    params = {"user_field_names": True}

    payload = {
        "csn": csn,
        "status": status,
        "modified_at": datetime.utcnow().isoformat(),
    }

    result = baserow.post_row(
        "discharge_statuses",
        params=params,
        payload=payload,
    )

    output = DischargeStatus.parse_obj(result)  # type: DischargeStatus
    return output


@mock_router.get("/discharge_status/", response_model=list[DischargeStatus])
def get_mock_discharge_status(
    delta_hours: int = 72,
    baserow: BaserowDB = Depends(get_baserow_db),
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
@logger_timeit()
def get_discharge_status(
    delta_hours: int = 72, baserow: BaserowDB = Depends(get_baserow_db)
) -> list[DischargeStatus]:
    _table = "discharge_statuses"

    field_ids = baserow.get_fields(_table)

    modified_at_field_id = field_ids["modified_at"]
    horizon = (datetime.utcnow() - timedelta(hours=float(delta_hours))).isoformat()

    params = {
        "size": 200,
        # The maximum size of a page.
        "user_field_names": "true",
        f"filter__field_{modified_at_field_id}__date_after": horizon,
    }

    rows = baserow.get_rows(_table, params)
    return [DischargeStatus.parse_obj(row) for row in rows]
