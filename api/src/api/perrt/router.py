"""
Serve the PERRT endpoints
- raw data in long form from EMAP visit observation table
- wrangled data at the route
"""

import datetime as dt
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from api.convert import parse_to_data_frame
from api.db import get_star_session
from api.mock import _get_json_rows, _parse_query
from api.perrt.wrangle import wrangle
from models.perrt import EmapVitalsLong, EmapVitalsWide

router = APIRouter(prefix="/perrt")
mock_router = APIRouter(prefix="/perrt")
_this_file = Path(__file__)


@router.get("/vitals/long", response_model=list[EmapVitalsLong])
def get_emap_vitals(
    session: Session = Depends(get_star_session),
    encounter_ids: list[str] = Query(default=[]),
    horizon_dt: dt.datetime = dt.datetime.now() - dt.timedelta(hours=6),
):
    """
    Return vital signs
    :type horizon_dt: datetime remember to diff this from 'now'
    """
    params = {"encounter_ids": encounter_ids, "horizon_dt": horizon_dt}
    res = _parse_query(_this_file, "live_vitals.sql", session, EmapVitalsLong, params)
    return res


@mock_router.get("/vitals/long", response_model=list[EmapVitalsLong])
def get_mock_emap_vitals():
    """
    returns mock of emap query for vital signs
    :return:
    """
    rows = _get_json_rows(_this_file, "mock_vitals.json")
    return rows


# TODO: 2022-12-06 rather than prepare the vitals and the patients together;
#  leave that to the front end which can use census itself and instead you
#  will need a query for perrt consults and a wrangle to return one row per
#  encounter for the vitals


@mock_router.get("/vitals/wide")
def get_mock_emap_vitals_wide():
    """
    returns mock of emap query after wrangling
    :return:
    """
    rows = _get_json_rows(_this_file, "mock_vitals.json")
    df = parse_to_data_frame(rows, EmapVitalsLong)
    df_wide = wrangle(df)

    return [EmapVitalsWide.parse_obj(row) for row in df_wide.to_dict(orient="records")]


# @router.get("/", response_model=list[PerrtRead])
# def read_perrt(session: Session = Depends(get_star_session)):
#     """
#     Returns PerrtRead data class post wrangling
#
#     :param      session:  EMAP database connection
#     :type       session:  Session
#     """
#     # Run the 'raw query'
#     q = prepare_query("perrt", "FIXME")
#     results = session.exec(q)  # type: ignore
#     # Validate the raw query using the SQLModel (Pydantic model)
#     rec = [parse_obj_as(PerrtRaw, r) for r in results.fetchall()]
#     # now you want to hand this pandas without losing the typing
#     dfr = pd.DataFrame.from_records([dict(r) for r in rec])
#     # now wrangle
#     dfw = wrangle(dfr)
#     mask1 = dfw["news_scale_1_max"] > 0
#     mask2 = dfw["news_scale_2_max"] > 0
#     dfw = dfw[mask1 | mask2]
#     # now return as a list of dictionaries
#     recw = dfw.to_dict(orient="records")
#     # recw = recw[:10]
#     return recw
#
#
# @router.post("/admission_predictions", response_model=list[
# AdmissionPrediction])
# def get_predictions(
#         hospital_visit_ids: list[str] = Body(),
# ):
#     predictions_filepath = Path(
#         f"{Path(__file__).parent}/admission_probability/"
#         + "generated_data/id_to_admission_prediction.pkl"
#     )
#
#     predictions_map = {}
#
#     if predictions_filepath.is_file():
#         predictions_map = pickle.load(open(predictions_filepath, "rb"))
#
#     return [
#         {
#             "hospital_visit_id": key,
#             "admission_probability": predictions_map.get(key, None),
#         }
#         for key in hospital_visit_ids
#     ]
