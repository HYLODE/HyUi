import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.main import app
from config.settings import settings

client = TestClient(app)


@pytest.mark.smoke
def test_read_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "hyui pong!"}
