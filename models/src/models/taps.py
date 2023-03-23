from datetime import datetime

from pydantic import BaseModel


def _to_camel(member: str) -> str:
    return "".join(word.capitalize() for word in member.split("_"))


class TapsPredictor(BaseModel):
    bed_count: int
    probability: float
    predict_dt: datetime
    model_name: str
    model_version: int
    run_id: str
    horizon_dt: datetime
    inputs: str | None

    class Config:
        alias_generator = _to_camel
        allow_population_by_field_name = True
