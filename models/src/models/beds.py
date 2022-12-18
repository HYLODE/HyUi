from pydantic import BaseModel


class Bed(BaseModel):
    location_string: str
    closed: bool
    covid: bool
    xpos: float
    ypos: float
