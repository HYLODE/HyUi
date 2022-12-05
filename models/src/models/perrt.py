"""
data model for live PERRT query
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


def _to_camel(member: str) -> str:
    return "".join(word.capitalize() for word in member.split("_"))


class EmapVitals(BaseModel):
    """
    vital signs extracted from the visit observation table
    use hospital_visit_id as the key to link against beds
    """

    visit_observation_id: int
    hospital_visit_id: int
    encounter: int
    observation_datetime: datetime
    id_in_application: str
    value_as_real: Optional[float]
    value_as_text: Optional[str]
    unit: Optional[str]


# define the data model that you're expecting from your query
# class PerrtLong(BaseModel):
#     """
#     Raw data
#     Perrt class to hold data returned from the Perrt query
#     the SQL query that runs against EMAP etc
#     One row per visit observation (hence _long_)
#     """
#
#     # patient level fields
#     mrn: str
#     lastname: str
#     firstname: str
#     sex: str
#     date_of_birth: date
#     # visit level fields
#     perrt_consult_datetime: datetime
#     bed_admit_dt: datetime
#     dept_name: str
#     room_name: str
#     bed_hl7: str
#     hospital_visit_id: int
#     # observation level fields
#     visit_observation_id: int
#     observation_datetime: datetime
#     id_in_application: int
#     value_as_real: Optional[float]
#     value_as_text: Optional[str]
#     unit: Optional[str]
#
#
# class PerrtWide(BaseModel):
#     """
#     Wrangled data
#     Perrt class to hold data returned from the Perrt query
#     the SQL query or the API
#     """
#
#     # patient level fields
#     mrn: str
#     hospital_visit_id: str
#     lastname: str
#     firstname: str
#     sex: str
#     date_of_birth: date
#     bed_admit_dt: datetime
#     dept_name: str
#     room_name: str
#     bed_hl7: str
#     perrt_consult_datetime: object
#     # observation level fields collapsed to per patient
#     air_or_o2_max: Optional[float]
#     air_or_o2_min: Optional[float]
#     avpu_max: Optional[float]
#     avpu_min: Optional[float]
#     bp_max: Optional[float]
#     bp_min: Optional[float]
#     news_scale_1_max: Optional[float]
#     news_scale_1_min: Optional[float]
#     news_scale_2_max: Optional[float]
#     news_scale_2_min: Optional[float]
#     pulse_max: Optional[float]
#     pulse_min: Optional[float]
#     resp_max: Optional[float]
#     resp_min: Optional[float]
#     spo2_max: Optional[float]
#     spo2_min: Optional[float]
#     temp_max: Optional[float]
#     temp_min: Optional[float]
#
#
# class AdmissionPrediction(BaseModel):
#     hospital_visit_id: str
#     admission_probability: Optional[float]
