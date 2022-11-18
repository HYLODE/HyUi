from datetime import datetime, date

from pydantic import BaseModel


class EmergencyDepartmentPatient(BaseModel):
    arrival_datetime: datetime
    bed: str
    mrn: str
    name: str
    sex: str
    date_of_birth: date
    admission_probability: float | None
    next_location: str | None


class AggregateAdmissionRow(BaseModel):
    speciality: str

    beds_allocated: int
    """How many patients currently in ED have specific inpatient beds
    allocated.
    """

    beds_not_allocated: int
    """How many patients currently in ED have inpatient bed requests but do not
     actually have a bed allocated.
     """

    without_decision_to_admit_seventy_percent: int
    """How many patients are likely to be admitted to the hospital from ED.
    This number has a 70% or more probability of being accurate. This also
    excludes all patients currently in ED that already have a decision to be
    admitted.
    """

    without_decision_to_admit_ninety_percent: int
    """How many patients are likely to be admitted to the hospital from ED.
    This number has a 90% or more probability of being accurate. This also
    excludes all patients currently in ED that already have a decision to be
    admitted.
    """

    yet_to_arrive_seventy_percent: int
    """How many patients yet to arrive in ED are likely to be admitted in the
    next period of time with a 70% or more probability of being accurate.
    """

    yet_to_arrive_ninety_percent: int
    """How many patients yet to arrive in ED are likely to be admitted in the
    next period of time with a 90% or more probability of being accurate.
    """
