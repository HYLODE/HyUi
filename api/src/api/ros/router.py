from collections import namedtuple

from fastapi import APIRouter, Depends
from sqlmodel import Session

from models.ros import RosRead
from api.dependencies import add_cache_control_header
from api.db import prepare_query, get_star_session

router = APIRouter(prefix="/ros", dependencies=[Depends(add_cache_control_header)])


@router.get("/", response_model=list[RosRead])
def read_ros(session: Session = Depends(get_star_session)) -> list[RosRead]:
    """
    Returns Ros data
    """
    q = prepare_query("ros", "FIXME")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
