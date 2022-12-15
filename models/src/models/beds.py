from pydantic import BaseModel


class Bed(BaseModel):
    location_string: str
    room: str
    bed: str
    closed: bool
    covid: bool
