from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from config.settings import settings
from models.hymind import EmElTapPostBody
from utils import get_model_from_route
from utils.api import pydantic_dataframe

MOCK_ICU_DISCHARGE_DATA = (
    Path(__file__).resolve().parent / "data" / "mock_icu_discharge.json"
)
MOCK_TAP_EMERGENCY_DATA = (
    Path(__file__).resolve().parent / "data" / "tap_nonelective_tower.json"
)
MOCK_TAP_ELECTIVE_DATA = (
    Path(__file__).resolve().parent / "data" / "tap_elective_tower.json"
)

router = APIRouter(
    prefix="/hymind",
)

IcuDischarge = get_model_from_route("Hymind", standalone="IcuDischarge")
EmTap = get_model_from_route("Hymind", standalone="EmTap")
ElTap = get_model_from_route("Hymind", standalone="ElTap")


def read_query(file_live: str, table_mock: str):
    """
    generates a query based on the environment

    :param      file_live:   The file live
                             e.g. live_case.sql
    :param      table_mock:  The table mock
                             e.g. electivesmock
    returns a string containing a SQL query
    """
    if settings.ENV == "dev":
        query = f"SELECT * FROM {table_mock}"
    else:
        sql_file = Path(__file__).resolve().parent / file_live
        query = Path(sql_file).read_text()
    return query


@router.get("/icu/discharge")  # type: ignore
def read_icu_discharge(ward: str):
    """ """
    if settings.ENV == "dev":

        # import ipdb; ipdb.set_trace()
        _ = pd.read_json(MOCK_ICU_DISCHARGE_DATA)
        df = pd.DataFrame.from_records(_["data"])
        df = pydantic_dataframe(df, IcuDischarge)
    else:
        return (
            "API not designed to work in live environment. You should call "
            "http://uclvlddpragae08:5907/predictions/icu/discharge?ward=T03 "
            "or similar instead"
        )
    records = df.to_dict(orient="records")
    response = dict(data=records)  # to match API
    # deliberately not using response model in the decorator definition b/c we
    # do the validating in the function and the model is nested as {data:
    # List[Model]} which I cannot encode
    return response


# deliberately not using response model in the decorator definition b/c we
# do the validating in the function and the model is nested as {data:
# List[Model]} which I cannot encode
# @router.post("/icu/tap/emergency", response_model=EmTap)  # type: ignore
@router.post("/icu/tap/emergency")  # type: ignore
def read_tap_emergency(data: EmElTapPostBody):
    """ """
    if settings.ENV == "dev":

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


@router.get("/icu/tap/electives")  # type: ignore
def read_tap_electives(data: EmElTapPostBody):
    if settings.ENV == "dev":

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
