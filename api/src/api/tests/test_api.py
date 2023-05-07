from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_app():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}
