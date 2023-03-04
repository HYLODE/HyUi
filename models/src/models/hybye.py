from datetime import date

from pydantic import BaseModel


class HospitalFlowRow(BaseModel):
    event_date: date
    count: int
