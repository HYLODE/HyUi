from collections import namedtuple

from fastapi import APIRouter, Depends
from sqlmodel import Session

from models.ros import RosRead
from api.db import prepare_query
from utils.api import get_emap_session


router = APIRouter(
    prefix="/ros",
)


@router.get("/", response_model=list[RosRead])
def read_ros(session: Session = Depends(get_emap_session)):
    """
    Returns Ros data
    """
    q = prepare_query("ros")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
