import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from api.main import app
from app.utils import json_to_pandas_via_pydantic


def test_request_json_data(session: Session, client: TestClient):
    resp = client.get("/results/")
    assert resp.status_code == 200
    d = json_to_pandas_via_pydantic()
