from collections import namedtuple

from fastapi import APIRouter, Depends
from sqlmodel import Session

from models.consults import ConsultsRead
from api.db import prepare_query, get_star_session

router = APIRouter(
    prefix="/consults",
)


@router.get("/", response_model=list[ConsultsRead])
def read_consults(session: Session = Depends(get_star_session)):
    """
    Returns Consults data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    q = prepare_query("consults", "FIXME")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
