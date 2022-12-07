from datetime import datetime

from pydantic import BaseModel


def _to_camel(member: str) -> str:
    return "".join(word.capitalize() for word in member.split("_"))


class ClarityOrCase(BaseModel):
    """
    Vignette example built from Clarity query for future surgical cases
    """

    pod_orc: str
    or_case_id: int
    surgery_date_clarity: datetime

    class Config:
        alias_generator = _to_camel
        allow_population_by_field_name = True
