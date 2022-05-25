import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app
from mock.mock import make_mock_df
import arrow


@pytest.mark.smoke
def test_read_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "hyui pong!"}


@pytest.mark.smoke
def test_get_results(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/results/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_results_consults_ed(session: Session, client: TestClient):
    """
    Specific test for ED consults query
    Will need re-writing for each query
    but provided here as an example
    """
    response = client.get("/results/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    res = data[0]

    assert isinstance(res["firstname"], str)
    assert isinstance(res["lastname"], str)
    assert isinstance(res["date_of_birth"], str)
    assert isinstance(res["cancelled"], bool)

    df = make_mock_df()
    df0 = df.loc[0]

    assert df0.firstname == res["firstname"]
    assert df0.lastname == res["lastname"]
    assert df0.date_of_birth.date() == arrow.get(res["date_of_birth"]).date()
    assert df0.cancelled == res["cancelled"]


def test_get_results_consults_ed_mismatch(session: Session, client: TestClient):
    """
    Specific test for ED consults query
    Will need re-writing for each query
    but provided here as an example
    """
    response = client.get("/results/")
    data = response.json()
    df = make_mock_df()
    # DELIBERATELY MISMATCH
    re0 = data[0]
    df1 = df.loc[1]

    with pytest.raises(AssertionError):
        assert df1.date_of_birth == arrow.get(re0["date_of_birth"]).date()
