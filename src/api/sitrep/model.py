# src/api/sitrep/model.py
"""
Results from Sitrep API
eg.

http://172.16.149.205:5006/icu/live/{ward}/ui

The developer should specify the data models here
and follow the **same** naming convention such that
the module.classname can be reliably used for access
"""

from datetime import date, datetime
from typing import Optional

import arrow
from pydantic import validator
from sqlmodel import Field, SQLModel

from config.settings import settings  # type: ignore


# define the data model that you're expecting from your query
class SitrepBase(SQLModel):
    """
    Sitrep class to hold data returned from
    the SQL query or the API
    This particular example holds the results from a call to the Sitrep API for the ICU
    """

    dob: date
    admission_age_years: int
    name: str
    mrn: str
    csn: int
    episode_slice_id: int
    admission_dt: datetime
    elapsed_los_td: float
    bed_code: str
    bay_code: str
    ward_code: str
    sex: str
    is_proned_1_4h: Optional[bool]
    discharge_ready_1_4h: Optional[bool]
    is_agitated_1_8h: Optional[bool]
    n_inotropes_1_4h: Optional[int]
    had_nitric_1_8h: Optional[bool]
    had_rrt_1_4h: Optional[bool]
    had_trache_1_12h: Optional[bool]
    vent_type_1_4h: Optional[str]
    avg_heart_rate_1_24h: Optional[float]
    max_temp_1_12h: Optional[float]
    avg_resp_rate_1_24h: Optional[float]
    wim_1: int

    @validator("dob", pre=True)
    def convert_datetime_to_date(cls, v):
        if isinstance(v, str):
            try:
                return arrow.get(v).date()
            except Exception as e:
                print("Unable to convert dob to date")
                print(e)
        return v


class Sitrep(SitrepBase, table=True):
    """
    The table version of the pydantic class
    Used for creating tables via SQLModel
    """

    # only set schema if in postgres
    if "postgres" in settings.DB_URL:
        __table_args__ = {"schema": settings.DB_POSTGRES_SCHEMA}
    id: Optional[int] = Field(default=None, primary_key=True)


class SitrepRead(SitrepBase):
    """
    Read version that includes the key column
    """

    id: Optional[int]
