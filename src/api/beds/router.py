from collections import namedtuple
from typing import List, Union

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
import sqlalchemy as sa

from utils import get_model_from_route, prepare_query
from utils.api import get_emap_session
from utils.wards import wards, departments_missing_beds

router = APIRouter(
    prefix="/beds",
)

BedsRead = get_model_from_route("Beds", "Read")


@router.get("/", response_model=List[BedsRead])  # type: ignore
def read_beds(
    session: Session = Depends(get_emap_session),
    departments: Union[List[str], None] = Query(default=wards),
    locations: Union[List[str], None] = Query(default=[]),
):
    """
    Returns beds data class populated by query-live/mock
    query preparation depends on the environment so will return
    mock data in dev and live data in prod
    """
    for d in departments:
        if d in departments_missing_beds.keys():
            locations_to_add = departments_missing_beds[d]
            [locations.append(l) for l in locations_to_add]

    qtext = prepare_query("beds")
    if session.get_bind().name == 'sqlite':
    # as per https://stackoverflow.com/a/56382828/992999
        qtext = sa.text(qtext)
        qtext = qtext.bindparams(
            sa.bindparam("departments", expanding=True),
            sa.bindparam("locations", expanding=True),
        )
    elif session.get_bind().name == 'postgresql':
        qtext = sa.text(qtext)
    else:
        raise Exception

    params = {"departments": departments, "locations": locations}
    # NOTE: this fails with sqlmodel.exec / works with sa.execute
    # import pdb; pdb.set_trace()
    results = session.execute(qtext, params)

    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records
