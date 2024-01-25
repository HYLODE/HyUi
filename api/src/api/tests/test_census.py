# type: ignore
import pandas as pd

from api import wards
from api.census.router import _fetch_mock_census
from api.census.wrangle import (
    aggregate_by_department,
    _aggregate_by_department,
    _split_location_string,
    _remove_non_beds,
)
from api.main import app
from fastapi.testclient import TestClient

from models.census import CensusDepartment, CensusRow

client = TestClient(app)


def test_fetch_mock_census() -> None:
    census_rows = _fetch_mock_census(list(wards.ALL), [])
    assert len(census_rows) > 0


def test_aggregate_by_department() -> None:
    census_rows = _fetch_mock_census(list(wards.ALL), [])

    census_df = pd.DataFrame((row.dict() for row in census_rows))
    aggregated_df = aggregate_by_department(census_df)

    assert len(aggregated_df.index) > 0


def test__aggregate_by_department_handles_nat() -> None:
    census_rows = _fetch_mock_census(list(wards.ALL), [])

    census_df = pd.DataFrame((row.dict() for row in census_rows))

    census_df = _split_location_string(census_df)
    census_df = _remove_non_beds(census_df)

    aggregated_df = _aggregate_by_department(census_df)

    assert len(aggregated_df.index) > 0


def test_get_mock_departments() -> None:
    response = client.get("/mock/census/departments")
    assert response.status_code == 200

    census_departments = [CensusDepartment.parse_obj(row) for row in response.json()]
    assert len(census_departments) > 0


def test_get_mock_census() -> None:
    response = client.get(
        "/mock/census/", params={"departments": "UCH T03 INTENSIVE CARE"}
    )
    assert response.status_code == 200

    census_rows = [CensusRow.parse_obj(row) for row in response.json()]
    assert len(census_rows) > 0
