import pandas as pd

from api import wards
from api.census.router import fetch_mock_census
from api.census.wrangle import aggregate_by_department
from api.main import app
from fastapi.testclient import TestClient

from models.census import CensusDepartment, CensusRow, ClosedBed

client = TestClient(app)


def test_fetch_mock_census():
    census_rows = fetch_mock_census(wards.ALL, [])
    assert len(census_rows) > 0


def test_aggregate_by_department():
    census_rows = fetch_mock_census(wards.ALL, [])

    census_df = pd.DataFrame((row.dict() for row in census_rows))
    aggregated_df = aggregate_by_department(census_df)

    assert len(aggregated_df.index) > 0


def test_get_mock_departments():
    response = client.get("/mock/census/departments")
    assert response.status_code == 200

    census_departments = [CensusDepartment.parse_obj(row) for row in response.json()]
    assert len(census_departments) > 0


def test_get_mock_census():
    response = client.get("/mock/census/")
    assert response.status_code == 200

    census_rows = [CensusRow.parse_obj(row) for row in response.json()]
    assert len(census_rows) > 0


def test_get_mock_beds_closed():
    response = client.get("/mock/census/beds/closed/")
    assert response.status_code == 200

    closed_beds_rows = [ClosedBed.parse_obj(row) for row in response.json()]
    assert len(closed_beds_rows) > 0
