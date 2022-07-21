"""
Unit tests for the perrt API module
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app  # type: ignore
import arrow
import pandas as pd

client = TestClient(app)


@pytest.mark.smoke
def test_get_results_perrt_raw(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/perrt/raw")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


@pytest.mark.smoke
def test_get_results_perrt(session: Session, client: TestClient):
    """
    Prove that the test session/client relationship works
    and that there are data in the database
    """
    # https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
    response = client.get("/perrt")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
