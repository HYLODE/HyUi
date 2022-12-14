from typing import Any

from fastapi import APIRouter

router = APIRouter(
    prefix="/bedbones",
)

mock_router = APIRouter(
    prefix="/bedbones",
)


@mock_router.get("/beds/")
def get_mock_beds() -> dict[str, Any]:
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
                    "gynaecology - general __ uch t06"
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
