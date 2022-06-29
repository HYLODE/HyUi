# src/api/perrt/model.py
"""
Model for ward patients at risk of deterioration
Not linked to Dan's work (for now)
Should always follow the naming pattern

ModuleModel (e.g. PerrtEMAP, PerrtRead)

where Module alone returns the base model

"""

from datetime import date, datetime
from typing import Optional

import arrow
import pandas as pd
from pydantic import validator
from sqlmodel import Field, SQLModel

from config.settings import settings  # type: ignore


# define the data model that you're expecting from your query
class PerrtRaw(SQLModel):
    """
    Perrt class to hold data returned from the Perrt query
    the SQL query that runs against EMAP etc
    """

    visit_observation_id: int
    ob_tail_i: int
    observation_datetime: datetime
    id_in_application: int
    value_as_real: Optional[float]
    value_as_text: Optional[str]
    unit: Optional[str]
    mrn: str
    lastname: str
    firstname: str
    sex: str
    date_of_birth: date
    bed_admit_dt: datetime
    dept_name: str
    room_name: str
    bed_hl7: str

    @validator("date_of_birth", pre=True)
    def convert_datetime_to_date(cls, v):
        if isinstance(v, str):
            try:
                return arrow.get(v).date()
            except Exception as e:
                print("Unable to convert dob to date")
                print(e)
        elif isinstance(v, pd.Timestamp):
            try:
                return v.date()
            except Exception as e:
                print("Unable to convert pandas Timestamp to date")
                print(e)
        return v


class PerrtMock(PerrtRaw, table=True):
    """
    The table version of the pydantic class
    Used for creating tables via SQLModel for mocking
    """

    # only set schema if in postgres
    if "postgres" in settings.DB_URL:
        __table_args__ = {"schema": settings.DB_POSTGRES_SCHEMA}
    Perrt_id: Optional[int] = Field(default=None, primary_key=True)


# define the data model that you're expecting from your query
class PerrtBase(SQLModel):
    """
    Perrt class to hold data returned from the Perrt query
    the SQL query or the API
    This particular example holds the results from a call to the Census API for the ICU
    """

    visit_observation_id: int
    ob_tail_i: int
    observation_datetime: datetime
    id_in_application: int
    value_as_real: Optional[float]
    value_as_text: Optional[str]
    unit: Optional[str]
    mrn: str
    lastname: str
    firstname: str
    sex: str
    date_of_birth: date
    bed_admit_dt: datetime
    dept_name: str
    room_name: str
    bed_hl7: str

    @validator("date_of_birth", pre=True)
    def convert_datetime_to_date(cls, v):
        if isinstance(v, str):
            try:
                return arrow.get(v).date()
            except Exception as e:
                print("Unable to convert dob to date")
                print(e)
        elif isinstance(v, pd.Timestamp):
            try:
                return v.date()
            except Exception as e:
                print("Unable to convert pandas Timestamp to date")
                print(e)
        return v


class PerrtRead(PerrtBase):
    """
    Read version that includes the key column
    """

    Perrt_id: Optional[int]
