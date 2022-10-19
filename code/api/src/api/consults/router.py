from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from models.consults import ConsultsRead
from api.db import prepare_query
from utils.api import get_emap_session

router = APIRouter(
    prefix="/consults",
)


@router.get("/", response_model=List[ConsultsRead])
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
