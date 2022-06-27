# src/api/sitrep/router.py
from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from utils import get_emap_session, get_model_from_route, prepare_query

router = APIRouter(
    prefix="/sitrep",
)

SitrepRead = get_model_from_route("Sitrep", "Read")


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
