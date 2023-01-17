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
    # admission_dt: "2022-12-14T12:20:00+00:00",
    # elapsed_los_td: 733260.0,
    # bed_code: "BY04-30",
    # bay_code: "BY04",
    # bay_type: "Regular",
    # ward_code: "T03",
    # mrn: "",
    # name: "",
    # dob: "1938-01-30",
    # admission_age_years: 84,
    # sex: "F",
    # is_proned_1_4h: false,
    # discharge_ready_1_4h: "No",
    discharge_ready_1_4h: str | None
    is_agitated_1_8h: bool
    # had_nitric_1_8h: false,
    # had_rrt_1_4h: false,
    # had_trache_1_12h: false,
    # vent_type_1_4h: "Unknown",
    # avg_heart_rate_1_24h: 87.5,
    # max_temp_1_12h: null,
    # avg_resp_rate_1_24h: 21.0,
    # wim_1: 0


class IndividualDischargePrediction(BaseModel):
    episode_slice_id: int
    prediction: float = Field(..., alias="prediction_as_real")
