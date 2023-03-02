from datetime import date

from pydantic import BaseModel


class DischargeRow(BaseModel):
    discharge_date: date
    count: int
