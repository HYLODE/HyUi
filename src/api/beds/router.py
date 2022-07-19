from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from utils import get_model_from_route, prepare_query
from utils.api import get_emap_session

router = APIRouter(
    prefix="/beds",
)

BedsRead = get_model_from_route("Beds", "Read")
BedsMock = get_model_from_route("Beds", "Mock")


@router.get("/", response_model=List[BedsMock])  # type: ignore
def read_beds(
    session: Session = Depends(get_emap_session),
    department: str = "UCH T03 INTENSIVE CARE",
):
    """
    Returns beds data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    q = prepare_query("beds")
    # results = session.exec(q, params={'department': list(department)})  # type: ignore
    # results = session.exec(q, params={'department': list(department)})  # type: ignore
    with session:
        # statement = select(BedsMock).limit(10)
        statement = select(BedsMock).where(BedsMock.department == department)
        results = session.exec(statement).all()
        return results
    # Record = namedtuple("Record", results.keys())  # type: ignore
    # records = [Record(*r) for r in results.fetchall()]
    # return records
