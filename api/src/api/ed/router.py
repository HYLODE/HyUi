from datetime import datetime, date, timedelta
from typing import cast

import pandas as pd
import requests
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.config import get_settings, Settings
from api.convert import parse_to_data_frame, to_data_frame
from api.db import get_star_session
from api.movement import next_locations, NextLocation
from models.ed import EmergencyDepartmentPatient, AggregateAdmissionRow

router = APIRouter(prefix="/ed")

mock_router = APIRouter(prefix="/ed")


@mock_router.get("/individual/", response_model=list[EmergencyDepartmentPatient])
def get_mock_individual_admission_rows() -> list[EmergencyDepartmentPatient]:
    return [
        EmergencyDepartmentPatient(
            arrival_datetime=datetime(2022, 10, 12, 13, 14),
            bed="BED2",
            mrn="MRNABC1",
            name="Donald Trump",
            sex="F",
            date_of_birth=date(1990, 10, 6),
            admission_probability=0.06,
        ),
        EmergencyDepartmentPatient(
            arrival_datetime=datetime(2022, 10, 13, 13, 14),
            bed="BED1",
            mrn="MRNABC2",
            name="Boris Johnson",
            sex="F",
            date_of_birth=date(1990, 10, 6),
            admission_probability=0.26,
        ),
        EmergencyDepartmentPatient(
            arrival_datetime=datetime(2022, 10, 12, 9, 14),
            bed="BED3",
            mrn="MRN12345",
            name="Vladimir Putin",
            sex="F",
            date_of_birth=date(1990, 10, 6),
            admission_probability=0.16,
        ),
    ]


class Census(BaseModel):
    csn: str
    mrn: str
    name: str
    date_of_birth: date = Field(..., alias="dob")
    sex: str
    arrival_datetime: datetime = Field(..., alias="admission_dt")
    bed: str = Field(..., alias="bed_code")
    bay: str = Field(..., alias="bay_code")
    ward: str = Field(..., alias="ward_code")


def _get_census(hycastle_url: str) -> pd.DataFrame:
    response = requests.get(f"{hycastle_url}/emap/ed/census/ED/")
    return parse_to_data_frame(response.json()["data"], Census)


class Feature(BaseModel):
    episode_slice_id: int | None
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


def _set_next_location_text(row: pd.Series) -> str | None:
    if pd.isnull(row["event_datetime"]):
        return None

    if pd.isnull(row["next_location"]):
        return "Possibly Ward"

    return cast(str, row["next_location"])


@router.get("/individual/", response_model=list[EmergencyDepartmentPatient])
def get_individual_admission_rows(
    settings: Settings = Depends(get_settings),
    star_session: Session = Depends(get_star_session),
) -> list[EmergencyDepartmentPatient]:
    census_df = _get_census(settings.hycastle_url)
    features_df = _get_features(settings.hycastle_url)
    predictions_df = _get_individual_predictions(settings.hymind_url)

    csns = census_df["csn"].tolist()
    next_locations_df = to_data_frame(next_locations(star_session, csns), NextLocation)

    output_df = pd.merge(census_df, features_df, on="csn", how="left")
    output_df = pd.merge(output_df, predictions_df, on="episode_slice_id", how="left")
    output_df = pd.merge(output_df, next_locations_df, on="csn", how="left")
    output_df["next_location"] = output_df.apply(
        _set_next_location_text, axis="columns"
    )
    output_df = output_df.rename(
        columns={"prediction_as_real": "admission_probability"}
    )

    return [
        EmergencyDepartmentPatient.parse_obj(row)
        for row in output_df.to_dict(orient="records")
    ]


@mock_router.get("/aggregate/", response_model=list[AggregateAdmissionRow])
def get_mock_aggregate_admission_rows() -> list[AggregateAdmissionRow]:
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


def adjust_for_model_specific_times(t: datetime) -> datetime:
    """
    The current aggregation model only accepts specific times of the day as an
    input parameter. This function rounds down t to the closest acceptable time
    of day.
    """
    t = t.replace(second=0, microsecond=0)

    if t > t.replace(hour=22, minute=30):
        return t.replace(hour=22, minute=30)

    if t > t.replace(hour=15, minute=30):
        return t.replace(hour=15, minute=30)

    if t > t.replace(hour=12, minute=0):
        return t.replace(hour=12, minute=0)

    if t > t.replace(hour=9, minute=30):
        return t.replace(hour=9, minute=30)

    if t > t.replace(hour=6, minute=30):
        return t.replace(hour=6, minute=30)

    return (t - timedelta(days=1)).replace(hour=22, minute=30)


@router.get("/aggregate/", response_model=list[AggregateAdmissionRow])
def get_aggregate_admission_rows(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> list[AggregateAdmissionRow]:
    horizon_dt = datetime.now()

    response = requests.get(
        f"{settings.towermail_url}/aggregations/",
        params={
            "horizon_dt": adjust_for_model_specific_times(horizon_dt),
        },  # type: ignore
    )

    # Use dict({"speciality":row[0]}, **row[1]) to turn
    # {"medical": {"beds_allocated: 2, ...}} into
    # {"specialty": "medical", beds_allocated": 2 ...}.
    return [
        AggregateAdmissionRow.parse_obj(dict({"speciality": row[0]}, **row[1]))
        for row in response.json().items()
    ]
