from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from utils import get_model_from_route, prepare_query
from utils.api import get_emap_session

router = APIRouter(
    prefix="/consults",
)

ConsultsRead = get_model_from_route("Consults", "Read")


@router.get("/", response_model=List[ConsultsRead])  # type: ignore
def read_consults(session: Session = Depends(get_emap_session)):
    """
    Returns Consults data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    q = prepare_query("consults")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
