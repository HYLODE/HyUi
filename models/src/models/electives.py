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
    PatientDurableKey: int
    SurgicalCaseKey: int | None


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


class SurgData(CabData):
    PrimaryMrn: int
    PatientKey: int
    SurgicalCaseUclhKey: int
    FirstName: str
    LastName: str
    BirthDate: datetime
    AgeInYears: int
    Sex: str
    PlacedOnWaitingListDate: datetime | None
    DecidedToAdmitDate: datetime | None
    SurgeryDate: datetime
    CaseRequestDate: datetime
    CaseRequestTimeOfDay: time
    CancelDate: date | None
    PrimaryService: str
    ProcedureLevel: str | None
    Classification: str | None
    SurgeryPatientClass: str
    AdmissionPatientClass: str
    PrimaryAnesthesiaType: str | None
    ReasonNotPerformed: str | None
    Canceled: bool | None
    PlannedOperationStartInstant: datetime | None
    PlannedOperationEndInstant: datetime | None
    TouchTimeStartInstant: datetime | None
    TouchTimeEndInstant: datetime | None
    TouchTimeMinutes: float | None
    PostOperativeDestination: str
    AdmissionService: str | None
    ElectiveAdmissionType: str
    IntendedManagement: str
    Priority: str | None
    RemovalReason: str | None
    Status: str | None
    SurgicalService: str | None
    Type: str | None  # TODO: FIX RISK - DUPLICATED NAME
    Count: str | None
    CaseScheduleStatus: str | None
    CaseCancelReason: str | None
    CaseCancelReasonCode: str | None
    AsaRatingCode: str | None
    Name: str | None  # TODO: FIX RISK - DUPLICATED NAME
    PatientFriendlyName: str | None
    RoomName: str | None
    DepartmentName: str | None
    booked_destination: str | None
    pacu: int | None


class PreassessData(CabData):
    CreationInstant: datetime
    Type: str | None  # TODO: FIX RISK - DUPLICATED NAME
    AuthorType: str | None
    StringValue: str | None
    NumericValue: float | None
    DateValue: datetime | None
    SmartDataElementEpicId: str | None
    Name: str | None  # TODO: FIX RISK - DUPLICATED NAME
    Abbreviation: str | None
    DataType: str | None
    ConceptType: str | None
    ConceptValue: str | None  # TODO: FIX float ideally


class LabData(CabData):
    Name: str
    PlannedOperationStartInstant: datetime
    Value: float
    ResultInstant: datetime


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
    CPET: int | None
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
    NA_abnormal_count: float | None
    CRP_abnormal_count: float | None
    INR_last_value: float | None
    NA_max_value: float | None
    simple_score: float | None
    EchoPerformed: bool | None
    EchoAbnormal: bool | None
    SYS_BP_abnormal_count: int | None
    DIAS_BP_abnormal_count: int | None
    PULSE_measured_count: int | None
    BMI_max_value: float | None


class EchoData(CabData):
    ImagingKey: int
    FindingType: str | None
    FindingName: str | None
    StringValue: str | None
    NumericValue: float | None
    Unit: str | None
    EchoStartDate: datetime
    EchoFinalisedDate: datetime
    PlannedOperationStartInstant: datetime


class ObsData(CabData):
    PlannedOperationStartInstant: datetime
    Value: str
    NumericValue: float | None
    FirstDocumentedInstant: datetime
    TakenInstant: datetime
    DisplayName: str
