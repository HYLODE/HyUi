from datetime import datetime
from pydantic import BaseModel, validator


class DischargeStatus(BaseModel):
    id: int | None
    order: float | None
    csn: int
    status: str
    modified_at: datetime


class Bed(BaseModel):
    location_string: str
    closed: bool | None
    covid: bool | None
    xpos: int | None
    ypos: int | None

    # FIXME: Baserow data is stored as strings as there does not to be a way
    #  to define type when doing a bulk upload of data; these validators
    #  convert strings to the appropriate 'missing' type
    @validator("closed", "covid", pre=True)
    def empty_string_to_false(cls, value: str) -> bool:
        """convert empty string to false"""
        if value == "" or value is None:
            return False
        if type(value) is str and value.lower() == "true":
            return True
        try:
            int_value = int(float(value))
            return True if int_value else False
        except ValueError:
            return False

    @validator("xpos", "ypos", pre=True)
    def empty_string_to_minus_one(cls, value: str) -> int:
        """convert empty string to zero"""
        if value == "" or value is None:
            return -1
        try:
            int_value = int(float(value))
            return int_value
        except ValueError:
            return -1
