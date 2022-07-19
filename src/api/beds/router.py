from collections import namedtuple
from typing import List, Union

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
import sqlalchemy as sa

from utils import get_model_from_route, prepare_query
from utils.api import get_emap_session
from utils.wards import wards

router = APIRouter(
    prefix="/beds",
)

BedsRead = get_model_from_route("Beds", "Read")


@router.get("/", response_model=List[BedsRead])  # type: ignore
def read_beds(
    session: Session = Depends(get_emap_session),
    department: Union[List[str], None] = Query(default=wards),
):
    """
    Returns beds data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    q = prepare_query("beds")
    # as per https://stackoverflow.com/a/56382828/992999
    qtext = sa.text(q)
    qtext = qtext.bindparams(sa.bindparam("depts", expanding=True))

    if type(department) is str:
        depts = [department]
    else:
        depts = department

    params = {"depts": depts}
    # NOTE: this fails with sqlmodel.exec / works with sa.execute
    results = session.execute(qtext, params)

    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
