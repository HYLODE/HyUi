"""
Unit tests for the census API module
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app  # type: ignore
import arrow
import pandas as pd

client = TestClient(app)


@pytest.mark.smoke
def test_get_results_census(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/census")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_results_census_content_match(
    session: Session, client: TestClient, mock_df_census: pd.DataFrame
):
    """
    Specific test for census
    Provided here as an example
    Will need duplicating and re-writing for each endpoint
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/census")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

    res = data[0]

    assert isinstance(res["name"], str)
    assert isinstance(res["mrn"], str)
    assert isinstance(res["csn"], int)
    assert isinstance(res["dob"], str)
    assert isinstance(res["postcode"], str)
    assert isinstance(res["ward_code"], str)
    assert isinstance(res["bay_code"], str)
    assert isinstance(res["bed_code"], str)

    # should load the first row of the mock data directly from file
    df0 = mock_df_census.loc[0]

    # check that the API delivers the same data
    assert df0["name"] == res["name"]
    assert str(df0["mrn"]) == str(res["mrn"])
    assert df0["dob"] == arrow.get(res["dob"]).date()
    assert df0["postcode"] == res["postcode"]
