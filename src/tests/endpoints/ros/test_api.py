"""
Unit tests for the ros API module
"""
from sqlite3 import Timestamp
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app  # type: ignore
import arrow
import pandas as pd

client = TestClient(app)


@pytest.mark.smoke
def test_get_results_ros(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/ros")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


@pytest.mark.api
def test_get_results_ros_content_match(
    session: Session, client: TestClient, mock_df_ros: pd.DataFrame
):
    """
    Specific test for oros
    Provided here as an example
    Will need duplicating and re-writing for each endpoint
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/ros")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

    first_result = data[0]

    assert isinstance(first_result["department"], str)
    assert isinstance(first_result["bed_name"], str)
    assert isinstance(first_result["mrn"], int)
    assert isinstance(first_result["encounter"], int)
    assert isinstance(first_result["firstname"], str)
    assert isinstance(first_result["lastname"], str)
    assert isinstance(first_result["date_of_birth"], str)
    assert isinstance(first_result["hospital_admission_time"], str)
    assert isinstance(first_result["location_admission_time"], str)
    assert isinstance(first_result["ros_order_datetime"], str)
    assert isinstance(first_result["ros_lab_result_id"], float)
    assert isinstance(first_result["ros_value_as_text"], str)
    assert isinstance(first_result["mrsa_order_datetime"], str)
    assert isinstance(first_result["mrsa_lab_result_id"], float)
    assert isinstance(first_result["mrsa_value_as_text"], str)

    api_result_keys = sorted(first_result.keys())

    # API result has an ID column
    assert api_result_keys.count("id") == 1

    # Mock data doesn't have this column, remove it before assertion
    api_result_keys.remove("id")

    # Validate mock_df has same columns as API result
    assert sorted(list(mock_df_ros)) == api_result_keys

    df0 = mock_df_ros.loc[0]

    for key in list(mock_df_ros):
        # dates from pandas are of a different type and need to be handled
        if isinstance(df0[key], Timestamp):
            assert (key, df0[key]) == (key, arrow.get(first_result[key]).date())
        else:
            # assert as a tuple so if this fails the key will be printed in the error
            assert (key, df0[key]) == (key, first_result[key])
