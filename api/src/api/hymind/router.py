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


@router.post("/icu/tap/emergency")
def read_tap_emergency(
    data: EmElTapPostBody, settings: Depends = Depends(get_settings)
) -> pd.DataFrame | str:
    """ """
    if settings.env == "dev":

        # import ipdb; ipdb.set_trace()
        _ = pd.read_json(MOCK_TAP_EMERGENCY_DATA)
        df = pd.DataFrame.from_records(_["data"])
        df = pydantic_dataframe(df, EmTap)
    else:
        return (
            "API not designed to work in live environment. "
            "You should POST to http://uclvlddpragae08:5230/predict/ "
            "(see {example}/docs)"
        )
    records = df.to_dict(orient="records")
    response = dict(data=records)  # to match API structure {"data": List[Dict]}
    return response


@router.get("/icu/tap/electives")
def read_tap_electives(
    data: EmElTapPostBody, settings: Depends = Depends(get_settings)
) -> pd.DataFrame | str:
    if settings.env == "dev":

        # import ipdb; ipdb.set_trace()
        _ = pd.read_json(MOCK_TAP_ELECTIVE_DATA)
        df = pd.DataFrame.from_records(_["data"])
        df = pydantic_dataframe(df, ElTap)
    else:
        return (
            "API not designed to work in live environment. "
            "You should GET to http://uclvlddpragae08:5230/predict/ "
            "(see {example}/docs)"
        )
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
    response.headers["Cache-Control"] = "public, max-age=3600"
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
