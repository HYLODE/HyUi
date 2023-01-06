"""
Results from Electives Query
eg.

The developer should specify the data models here
and follow the **same** naming convention such that
the module.classname can be reliably used for access
"""

from datetime import datetime, date, time

from pydantic import BaseModel


def _to_camel(member: str) -> str:
    return "".join(word.capitalize() for word in member.split("_"))


class CabData(BaseModel):
    patient_durable_key: int
    surgical_case_key: int | None

    class Config:
        alias_generator = _to_camel
        allow_population_by_field_name = True


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


class SurgData(CabData):
    primary_mrn: int
    patient_key: int
    surgical_case_uclh_key: int
    first_name: str
    last_name: str
    birth_date: date
    age_in_years: int
    sex: str
    placed_on_waiting_list_date: date | None
    decided_to_admit_date: date | None
    surgery_date: date
    case_request_date: date
    case_request_time_of_day: time
    cancel_date: date | None
    primary_service: str
    procedure_level: str | None
    classification: str | None
    surgery_patient_class: str
    admission_patient_class: str
    primary_anaesthesia_type: str | None
    reason_not_performed: str | None
    canceled: bool | None
    planned_operation_start_instant: datetime | None
    planned_operation_end_instant: datetime | None
    touch_time_start_instant: datetime | None
    touch_time_end_instant: datetime | None
    touch_time_minutes: float | None
    post_operative_destination: str
    admission_service: str | None
    elective_admission_type: str
    intended_management: str
    priority: str | None
    removal_reason: str | None
    status: str | None
    surgical_service: str | None
    type: str | None  # TODO: FIX RISK - DUPLICATED NAME
    count: str | None
    case_schedule_status: str | None
    case_cancel_reason: str | None
    case_cancel_reason_code: str | None
    asa_rating_code: str | None
    name: str | None  # TODO: FIX RISK - DUPLICATED NAME
    patient_friendly_name: str | None
    room_name: str | None
    department_name: str | None
    booked_destination: str | None
    pacu: int | None


class PreassessData(CabData):
    creation_instant: datetime
    type: str | None  # TODO: FIX RISK - DUPLICATED NAME
    author_type: str | None
    string_value: str | None
    numeric_value: float | None
    date_value: datetime | None
    smart_data_element_epic_id: str | None
    name: str | None  # TODO: FIX RISK - DUPLICATED NAME
    abbreviation: str | None
    data_type: str | None
    concept_type: str | None
    concept_value: str | None  # TODO: FIX float ideally


class LabData(CabData):
    name: str
    planned_operation_start_instant: datetime
    value: float
    result_instant: datetime


class MergedData(SurgData):
    #  cardio: int | None ## TODO: FIX cardio does not appear. wrangle. preassess error.
    resp: int | None
    airway: int | None
    infectious: int | None
    endo: int | None
    neuro: int | None
    haem: int | None
    renal: int | None
    gastro: int | None
    cpet: int | None
    mets: int | None
    anaesthetic_alert: int | None
    asa: int | None
    c_line: int | None
    a_line: int | None
    expected_stay: str | None
    urgency: str | None
    pacdest: str | None
    prioritisation: str | None
    preassess_date: date | None
    na_abnormal_count: float | None
    crp_abnormal_count: float | None
    inr_last_value: float | None
    na_max_value: float | None
    simple_score: float | None
    echo_performed: bool | None
    echo_abnormal: bool | None
    sys_bp_abnormal_count: int | None
    dias_bp_abnormal_count: int | None
    pulse_measured_count: int | None
    bmi_max_value: float | None


class EchoData(CabData):
    imaging_key: int
    finding_type: str | None
    finding_name: str | None
    string_value: str | None
    numeric_value: float | None
    unit: str | None
    echo_start_date: date
    echo_finalised_date: date
    planned_operation_start_instant: datetime


class EchoWithAbnormalData(CabData):
    imaging_key: int
    narrative: str
    finalizing_date_key: date
    date_value: date
    is_abnormal: bool
    planned_operation_start_instant: datetime
    touch_time_start_instant: datetime


class ObsData(CabData):
    planned_operation_start_instant: datetime
    value: str
    numeric_value: float | None
    first_documented_instant: datetime
    taken_instant: datetime
    display_name: str
