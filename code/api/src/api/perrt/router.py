from collections import namedtuple
from typing import List

from fastapi import APIRouter, Depends, Query, Body
from sqlmodel import Session
from pydantic import parse_obj_as
import pandas as pd
import pickle
from pathlib import Path

from models.perrt import AdmissionPrediction, PerrtRaw, PerrtRead
from api.db import prepare_query
from utils.api import get_emap_session

from api.perrt.wrangle import wrangle

router = APIRouter(
    prefix="/perrt",
)


@router.get("/raw", response_model=List[PerrtRaw])
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


@router.get("/", response_model=List[PerrtRead])
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


@router.post("/admission_predictions", response_model=List[AdmissionPrediction])
def get_predictions(
    hospital_visit_ids: List[str] = Body(), session: Session = Depends(get_emap_session)
):

    predictions_filepath = Path(
        f"{Path(__file__).parent}/admission_probability/"
        + "generated_data/id_to_admission_prediction.pkl"
    )

    predictions_map = {}

    if predictions_filepath.is_file():
        predictions_map = pickle.load(open(predictions_filepath, "rb"))

    return [
        {
            "hospital_visit_id": key,
            "admission_probability": predictions_map.get(key, None),
        }
        for key in hospital_visit_ids
    ]
