import logging

import datetime
import pandas as pd
import pytz  # type: ignore
import requests
from fastapi import APIRouter, Depends, Query, Response
from pathlib import Path

from api.config import Settings, get_settings
from api.validate import pydantic_dataframe
from models.hymind import ElTap, EmElTapPostBody, EmTap, IcuDischarge

MOCK_ICU_DISCHARGE_DATA = (
    Path(__file__).resolve().parent / "data" / "mock_icu_discharge.json"
)
MOCK_TAP_EMERGENCY_DATA = (
    Path(__file__).resolve().parent / "data" / "tap_nonelective_tower.json"
)
MOCK_TAP_ELECTIVE_DATA = (
    Path(__file__).resolve().parent / "data" / "tap_elective_tower.json"
)

router = APIRouter(prefix="/hymind")

mock_router = APIRouter(
    prefix="/hymind",
)


@router.post(
    "/icu/tap/emergency/",
    response_model=list[EmTap],
)
def get_emergency_icu_admission_predictions(
    response: Response,
    data: EmElTapPostBody,
    settings: Settings = Depends(get_settings),
) -> list[EmTap]:
    """Retrieve emergency icu admission predictions

    Sends a POST to the hymind non-elective tap API endpoint
    Returns the result

    Args:
        response (Response): FastAPI Response object
        data (EmElTapPostBody): Emergency tap post body Pydantic model
        settings (Settings, optional): API settings from env file.
                                    Defaults to Depends(get_settings).

    Returns:
        list[EmTap]: List of ICU Emergency tap predictions
    """
    response = requests.post(f"{settings.emergency_tap_url}/predict", json=data.dict())
    rows = response.json()["data"]
    return [EmTap.parse_obj(row) for row in rows]


@mock_router.get("/icu/tap/emergency")
def get_mock_emergency_icu_admission_predictions() -> pd.DataFrame:
    """Retrieve mock ICU emergency tap predictions

    Returns:
        pd.DataFrame: DataFrame of mock emergency icu admission predictions
    """
    mock_dataframe = pd.read_json(MOCK_TAP_EMERGENCY_DATA)
    df = pd.DataFrame.from_records(mock_dataframe["data"])
    df = pydantic_dataframe(df, EmTap)
    records = df.to_dict(orient="records")
    response = dict(data=records)  # to match API structure {"data": List[Dict]}
    return response


@router.post("/icu/tap/electives")
def get_elective_icu_admission_predictions(
    response: Response,
    data: EmElTapPostBody,
    settings: Settings = Depends(get_settings),
) -> list[ElTap]:
    """Retrieve elective icu admission predictions

    Sends a POST to the hymind elective tap API endpoint
    Returns the result

    Args:
        response (Response): FastAPI Response object
        data (EmElTapPostBody): Elective tap post body Pydantic model
        settings (Settings, optional): API settings from env file.
                                    Defaults to Depends(get_settings).

    Returns:
        list[ElTap]: List of ICU Elective tap predictions
    """
    response = requests.post(f"{settings.electives_tap_url}/predict", json=data.dict())
    rows = response.json()["data"]
    return [ElTap.parse_obj(row) for row in rows]


@mock_router.get("/icu/tap/electives")
def get_mock_elective_icu_admission_predictions() -> pd.DataFrame:
    """Retrieve mock ICU elective tap predictions

    Returns:
        pd.DataFrame: DataFrame of mock elective icu admission predictions
    """
    mock_electives_dataframe = pd.read_json(MOCK_TAP_ELECTIVE_DATA)
    df = pd.DataFrame.from_records(mock_electives_dataframe["data"])
    df = pydantic_dataframe(df, ElTap)

    records = df.to_dict(orient="records")
    response = dict(data=records)  # to match API structure {"data": List[Dict]}
    return response


@router.get(
    "/discharge/individual/{ward}/",
    response_model=list[IcuDischarge],
)
def get_individual_discharge_predictions(
    response: Response,
    ward: str = Query(default=""),
    settings: Settings = Depends(get_settings),
) -> list[IcuDischarge]:
    # force to upper as expected by hymind API
    ward = ward.upper()
    response = requests.get(
        f"{settings.hymind_url}/predictions/icu/discharge", params={"ward": ward}
    )
    rows = response.json()["data"]
    return [IcuDischarge.parse_obj(row) for row in rows]


@mock_router.get(
    "/discharge/individual/{ward}/",
    response_model=list[IcuDischarge],
)
def get_mock_individual_discharge_predictions(
    ward: str = Query(default=""),
) -> list[IcuDischarge]:
    logging.info(f"Mock predictions for {ward}")
    return [
        IcuDischarge(
            prediction_id=421859,
            episode_slice_id=539532,
            model_name="bournville_rf",
            model_version=3,
            prediction_as_real=0.6994126228548821,
            predict_dt=datetime.datetime(2023, 1, 25, 22, 16, 24, 00, tzinfo=pytz.UTC),
        )
    ]
