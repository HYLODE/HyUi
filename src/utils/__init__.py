import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CensusDict:
    csn: int
    mrn: str
    name: str
    dob: datetime.date
    sex: str
    ethnicity: List[str]
    postcode: str
    admission_dt: datetime.datetime
    discharge_dt: Optional[datetime.datetime]
    bed_code: str
    bay_code: str
    bay_type: str
    ward_code: str
