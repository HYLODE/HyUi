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
    primary_mrn: str
    patient_key: int
    surgical_case_uclh_key: int
    surgical_case_epic_id: int
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
    primary_anesthesia_type: str | None
    reason_not_performed: str | None
    canceled: bool | None
    planned_operation_start_instant: datetime
    planned_operation_end_instant: datetime
    touch_time_start_instant: datetime | None
    touch_time_end_instant: datetime | None
    touch_time_minutes: float | None
    post_operative_destination: str
    admission_service: str | None
    elective_admission_type: str | None
    intended_management: str | None
    priority: str | None
    removal_reason: str | None
    status: str | None
    surgical_service: str | None
    type: str | None
    count: str | None
    case_schedule_status: str | None
    case_cancel_reason: str | None
    case_cancel_reason_code: str | None
    asa_rating_code: str | None
    name: str | None
    patient_friendly_name: str | None
    room_name: str | None
    department_name: str | None
    booked_destination: str | None
    pacu: int | None


class PreassessData(CabData):
    creation_instant: datetime
    type: str | None
    author_type: str | None
    string_value: str | None
    numeric_value: float | None
    date_value: datetime | None
    smart_data_element_epic_id: str | None
    name: str | None
    abbreviation: str | None
    data_type: str | None
    concept_type: str | None
    concept_value: str | None  # TODO: FIX float ideally


class LabData(CabData):
    name: str
    planned_operation_start_instant: datetime
    value: float | str | None
    result_instant: datetime


class MergedData(CabData):
    primary_mrn: str
    surgical_case_uclh_key: str
    first_name: str
    last_name: str
    birth_date: date
    age_in_years: int
    sex: str
    surgery_date: date
    cancel_date: date | None
    primary_service: str
    classification: str | None
    admission_patient_class: str
    primary_anesthesia_type: str | None
    canceled: bool | None
    planned_operation_start_instant: datetime
    planned_operation_end_instant: datetime
    intended_management: str | None
    urgency: str | None
    priority: str | None
    patient_friendly_name: str | None
    department_name: str | None
    room_name: str | None
    preassess_date: date | None
    pac_dr_review: str | None
    pac_nursing_outcome: str | None
    pac_nursing_issues: str | None
    display_string: str | None
    mets: int | None
    anaesthetic_alert: int | None
    asa_rating_code: str | None
    asa: int | None
    prioritisation: str | None
    num_echo: int | None
    abnormal_echo: int | None
    last_echo_date: date | None
    last_echo_narrative: str | None
    bmi_max_value: float | None
    protocolised_adm: str | None
    post_operative_destination: str
    pod_orc: str | None
    pacdest: str | None
    booked_destination: str | None
    pacu: bool | None
    icu_prob: float | None


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
    finalizing_date_key: int
    date_value: date
    is_abnormal: bool
    planned_operation_start_instant: datetime
    touch_time_start_instant: datetime | None


class ObsData(CabData):
    planned_operation_start_instant: datetime
    value: str
    numeric_value: float | None
    first_documented_instant: datetime
    taken_instant: datetime
    display_name: str


class AxaCodes(BaseModel):
    surgical_service: str | None
    name: str | None
    axa_name: str | None
    axa_severity: str | None
    protocolised_adm: str | None

    class Config:
        alias_generator = _to_camel
        allow_population_by_field_name = True


class PreassessSummaryData(CabData):
    creation_instant: datetime | None
    string_value: str | None
    line_num: int | None
    name: str | None


class MedicalHx(CabData):
    value: str | None
    display_string: str | None
