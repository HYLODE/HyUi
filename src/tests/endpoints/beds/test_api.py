# src/tests/beds/test_api.py
"""
Unit tests for the beds API module
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app  # type: ignore
from datetime import date, datetime
import arrow
import pandas as pd

client = TestClient(app)


@pytest.mark.smoke
def test_get_results_beds(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/beds")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


@pytest.mark.api
def test_get_results_beds_content_match(
    session: Session, client: TestClient, mock_df_beds: pd.DataFrame
):
    """
    Specific test for beds
    Provided here as an example
    Will need duplicating and re-writing for each endpoint
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/beds")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

    res = data[3]

    assert isinstance(res["patient_class"], str)
    assert isinstance(res["firstname"], str)
    assert isinstance(res["lastname"], str)
    assert isinstance(res["mrn"], str)
    assert isinstance(res["encounter"], int)
    assert isinstance(arrow.get(res["date_of_birth"]).date(), date)

    assert isinstance(res["department"], str)
    assert isinstance(res["location_id"], int)
    assert isinstance(res["location_string"], str)

    assert isinstance(arrow.get(res["ovl_admission"]).datetime, datetime)
    assert isinstance(res["ovl_hv_id"], int)

    assert isinstance(arrow.get(res["cvl_admission"]).datetime, datetime)
    assert isinstance(arrow.get(res["cvl_discharge"]).datetime, datetime)
    assert isinstance(res["cvl_hv_id"], int)

    assert isinstance(res["ovl_ghost"], bool)
    assert isinstance(res["occupied"], bool)

    # should load the first row of the mock data directly from file
    df3 = mock_df_beds.loc[3]

    # check that the API delivers the same data
    assert df3["firstname"] == res["firstname"]
    assert df3["lastname"] == res["lastname"]
    assert str(df3["mrn"]) == str(res["mrn"])
    assert df3["date_of_birth"] == arrow.get(res["date_of_birth"]).date()
    assert df3["location_string"] == res["location_string"]
    assert df3["department"] == res["department"]
