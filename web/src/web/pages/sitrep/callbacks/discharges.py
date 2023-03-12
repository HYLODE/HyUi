"""
Module to manage the CRUD of discharge status
"""
import dash
import pandas as pd
import warnings

import requests
from dash import Input, Output, callback
from loguru import logger
from pydantic import BaseModel
from typing import Tuple

from models.beds import DischargeStatus
from web.config import get_settings
from web.convert import parse_to_data_frame
from web.logger import logger_timeit
from web.pages.sitrep import ids


def post_discharge_status(csn: int, status: str) -> Tuple[int, DischargeStatus]:
    status = status.lower()
    response = requests.post(
        url=f"{get_settings().api_url}/baserow/discharge_status",
        params={"csn": csn, "status": status},  # type: ignore
    )
    return response.status_code, DischargeStatus.parse_obj(response.json())


def _most_recent_row_only(
    rows: list[dict], groupby_col: str, timestamp_col: str, data_model: BaseModel
) -> list[dict]:
    df = parse_to_data_frame(rows, data_model)
    # remove duplicates here
    df = df.sort_values(timestamp_col, ascending=False)
    df = df.groupby(groupby_col).head(1)
    return df.to_dict(orient="records")  # type: ignore


def _get_discharge_updates(delta_hours: int = 48) -> list[dict]:
    response = requests.get(
        f"{get_settings().api_url}/baserow/discharge_status",
        params={"delta_hours": delta_hours},
    )
    if response.status_code == 200:
        return response.json()  # type: ignore
    else:
        warnings.warn("No data found for discharge statues (from Baserow " "store)")
        return [{}]


@callback(
    Output(ids.DISCHARGES_STORE, "data"),
    Input(ids.DEPT_SELECTOR, "value"),
)
@logger_timeit(level="DEBUG")
def store_discharge_status(dept: str) -> list[dict]:
    """
    Get discharge status
    Deduplicate to most recent only
    Refreshes on ward update
    """
    if not dept:
        return dash.no_update  # type: ignore
    discharges = _get_discharge_updates(delta_hours=36)
    if not discharges or not len(discharges):
        return dash.no_update  # type: ignore
    df = pd.DataFrame.from_records(discharges)
    try:
        df.sort_values(["csn", "modified_at"], ascending=[True, False], inplace=True)
        df.drop_duplicates(["csn"], inplace=True)
    except KeyError as e:
        logger.warning("Unable to sort: is the dataframe empty?")
        logger.exception(e)
    return df.to_dict(orient="records")  # type: ignore
