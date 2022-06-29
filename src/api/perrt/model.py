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
    Raw data
    Perrt class to hold data returned from the Perrt query
    the SQL query that runs against EMAP etc
    One row per visit observation (hence _long_)
    """

    # patient level fields
    mrn: str
    lastname: str
    firstname: str
    sex: str
    date_of_birth: date
    bed_admit_dt: datetime
    dept_name: str
    room_name: str
    bed_hl7: str
    perrt_consult_datetime: Optional[datetime]
    # observation level fields
    visit_observation_id: int
    ob_tail_i: int
    observation_datetime: datetime
    id_in_application: int
    value_as_real: Optional[float]
    value_as_text: Optional[str]
    unit: Optional[str]

    # TODO: how to share functions between classes?
    @validator("perrt_consult_datetime")
    def replace_NaT_with_None(cls, v):
        """
        SQLAlchemy chokes when converting pd.NaT It seems to convert to a float
        which is incompatible with the int type used for datetimes so here we
        simple convert NaT to None

        NB: pd.NaT is stored as -9223372036854775808 (int64 type)
        ```
        dfTest = pd.DataFrame([-9223372036854775808, 1655651820000000000],columns=['ts'])
        dfTest.apply(pd.to_datetime)
        ```
        """
        return v if v is not pd.NaT else None

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
    Wrangled data
    Perrt class to hold data returned from the Perrt query
    the SQL query or the API
    """

    # patient level fields
    mrn: str
    lastname: str
    firstname: str
    sex: str
    date_of_birth: date
    bed_admit_dt: datetime
    dept_name: str
    room_name: str
    bed_hl7: str
    perrt_consult_datetime: Optional[datetime]
    # observation level fields collapsed to per patient
    air_or_o2_max: Optional[float]
    air_or_o2_min: Optional[float]
    avpu_max: Optional[float]
    avpu_min: Optional[float]
    bp_max: Optional[float]
    bp_min: Optional[float]
    news_scale_1_max: Optional[float]
    news_scale_1_min: Optional[float]
    news_scale_2_max: Optional[float]
    news_scale_2_min: Optional[float]
    pulse_max: Optional[float]
    pulse_min: Optional[float]
    resp_max: Optional[float]
    resp_min: Optional[float]
    spo2_max: Optional[float]
    spo2_min: Optional[float]
    temp_max: Optional[float]
    temp_min: Optional[float]

    @validator("perrt_consult_datetime")
    def replace_NaT_with_None(cls, v):
        """
        SQLAlchemy chokes when converting pd.NaT It seems to convert to a float
        which is incompatible with the int type used for datetimes so here we
        simple convert NaT to None

        NB: pd.NaT is stored as -9223372036854775808 (int64 type)
        ```
        dfTest = pd.DataFrame([-9223372036854775808, 1655651820000000000],columns=['ts'])
        dfTest.apply(pd.to_datetime)
        ```
        """
        return v if v is not pd.NaT else None

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
