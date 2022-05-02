import datetime
from src.utils import CensusDict


def test_smoke():
    assert True


def test_CensusDict():
    """
    GIVEN a CensusDict dataclass
    WHEN instantiated
    THEN check name, csn etc
    """
    kenneth = CensusDict(
        1041677024,
        "45570713",
        "Kenneth Lewis",
        datetime.date(1974, 1, 30),
        "M",
        [],
        "16644",
        datetime.datetime(2021, 12, 21, 21, 37),
        None,
        "BY02-18",
        "BY02",
        "Regular",
        "T03",
    )
    assert kenneth.name == "Kenneth Lewis"
    assert kenneth.csn == 1041677024
    assert type(kenneth.mrn) is str
    assert kenneth.dob == datetime.date(1974, 1, 30)
