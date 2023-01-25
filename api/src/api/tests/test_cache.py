from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_mock_beds_cached() -> None:
    response = client.get("/mock/beds/?department=T03")
    assert response.headers["Cache-Control"] == "public, max-age=300"


def test_skip_cache() -> None:
    response = client.get("/mock/sitrep/predictions/discharge/individual/T03/")
    assert response.headers["Cache-control"] == "no-cache"
