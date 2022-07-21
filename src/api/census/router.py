# src/api/census/router.py
from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from utils import get_model_from_route, prepare_query
from utils.api import get_emap_session

router = APIRouter(
    prefix="/census",
)

CensusRead = get_model_from_route("Census", "Read")


@router.get("/", response_model=List[CensusRead])  # type: ignore
def read_census(session: Session = Depends(get_emap_session)):
    """
    Returns Census data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    """
    q = prepare_query("census")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
