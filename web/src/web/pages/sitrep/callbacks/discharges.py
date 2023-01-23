"""
Module to manage the CRUD of discharge status
"""
import requests
from pydantic import BaseModel
from typing import Tuple

from models.beds import DischargeStatus
from web.config import get_settings
from web.convert import parse_to_data_frame


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
