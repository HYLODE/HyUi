from api import wards
from api.census.router import read_mock_census
from api.census.wrangle import aggregate_by_department


def test_read_mock_census():
    beds = tuple(wards.DEPARTMENTS_MISSING_BEDS.values())
    df = read_mock_census(wards.ALL, beds)

    assert len(df.index) > 0


def test_aggregate_by_department():
    beds = tuple(wards.DEPARTMENTS_MISSING_BEDS.values())
    census_df = read_mock_census(wards.ALL, beds)

    aggregated_df = aggregate_by_department(census_df)

    assert len(aggregated_df.index) > 0
