from fastapi import APIRouter

from models.beds import Bed

router = APIRouter(
    prefix="/beds",
)

mock_router = APIRouter(
    prefix="/beds",
)


@mock_router.get("/", response_model=list[Bed])
def get_mock_beds(ward: str) -> list[Bed]:
    return [
        Bed(location_string="LOC1", room="ROOM1", bed="BED1", closed=False, covid=True),
        Bed(location_string="LOC1", room="ROOM1", bed="BED2", closed=True, covid=False),
    ]


@router.get("/", response_model=list[Bed])
def get_beds(ward: str) -> list[Bed]:
    pass

    # API_URL = f"{BASEROW_API_URL}/database/rows/table/261/"
    #
    # try:
    #     response = requests.get(
    #         url=API_URL,
    #         params={
    #             "user_field_names": "true",
    #             "filter__field_2051__equal": ward_radio_value,
    #             "include": (
    #                 "location_id,location_string,closed,unit_order,"
    #                 "DepartmentName,room,bed,bed_physical,"
    #                 "bed_functional,covid,LocationName"
    #             ),
    #             "include": (
    #                 "location_id,location_string,closed,unit_order,"
    #                 "DepartmentName,room,bed,bed_physical,"
    #                 "bed_functional,covid,LocationName"
    #             ),
    #         },
    #         headers={
    #             "Authorization": f"Token {settings.BASEROW_READWRITE_TOKEN}",
    #         },
    #     )
    # except requests.exceptions.RequestException:
    #     warnings.warn("HTTP Request failed")
