"""
Serve the PERRT endpoints
- raw data in long form from EMAP visit observation table
- wrangled data at the route
"""

from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.db import get_star_session
from api.mock import _get_json_rows, _parse_query
from models.perrt import EmapVitals

router = APIRouter(prefix="/perrt")
mock_router = APIRouter(prefix="/perrt")
_this_file = Path(__file__)


@router.get("/vitals", response_model=list[EmapVitals])
def get_emap_vitals(
    encounter_ids: List[int],
    horizon_dt: datetime,
    session: Session = Depends(get_star_session),
):
    """
    Return vital signs
    :type horizon_dt: datetime remember to diff this from 'now'
    """
    params = {"encounter_ids": encounter_ids, "horizon_dt": horizon_dt}
    res = _parse_query("live_vitals.sql", session, EmapVitals, params)
    return res


@mock_router.get("/vitals", response_model=list[EmapVitals])
def get_mock_emap_vitals():
    """
    returns mock of emap query for vital signs
    :return:
    """
    rows = _get_json_rows(_this_file, "mock_vitals.json")
    return rows


# TODO: 2022-12-05 resume here; check on live; write a test
# TODO: 2022-12-05 then call census and merge

# @router.get("/raw", response_model=list[PerrtRaw])
# def read_perrt_table(
#         session: Session = Depends(get_star_session),
#         offset: int = 0,
#         limit: int = Query(default=100, lte=100),
# ):
#     """
#     Returns PerrtTable data class populated by query-live/mock
#
#     Query preparation depends on the environment via arg get_emap_session so
#     will return mock data in dev and live (from the API itself)
#     """
#     q = prepare_query("perrt", "FIXME")
#     results = session.exec(q)  # type: ignore
#     Record = namedtuple("Record", results.keys())  # type: ignore
#     records = [Record(*r) for r in results.fetchall()]
#     records = records[offset:limit]
#     return records

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
# @router.post("/admission_predictions", response_model=list[AdmissionPrediction])
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
