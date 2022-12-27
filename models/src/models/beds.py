from datetime import datetime
from pydantic import BaseModel, validator


class DischargeStatus(BaseModel):
    id: int
    order: float
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
    def empty_string_to_false(cls, v):
        """convert empty string to false"""
        if v == "" or v is None:
            return False
        if type(v) is str and v.lower() == "true":
            return True
        try:
            v = int(float(v))
            return True if v else False
        except ValueError:
            return False

    @validator("xpos", "ypos", pre=True)
    def empty_string_to_minus_one(cls, v):
        """convert empty string to zero"""
        if v == "" or v is None:
            return -1
        try:
            v = int(float(v))
            return v
        except ValueError:
            return -1
