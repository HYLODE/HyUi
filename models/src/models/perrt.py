"""
data model for live PERRT query
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


def _to_camel(member: str) -> str:
    return "".join(word.capitalize() for word in member.split("_"))


class EmapCpr(BaseModel):
    """
    Advance Decisions and CPR
    """

    advance_decision_id: int
    requested_datetime: datetime
    status_change_datetime: datetime
    care_code: str
    name: str
    cancelled: bool
    closed_due_to_discharge: bool
    hospital_visit_id: int
    encounter: str


class EmapConsults(BaseModel):
    """
    Consults and Consult type
    """

    consultation_request_id: int
    scheduled_datetime: datetime
    status_change_datetime: datetime
    hospital_visit_id: int
    encounter: str
    code: str
    name: Optional[str]


class EmapVitalsLong(BaseModel):
    """
    vital signs extracted from the visit observation table
    use hospital_visit_id as the key to link against beds
    """

    visit_observation_id: int
    hospital_visit_id: int
    encounter: str
    observation_datetime: datetime
    id_in_application: str
    value_as_real: Optional[float]
    value_as_text: Optional[str]
    unit: Optional[str]


class EmapVitalsWide(BaseModel):
    """
    vital signs wrangled to one row per encounter by summarising over the
    window period
    """

    # patient level fields
    hospital_visit_id: str
    encounter: str
    # observation level fields collapsed to per patient
    air_or_o2_max: Optional[float]
    air_or_o2_min: Optional[float]
    avpu_max: Optional[float]
    avpu_min: Optional[float]
    bp_max: Optional[float]
    bp_min: Optional[float]
    news_scale_1_max: Optional[float]
    news_scale_1_min: Optional[float]
    news_scale_2_max: Optional[float]
    news_scale_2_min: Optional[float]
    pulse_max: Optional[float]
    pulse_min: Optional[float]
    resp_max: Optional[float]
    resp_min: Optional[float]
    spo2_max: Optional[float]
    spo2_min: Optional[float]
    temp_max: Optional[float]
    temp_min: Optional[float]


# class AdmissionPrediction(BaseModel):
#     hospital_visit_id: str
#     admission_probability: Optional[float]
