from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from utils import get_model_from_route, prepare_query
from utils.api import get_emap_session

router = APIRouter(
    prefix="/sitrep",
)

SitrepRead = get_model_from_route("Sitrep", "Read")


@router.get("/beds/list", response_model=List[dict])
def read_bed_list():
    # TODO: Look at utils.beds.py to see how this is implemented.
    return []


@router.get("/", response_model=List[SitrepRead])  # type: ignore
def read_sitrep(session: Session = Depends(get_emap_session)):
    """
    Returns Sitrep data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    """
    q = prepare_query("sitrep")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
