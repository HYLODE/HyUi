# src/api/ros/ros.py
from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from utils import get_model_from_route, prepare_query
from utils.api import get_emap_session


router = APIRouter(
    prefix="/ros",
)

RosRead = get_model_from_route("Ros", "Read")


@router.get("/", response_model=List[RosRead])  # type: ignore
def read_ros(session: Session = Depends(get_emap_session)):
    """
    Returns Ros data
    """
    q = prepare_query("ros")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
