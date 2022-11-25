from pydantic import BaseModel
from datetime import datetime


class ClarityOrCase(BaseModel):
    """
    Vignette example built from Clarity query for future surgical cases
    """

    pod_orc: str
    or_case_id: int
    SurgeryDateClarity: datetime
