from fastapi import APIRouter, Depends

from api.baserow import get_fields, get_rows
from api.config import get_settings, Settings
from models.beds import Bed

router = APIRouter(
    prefix="/beds",
)

mock_router = APIRouter(
    prefix="/beds",
)


@mock_router.get("/", response_model=list[Bed])
def get_mock_beds(department: str) -> list[Bed]:
    return [
        Bed(location_string="LOC1", room="ROOM1", closed=False, covid=True),
        Bed(location_string="LOC1", room="ROOM1", closed=True, covid=False),
    ]


@router.get("/", response_model=list[Bed])
def get_beds(department: str, settings: Settings = Depends(get_settings)) -> list[Bed]:

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
    return [Bed.parse_obj(row) for row in rows]
