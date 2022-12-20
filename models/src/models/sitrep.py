from pydantic import BaseModel, Field


class BedRow(BaseModel):
    location_string: str
    bed_functional: list[dict[str, str | int]]
    bed_physical: list[dict[str, str | int]]
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
    wim_1: int


class IndividualDischargePrediction(BaseModel):
    episode_slice_id: int
    prediction: float = Field(..., alias="prediction_as_real")
