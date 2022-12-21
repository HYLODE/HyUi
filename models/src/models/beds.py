from pydantic import BaseModel


class Bed(BaseModel):
    location_string: str
    closed: bool | None
    covid: bool | None
    xpos: int | None
    ypos: int | None
