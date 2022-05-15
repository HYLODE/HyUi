# src/models.py 
from typing import List, Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class ConsultsED(SQLModel):
    valid_from: datetime
    cancelled: bool
    closed_due_to_discharge: bool
    scheduled_datetime: datetime
    status_change_time: datetime
    comments: Optional[str]
    code: str
    name: str
    hospital_visit_id: int


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
    __table_args__ = {'schema': 'star'}
    consultation_request_id: Optional[int] = Field(default=None, primary_key=True)

class Consultation_Request_Read(Consultation_Request_Base):
    consultation_request_id: Optional[int]


class Consultation_Type_Base(SQLModel):
    #stored_from: datetime
    valid_from: datetime
    code: str
    name: Optional[str] = Field(default="")
    

class Consultation_Type(Consultation_Type_Base, table=True):
    __table_args__ = {'schema': 'star'}
    consultation_type_id: Optional[int] = Field(default=None, primary_key=True)
    

class Consultation_Type_Read(Consultation_Type_Base):
    consultation_type_id: int