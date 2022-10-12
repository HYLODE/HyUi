from collections import namedtuple
from typing import List, Union

import pandas as pd
import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query
from pydantic import parse_obj_as
from sqlmodel import Session

from utils import get_model_from_route, prepare_query
from utils.api import get_emap_session
from utils.wards import departments_missing_beds, wards

from .wrangle import aggregate_by_department

router = APIRouter(
    prefix="/census",
)

CensusRead = get_model_from_route("Census", "Read")
CensusDepartments = get_model_from_route("Census", "Departments")


@router.get("/", response_model=List[CensusRead])  # type: ignore
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
            [locations.append(i) for i in locations_to_add]

    qtext = prepare_query("census")
    qtext = sa.text(qtext)
    # necessary if working with mock data from sqlite rather than postgres
    if session.get_bind().name == "sqlite":
        # as per https://stackoverflow.com/a/56382828/992999
        qtext = qtext.bindparams(
            sa.bindparam("departments", expanding=True),
            sa.bindparam("locations", expanding=True),
        )

    params = {"departments": departments, "locations": locations}
    # NOTE: this fails with sqlmodel.exec / works with sa.execute
    # import pdb; pdb.set_trace()
    results = session.execute(qtext, params)

    Record = namedtuple("Record", results.keys())  # type: ignore
    records = [Record(*r) for r in results.fetchall()]
    return records


@router.get("/departments", response_model=List[CensusDepartments])  # type: ignore
def read_departments(session: Session = Depends(get_emap_session)):
    """
    Run the beds query then aggregate
    """
    locations = []
    departments = wards.copy()
    # this 'duplicates' functionality above but the alternative is to swap out
    # Query/Depends etc from the function b/c when called directly without the
    # decorator then all the types are wrong

    # add in locations without departments
    # TODO: need to use this info to add the department into the results
    for d in departments:
        if d in departments_missing_beds.keys():
            locations_to_add = departments_missing_beds[d]
            [locations.append(i) for i in locations_to_add]

    qtext = prepare_query("census")
    qtext = sa.text(qtext)
    # necessary if working with mock data from sqlite rather than postgres
    if session.get_bind().name == "sqlite":
        # as per https://stackoverflow.com/a/56382828/992999
        qtext = qtext.bindparams(
            sa.bindparam("departments", expanding=True),
            sa.bindparam("locations", expanding=True),
        )

    params = {"departments": departments, "locations": locations}

    df = pd.read_sql(qtext, session.connection(), params=params)

    # round trip from dataframe to dictionary to records back to dataframe
    # just to use the data validation properties of pydantic!
    l_of_d = df.to_dict(orient="records")
    l_of_r = parse_obj_as(List[CensusRead], l_of_d)
    df = pd.DataFrame.from_dict([r.dict() for r in l_of_r])

    res = aggregate_by_department(df).to_dict(orient="records")
    return res
