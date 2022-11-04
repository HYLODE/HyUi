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
