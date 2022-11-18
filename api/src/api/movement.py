from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session


class NextLocation(BaseModel):
    csn: str
    next_location: str | None
    speciality: str | None
    event_datetime: datetime


def next_locations(star_session: Session, csns: list[str]) -> list[NextLocation]:
    """
    For each patient CSN return whether a request to move to another bed has
    been made.

    :param star_session: Database connection to EMAP star.
    :param csns: A list of patient CSNs to check.
    :return: A data frame [csn, next_location, event_time, next_speciality]. No rows
        will be returned for patients that do not have bed requests.
    """

    query = text(
        """
        SELECT DISTINCT ON (hv.encounter) hv.encounter AS csn,
            l.location_string AS next_location,
            d.speciality AS next_speciality,
            pm.event_datetime AS event_dt
        FROM star.planned_movement pm
        INNER JOIN star.hospital_visit hv
            ON hv.hospital_visit_id = pm.hospital_visit_id
        LEFT JOIN star.location l
            ON l.location_id = pm.location_id
        LEFT JOIN star.department d
            ON d.department_id = l.department_id
        WHERE NOT pm.cancelled
        AND pm.event_datetime IS NOT NULL
        AND hv.encounter IN :csns
        ORDER BY hv.encounter, pm.event_datetime DESC
        """
    )

    results = star_session.execute(query, {"csns": tuple(csns)})

    return [NextLocation.parse_obj(row) for row in results]
