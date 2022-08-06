# src/api/hymind/router.py
from collections import namedtuple
from pathlib import Path
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends
from pydantic import parse_obj_as
from sqlmodel import Session

from config.settings import settings
from utils import get_model_from_route, prepare_query
from utils.api import get_caboodle_session, pydantic_dataframe

MOCK_ICU_DISCHARGE_DATA = (
    Path(__file__).resolve().parent / "data" / "mock_icu_discharge.json"
)

router = APIRouter(
    prefix="/hymind",
)

IcuDischarge = get_model_from_route("Hymind", standalone="IcuDischarge")


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


@router.get("/")  # type: ignore
def read_icu_discharge(ward: str):
    """ """
    if settings.ENV == "dev":

        # import ipdb; ipdb.set_trace()
        _ = pd.read_json(MOCK_ICU_DISCHARGE_DATA)
        df = pd.DataFrame.from_records(_["data"])
        df = pydantic_dataframe(df, IcuDischarge)
    else:
        example = "http://uclvlddpragae08:5907/predictions/icu/discharge?ward=T03"
        return f"""API not designed to work in live environment.\nYou should call {example} or similar instead"""
    records = df.to_dict(orient="records")
    response = dict(data=records)  # to match API
    # deliberately not using response model in the decorator definition b/c we
    # do the validating in the function and the model is nested as {data:
    # List[Model]} which I cannot encode
    return response
