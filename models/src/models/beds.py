from pydantic import BaseModel


class Bed(BaseModel):
    location_string: str
    room: str
    closed: bool
    covid: bool
