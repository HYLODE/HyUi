from collections import namedtuple

from fastapi import APIRouter, Depends
from sqlmodel import Session

from models.sitrep import SitrepRead
from utils import prepare_query
from utils.api import get_emap_session

router = APIRouter(
    prefix="/sitrep",
)


@router.get("/beds/list", response_model=list[dict])
def read_bed_list():
    # TODO: Look at utils.beds.py to see how this is implemented.
    return []


@router.get("/", response_model=list[SitrepRead])
def read_sitrep(session: Session = Depends(get_emap_session)):
    """
    Returns Sitrep data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live (from the API itself)\n\n
    """
    q = prepare_query("sitrep")
    results = session.exec(q)
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
