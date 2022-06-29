# src/api/perrt/router.py
from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from pydantic import parse_obj_as
import pandas as pd

from utils import get_emap_session, get_model_from_route, prepare_query
from .wrangle import wrangle

router = APIRouter(
    prefix="/perrt",
)

PerrtRaw = get_model_from_route("Perrt", "Raw")
PerrtRead = get_model_from_route("Perrt", "Read")


@router.get("/raw", response_model=List[PerrtRaw])  # type: ignore
def read_perrt_table(
    session: Session = Depends(get_emap_session),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
):
    """
    Returns PerrtTable data class populated by query-live/mock

    Query preparation depends on the environment via arg get_emap_session so
    will return mock data in dev and live (from the API itself)
    """
    q = prepare_query("perrt")
    results = session.exec(q)  # type: ignore
    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    records = records[offset:limit]
    return records


@router.get("/", response_model=List[PerrtRead])  # type: ignore
def read_perrt(session: Session = Depends(get_emap_session)):
    """
    Returns PerrtRead data class post wrangling

    :param      session:  EMAP database connection
    :type       session:  Session
    """
    # Run the 'raw query'
    q = prepare_query("perrt")
    results = session.exec(q)  # type: ignore
    # Validate the raw query using the SQLModel (Pydantic model)
    rec = [parse_obj_as(PerrtRaw, r) for r in results.fetchall()]
    # now you want to hand this pandas without losing the typing
    dfr = pd.DataFrame.from_records([dict(r) for r in rec])
    # now wrangle
    dfw = wrangle(dfr)
    mask1 = dfw["news_scale_1_max"] > 0
    mask2 = dfw["news_scale_2_max"] > 0
    dfw = dfw[mask1 | mask2]
    # now return as a list of dictionaries
    recw = dfw.to_dict(orient="records")
    # recw = recw[:10]
    return recw
