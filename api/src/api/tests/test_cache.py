from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_mock_beds_cached() -> None:
    response = client.get("/mock/beds/closed/")
    assert response.headers["Cache-control"] == "public, max-age=300"


def test_mock_beds_skip_cache() -> None:
    skip_cache_headers = {"X-Varnish-Nuke": "1"}
    response = client.get("/mock/beds/closed/", headers=skip_cache_headers)
    print(f"{response.headers=}")
    assert response.headers["Cache-control"] == "no-cache"


def test_mock_beds_alter_ttl() -> None:
    max_ttl = "max-age=10"
    skip_cache_headers = {"x-cache-control": max_ttl}
    response = client.get("/mock/beds/closed/", headers=skip_cache_headers)
    print(f"{response.headers=}")
    assert response.headers["Cache-control"] == max_ttl
