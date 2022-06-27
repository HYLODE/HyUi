# src/api/perrt/router.py
from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from utils import get_emap_session, get_model_from_route, prepare_query

router = APIRouter(
    prefix="/perrt",
)

PerrtRead = get_model_from_route("Perrt", "Read")


@router.get("/", response_model=List[PerrtRead])  # type: ignore
def read_perrt(
    session: Session = Depends(get_emap_session),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
):
    """
    Returns Perrt data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    TODO: need to add logic to join patient identifiers from EMAP
    """
    q = prepare_query("perrt")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    # returning JSON over the API seems to be the slow part
    # i.e. this is super quick
    # records = records[:100]
    # suggesting that the code above is OK for speed
    records = records[offset:limit]
    return records
