# src/api/electives/router.py
from pathlib import Path
from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from utils import get_model_from_route, prepare_query
from utils.api import get_caboodle_session


router = APIRouter(
    prefix="/electives",
)

ElectivesRead = get_model_from_route("Electives", "Read")
PodRead = get_model_from_route("Electives", "Pod")  # pod=post-op destination


@router.get("/electives", response_model=List[ElectivesRead])  # type: ignore
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


@router.get("/pod", response_model=List[PodRead])  # type: ignore
def read_pod(session: Session = Depends(get_clarity_session)):
    """
    Returns Electives data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    TODO: need to add logic to join patient identifiers from EMAP
    """
    sql_file = Path(__file__).resolve().parent / "live_pod.sql"
    query = Path(sql_file).read_text()
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
