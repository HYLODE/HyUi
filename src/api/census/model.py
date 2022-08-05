# src/api/census/model.py
"""
"""

from datetime import date, datetime
from typing import Optional

import arrow
import pandas as pd
from pydantic import validator
from sqlmodel import Field, SQLModel

from config.settings import settings  # type: ignore


# define the data model that you're expecting from your query
class CensusBase(SQLModel):
    """
    Census class to hold data returned from
    the SQL query or the API
    This particular example holds the results from a call to the Census API for the ICU
    """

    name: str
    sex: str
    # admission_age_years: int
    dob: date
    mrn: str
    csn: int
    postcode: Optional[str]
    admission_dt: datetime
    # discharge_dt: Optional[datetime]
    ward_code: str
    bay_code: str
    bed_code: str
    bay_type: str

    @validator("dob", pre=True)
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


class CensusMock(CensusBase, table=True):
    """
    The table version of the pydantic class
    Used for creating tables via SQLModel
    """

    # only set schema if in postgres
    if "postgres" in settings.STAR_URL:
        __table_args__ = {"schema": settings.DB_POSTGRES_SCHEMA}
    id: Optional[int] = Field(default=None, primary_key=True)


class CensusRead(CensusBase):
    """
    Read version that includes the key column
    """

    id: Optional[int]
