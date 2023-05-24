from datetime import date, datetime

from pydantic import BaseModel


class Consults(BaseModel):
    firstname: str
    lastname: str
    date_of_birth: date
    mrn: str
    # nhs_number: Optional[int]
    # valid_from: datetime
    scheduled_datetime: datetime
    # status_change_time: datetime
    # comments: Optional[str]
    name: str
    dept_name: str | None
    location_string: str
