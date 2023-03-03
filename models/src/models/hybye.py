from datetime import date

from pydantic import BaseModel


class HospitalFlowRow(BaseModel):
    date: date
    count: int
