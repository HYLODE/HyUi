"""
Unit tests for the electives API module
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app  # type: ignore
import arrow
import pandas as pd

client = TestClient(app)


@pytest.mark.smoke
@pytest.mark.skipif(
    os.environ["TEST_LEVEL"] == "SKIP_BROKEN_TESTS",
    reason="FIXME: mock data not available",
)
def test_get_results_electives(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/electives")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


@pytest.mark.api
@pytest.mark.skipif(
    os.environ["TEST_LEVEL"] == "SKIP_BROKEN_TESTS",
    reason="FIXME: mock data not available",
)
def test_get_results_electives_content_match(
    session: Session, client: TestClient, mock_df_electives: pd.DataFrame
):
    """
    Specific test for electives
    Provided here as an example
    Will need duplicating and re-writing for each endpoint
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/electives")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

    res = data[0]

    assert isinstance(res["PrimaryMrn"], str)
    assert isinstance(res["PatientKey"], int)
    assert isinstance(res["AgeInYears"], int)
    assert isinstance(res["AdmissionService"], str)
    assert isinstance(res["Priority"], str)
    assert isinstance(res["Status"], str)
    assert isinstance(res["SurgicalService"], str)
    assert isinstance(res["Type"], str)

    # should load the first row of the mock data directly from file
    df0 = mock_df_electives.loc[0]

    # check that the API delivers the same data
    assert str(df0["PrimaryMrn"]) == str(res["PrimaryMrn"])
    assert df0["PatientKey"] == res["PatientKey"]
    assert df0["AgeInYears"] == res["AgeInYears"]
    assert df0["AdmissionService"] == res["AdmissionService"]
    assert df0["Priority"] == res["Priority"]
    assert df0["Status"] == res["Status"]
    assert df0["SurgicalService"] == res["SurgicalService"]
    assert df0["Type"] == res["Type"]
    assert (
        df0["PlacedOnWaitingListDate"]
        == arrow.get(res["PlacedOnWaitingListDate"]).date()
    )
