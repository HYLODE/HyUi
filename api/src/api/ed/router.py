from datetime import datetime, date

import pandas as pd
import requests
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.config import get_settings
from api.convert import parse_to_data_frame
from models.ed import EmergencyDepartmentPatient, AggregateAdmissionRow

router = APIRouter(
    prefix="/ed",
)

mock_router = APIRouter(
    prefix="/ed",
)


@mock_router.get("/individual/", response_model=list[EmergencyDepartmentPatient])
def get_mock_individual_admission_rows():
    return [
        EmergencyDepartmentPatient(
            arrival_datetime=datetime(2022, 10, 12, 13, 14),
            bed="BED1",
            mrn="MRNABC",
            name="Name A",
            sex="F",
            date_of_birth=date(1990, 10, 6),
            admission_probability=0.56,
        )
    ]


class Census(BaseModel):
    csn: str
    mrn: str
    name: str
    dob: date
    sex: str
    admission_dt: datetime
    bed_code: str
    bay_code: str
    ward_code: str


def _get_census(hycastle_url: str) -> pd.DataFrame:
    response = requests.get(f"{hycastle_url}/emap/ed/census/ED/")
    return parse_to_data_frame(response.json()["data"], Census)


class Feature(BaseModel):
    episode_slice_id: int
    csn: str


def _get_features(hycastle_url: str) -> pd.DataFrame:
    response = requests.get(f"{hycastle_url}/live/ed/ED/ui")
    return parse_to_data_frame(response.json()["data"], Feature)


class IndividualPrediction(BaseModel):
    episode_slice_id: int
    prediction_as_real: float


def _get_individual_predictions(hymind_url: str) -> pd.DataFrame:
    response = requests.get(f"{hymind_url}/predictions/ed/admissions/individual")
    return parse_to_data_frame(response.json()["data"], IndividualPrediction)


@router.get("/individual/", response_model=list[EmergencyDepartmentPatient])
def get_individual_admission_rows(settings=Depends(get_settings)):
    census_df = _get_census(settings.hycastle_url)
    features_df = _get_features(settings.hycastle_url)
    predictions_df = _get_individual_predictions(settings.hymind_url)

    output_df = pd.merge(census_df, features_df, on="csn", how="left")
    output_df = pd.merge(output_df, predictions_df, on="episode_slice_id", how="left")

    return [
        EmergencyDepartmentPatient.parse_obj(row)
        for row in output_df.to_dict(orient="records")
    ]


@mock_router.get("/aggregate/", response_model=list[AggregateAdmissionRow])
def get_mock_aggregate_admission_rows():
    return [
        AggregateAdmissionRow(
            speciality="medical",
            beds_allocated=5,
            beds_not_allocated=2,
            without_decision_to_admit_seventy_percent=6,
            without_decision_to_admit_ninety_percent=4,
            yet_to_arrive_seventy_percent=10,
            yet_to_arrive_ninety_percent=6,
        )
    ]


@router.get("/aggregate/", response_model=list[AggregateAdmissionRow])
def get_aggregate_admission_rows():
    return [
        AggregateAdmissionRow(
            speciality="medical",
            beds_allocated=5,
            beds_not_allocated=2,
            without_decision_to_admit_seventy_percent=6,
            without_decision_to_admit_ninety_percent=4,
            yet_to_arrive_seventy_percent=10,
            yet_to_arrive_ninety_percent=6,
        )
    ]
