from datetime import date, datetime

from pydantic import BaseModel


class HospitalFlowRow(BaseModel):
    event_date: date
    count: int


class CensusData(BaseModel):
    location_id: int
    department: str
    location_string: str
    ovl_admission: datetime
    ovl_hv_id: int
    open_visits_n: int
    cvl_admission: datetime
    cvl_discharge: datetime
    cvl_hv_id: int
    ovl_ghost: bool
    occupied: bool
    patient_class: str
    mrn: str
    lastname: str
    firstname: str
    date_of_birth: datetime
