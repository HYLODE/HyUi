from pydantic import BaseModel


class BedRow(BaseModel):
    location_string: str
    bed_functional: list[dict[str, str]]
    bed_physical: list[dict[str, str]]
    unit_order: int | None
    closed: bool
    covid: bool
    bed: str
    room: str


class SitrepRow(BaseModel):
    csn: str
    episode_slice_id: int
    n_inotropes_1_4h: int
    had_rrt_1_4h: bool
    vent_type_1_4h: str


class IndividualDischargePrediction(BaseModel):
    episode_slice_id: int
    prediction: float
