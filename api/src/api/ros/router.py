# type: ignore
from collections import namedtuple

from fastapi import APIRouter, Depends
from sqlmodel import Session

from models.ros import RosRead
from api.db import prepare_query, get_star_session

router = APIRouter(prefix="/ros")


@router.get("/", response_model=list[RosRead])
def read_ros(session: Session = Depends(get_star_session)) -> list[RosRead]:
    """
    Returns Ros data
    """
    q = prepare_query("ros", "FIXME")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]  # type: ignore
    return records
