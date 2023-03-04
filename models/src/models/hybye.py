from datetime import date, datetime

from pydantic import BaseModel


class HospitalFlowRow(BaseModel):
    event_date: date
    count: int


class CensusData(BaseModel):
    location_id: int
    department: str
    location_string: str
    ovl_admission: datetime | None
    ovl_hv_id: int | None
    open_visits_n: int | None
    cvl_admission: datetime | None
    cvl_discharge: datetime | None
    cvl_hv_id: int | None
    ovl_ghost: bool
    occupied: bool
    patient_class: str | None
    mrn: str | None
    lastname: str | None
    firstname: str | None
    date_of_birth: date | None
