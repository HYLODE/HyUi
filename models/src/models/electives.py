"""
Results from Electives Query
eg.

The developer should specify the data models here
and follow the **same** naming convention such that
the module.classname can be reliably used for access
"""

from datetime import datetime, date

from pydantic import BaseModel


def _to_camel(member: str) -> str:
    return "".join(word.capitalize() for word in member.split("_"))


class CaboodleCaseBooking(BaseModel):
    """
    results of the live_case.sql query against caboodle
    """

    patient_durable_key: int
    primary_mrn: str
    surgical_case_epic_id: int
    canceled: bool
    surgical_service: str | None
    age_in_years: int
    sex: str
    first_name: str
    last_name: str
    room_name: str
    surgery_date: date
    patient_friendly_name: str
    planned_operation_start_instant: datetime

    class Config:
        alias_generator = _to_camel
        # https://stackoverflow.com/a/69434012/992999
        allow_population_by_field_name = True


class ClarityPostopDestination(BaseModel):
    pod_orc: str
    or_case_id: int
    surgery_date_clarity: datetime

    class Config:
        alias_generator = _to_camel
        allow_population_by_field_name = True


class CaboodlePreassessment(BaseModel):
    patient_durable_key: int
    name: str
    creation_instant: datetime
    string_value: str

    class Config:
        alias_generator = _to_camel
        allow_population_by_field_name = True


class ElectiveSurgCase(BaseModel):
    patient_durable_key: int
    primary_mrn: str
    surgical_case_epic_id: int
    canceled: bool
    surgical_service: str | None
    most_recent_pod_dt: datetime | None
    pod_preassessment: str | None
    most_recent_asa: str | None
    most_recent_mets: str | None
    pod_orc: str | None
    or_case_id: str | None
    pacu: bool
    age_in_years: int
    sex: str
    first_name: str
    last_name: str
    room_name: str
    surgery_date: date
    patient_friendly_name: str
    planned_operation_start_instant: datetime