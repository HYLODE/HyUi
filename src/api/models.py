# src/models.py
"""
The developer should specifc the data models here
Both the ResultsBase and the Results classes will need editing
"""
from datetime import date, datetime
from typing import Optional

import arrow
from pydantic import validator
from sqlmodel import Field, SQLModel
from config.settings import settings


# define the data model that you're expecting from your query
class ResultsBase(SQLModel):
    """
    Generic results class to hold data returned from
    the SQL query or the API
    This particular example holds list of patients in the ED
    with pending inpatient consults
    """

    firstname: str
    lastname: str
    date_of_birth: date
    mrn: str
    nhs_number: Optional[int]
    valid_from: datetime
    cancelled: bool
    closed_due_to_discharge: bool
    scheduled_datetime: datetime
    status_change_time: datetime
    comments: Optional[str]
    name: str
    dept_name: str

    @validator("date_of_birth", pre=True)
    def convert_datetime_to_date(cls, v):
        if isinstance(v, str):
            try:
                return arrow.get(v).date()
            except Exception as e:
                print("Unable to convert date_of_birth to date")
                print(e)
        return v


class Results(ResultsBase, table=True):
    """
    The table version of the pydantic class
    Used for creating tables via SQLModel
    """

    # only set schema if in postgres
    if "postgres" in settings.DB_URL:
        __table_args__ = {"schema": settings.DB_POSTGRES_SCHEMA}
    consultation_request_id: Optional[int] = Field(default=None, primary_key=True)
