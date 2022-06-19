import arrow
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app  # type: ignore

client = TestClient(app)


@pytest.mark.smoke
@pytest.mark.api
def test_read_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "hyui pong!"}


@pytest.mark.smoke
@pytest.mark.api
def test_get_results_sitrep(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/sitrep")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


@pytest.mark.smoke
@pytest.mark.api
def test_get_results_exemplar(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database and those data match those
    in the original HDF file
    Uses sitrep only as an example so doesn't check contents just function
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/sitrep")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


@pytest.mark.api
def test_get_results_sitrep_content_match(
    session: Session, client: TestClient, mock_df: pd.DataFrame
):
    """
    Specific test for sitrep
    Provided here as an example
    Will need duplicating and re-writing for each endpoint
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/sitrep")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

    res = data[0]

    assert isinstance(res["name"], str)
    assert isinstance(res["mrn"], str)
    assert isinstance(res["dob"], str)
    assert isinstance(res["is_proned_1_4h"], bool)

    df0 = mock_df.loc[0]

    assert df0["name"] == res["name"]
    assert str(df0["mrn"]) == str(res["mrn"])
    assert df0["dob"] == arrow.get(res["dob"]).date()
    assert df0["is_proned_1_4h"] == res["is_proned_1_4h"]


@pytest.mark.api
def test_get_results_sitrep_content_mismatch(
    session: Session, client: TestClient, mock_df
):
    """
    Specific test for sitrep query
    Will need re-writing for each query
    but provided here as an example
    """
    response = client.get("/sitrep")
    data = response.json()
    # DELIBERATELY MISMATCH
    re0 = data[0]
    df1 = mock_df.loc[1]

    with pytest.raises(AssertionError):
        assert df1["dob"] == arrow.get(re0["dob"]).date()
