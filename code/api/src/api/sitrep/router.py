from collections import namedtuple

import requests
from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.config import get_settings
from models.sitrep import SitrepRead
from api.db import prepare_query, get_star_session

router = APIRouter(
    prefix="/sitrep",
)


@router.get("/beds/list", response_model=list[dict])
def read_bed_list():
    # TODO: Look at utils.beds.py to see how this is implemented.
    return []


@router.get("/", response_model=list[SitrepRead])
def read_sitrep(session: Session = Depends(get_star_session)):
    """
    Returns Sitrep data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    """
    q = prepare_query("sitrep")
    results = session.exec(q)
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


@router.patch("/beds")
def update_bed_row(
    table_id: int, row_id: int, data: dict, settings=Depends(get_settings)
):
    url = f"{settings.baserow_url}/api/database/rows/table/{table_id}/"

    # TODO: Need to get working.
    requests.patch(
        url=f"{url}{row_id}/?user_field_names=true",
        headers={
            "Authorization": f"Token {settings.BASEROW_READWRITE_TOKEN}",
            "Content-Type": "application/json",
        },
        json=data,
    )
