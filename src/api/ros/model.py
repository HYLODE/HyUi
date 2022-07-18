# src/api/ros/model.py
"""

"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from config.settings import settings  # type: ignore


# define the data model that you're expecting from your query
class RosBase(SQLModel):

    date_of_birth: date
    admission_time: datetime
    firstname: str
    lastname: str
    bed_name: str
    room_name: str
    live_mrn: str
    hospital_visit_id: str
    order_datetime: Optional[datetime]
    lab_result_id: Optional[float]

    # @validator("dob", pre=True)
    # def convert_datetime_to_date(cls, v):
    #     if isinstance(v, str):
    #         try:
    #             return arrow.get(v).date()
    #         except Exception as e:
    #             print("Unable to convert dob to date")
    #             print(e)
    #     return v


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
