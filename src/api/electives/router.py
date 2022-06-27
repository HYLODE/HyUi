# src/api/electives/router.py
from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from utils import get_caboodle_session, get_model_from_route, prepare_query

router = APIRouter(
    prefix="/electives",
)

ElectivesRead = get_model_from_route("Electives", "Read")


@router.get("/", response_model=List[ElectivesRead])  # type: ignore
def read_electives(session: Session = Depends(get_caboodle_session)):
    """
    Returns Electives data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    TODO: need to add logic to join patient identifiers from EMAP
    """
    q = prepare_query("electives")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
