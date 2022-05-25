import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app


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
    print(data[0])
