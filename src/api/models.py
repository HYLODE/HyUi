# src/models.py
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime, date
from pydantic import validator
import arrow



class ConsultsED(SQLModel):
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


class Consultation_Request_Base(SQLModel):
    valid_from: Optional[datetime]
    cancelled: Optional[bool]
    closed_due_to_discharge: Optional[bool]
    scheduled_datetime: Optional[datetime]
    status_change_time: Optional[datetime]
    comments: Optional[str]
    consultation_type_id: Optional[int]
    hospital_visit_id: Optional[int]


class Consultation_Request(Consultation_Request_Base, table=True):
    __table_args__ = {"schema": "star"}
    consultation_request_id: Optional[int] = Field(default=None, primary_key=True)


class Consultation_Request_Read(Consultation_Request_Base):
    consultation_request_id: Optional[int]


class Consultation_Type_Base(SQLModel):
    # stored_from: datetime
    valid_from: datetime
    code: str
    name: Optional[str] = Field(default="")


class Consultation_Type(Consultation_Type_Base, table=True):
    __table_args__ = {"schema": "star"}
    consultation_type_id: Optional[int] = Field(default=None, primary_key=True)


class Consultation_Type_Read(Consultation_Type_Base):
    consultation_type_id: int
