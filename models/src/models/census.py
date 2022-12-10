from datetime import date, datetime

from pydantic import BaseModel


class CensusRow(BaseModel):

    modified_at: datetime
    location_id: int
    department: str
    location_string: str

    ovl_admission: datetime | None
    ovl_hv_id: int | None
    open_visits_n: int | None

    cvl_admission: datetime | None
    cvl_discharge: datetime | None
    cvl_hv_id: int | None

    ovl_ghost: bool | None
    occupied: bool | None

    patient_class: str | None

    mrn: str | None
    encounter: str | None
    date_of_birth: date | None
    lastname: str | None
    firstname: str | None
    sex: str | None

    planned_move: str | None
    pm_datetime: datetime | None
    pm_type: str | None
    pm_dept: str | None
    pm_location_string: str | None


class CensusDepartment(BaseModel):
    department: str
    beds: int
    patients: int
    empties: int
    days_since_last_dc: int
    closed_temp: bool
    closed_perm: bool | None
    modified_at: datetime


class ClosedBed(BaseModel):
    department: str
    closed: bool


class CensusBed(BaseModel):
    """Bed model as defined in baserow"""

    id: int
    order: int
    location_string: str
    location_id: int
    department_id: int
    room_id: int
    bed_id: int
    department: str
    speciality: str
    room: str
    dept: int
    room_hl7: str
    bed: str
    # loc2merge: "critical care - gwb l01 icu __ gwb l01 critical care __ sr04 __ sr04-04",
    DepartmentKey: int
    BedEpicId: int
    Name: str
    DepartmentName: str
    RoomName: str
    BedName: str
    IsBed: bool
    BedInCensus: bool
    IsDepartment: bool
    IsRoom: bool
    IsCareArea: bool
    DepartmentExternalName: str
    DepartmentSpecialty: str
    DepartmentType: str
    DepartmentServiceGrouper: str
    DepartmentLevelOfCareGrouper: str
    LocationName: str
    ParentLocationName: str
    _CreationInstant: datetime
    _LastUpdatedInstant: datetime
    # _merge: "both",
    unit_order: int
    closed: bool
    covid: bool
    # DischargeReady: str
    bed_physical: list[dict]
    # "bed_physical": [
    #     {
    #         "id": 981,
    #         "value": "sideroom",
    #         "color": "dark-red"
    #     }
    # ],
    bed_functional: list[dict]
    # "bed_functional": [
    #     {
    #         "id": 986,
    #         "value": "ficm",
    #         "color": "dark-green"
    #     },
    #     {
    #         "id": 987,
    #         "value": "gwb",
    #         "color": "light-orange"
    #     }
    # ],
