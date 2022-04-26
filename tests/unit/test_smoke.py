import dataclasses
import pytest
from src.utils import CensusDict
import datetime


def test_smoke():
    assert True


def test_CensusDict():
    kenneth = CensusDict(
        1041677024,
        "45570713",
        "Kenneth Lewis",
        datetime.date(1974,1,30),
        "M",
        [],
        "16644",
        datetime.datetime(2021,12,21,21,37),
        None,
        "BY02-18",
        "BY02",
        "Regular",
        "T03"
        )
    assert kenneth.name == "Kenneth Lewis"
    assert kenneth.csn == 1041677024
    assert type(kenneth.mrn) is str
    assert kenneth.dob == datetime.date(1974,1,30)
    kenneth_dict = dataclasses.asdict(kenneth)
    assert kenneth_dict == {
        "csn": "1041677024",
        "mrn": "45570713",
        "name": "Kenneth Lewis",
        "dob": "1998-08-19",
        "sex": "M",
        "ethnicity": [],
        "postcode": "16644",
        "admission_dt": "2021-12-21T21:37:00+00:00",
        "discharge_dt": "",
        "bed_code": "BY02-18",
        "bay_code": "BY02",
        "bay_type": "Regular",
        "ward_code": "T03"
    }



