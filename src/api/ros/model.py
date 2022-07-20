# src/api/ros/model.py
"""

"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from config.settings import settings  # type: ignore


# define the data model that you're expecting from your query
class RosBase(SQLModel):

    department: str
    bed_name: str
    mrn: int
    encounter: int
    firstname: str
    lastname: str
    date_of_birth: date
    hospital_admission_time: datetime
    location_admission_time: datetime
    ros_order_datetime: Optional[datetime]
    ros_lab_result_id: Optional[float]
    ros_value_as_text: Optional[str]
    mrsa_order_datetime: Optional[datetime]
    mrsa_lab_result_id: Optional[float]
    mrsa_value_as_text: Optional[str]


class RosMock(RosBase, table=True):
    """
    The table version of the pydantic class
    Used for creating tables via SQLModel
    """

    # only set schema if in postgres
    if "postgres" in settings.DB_URL:
        __table_args__ = {"schema": settings.DB_POSTGRES_SCHEMA}
    id: Optional[int] = Field(default=None, primary_key=True)


class RosRead(RosBase):
    """
    Read version that includes the key column
    """

    id: Optional[int]
