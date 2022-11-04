from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


# define the data model that you're expecting from your query
class RosBase(BaseModel):

    department: str
    bed_name: str
    mrn: str
    encounter: int
    firstname: str
    lastname: str
    date_of_birth: date
    hospital_admission_datetime: datetime
    location_admission_datetime: datetime
    # ros_orders: Optional[List[dict[str, object]]]
    # mrsa_orders: Optional[List[dict[str, object]]]
    # covid_orders: Optional[List[dict[str, object]]]
    ros_orders: Optional[str]
    mrsa_orders: Optional[str]
    covid_orders: Optional[str]


class RosMock(RosBase):  # , table=True):  # type: ignore
    """
    The table version of the pydantic class
    Used for creating tables via SQLModel
    """

    # only set schema if in postgres
    # TODO: Figure out how to fix this.
    # if "postgres" in settings.STAR_URL:
    #     __table_args__ = {"schema": settings.DB_POSTGRES_SCHEMA}
    id: Optional[int]  # = Field(default=None, primary_key=True)


class RosRead(RosBase):
    """
    Read version that includes the key column
    """

    id: Optional[int]
