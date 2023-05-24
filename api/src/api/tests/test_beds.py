# type: ignore
from fastapi.testclient import TestClient

from api.main import app
from models.beds import Bed

client = TestClient(app)


def test_get_mock_beds_closed() -> None:
    response = client.get("/mock/baserow/closed/")
    assert response.status_code == 200

    closed_beds_rows = [Bed.parse_obj(row) for row in response.json()]
    assert len(closed_beds_rows) > 0


def test_get_mock_beds() -> None:
    response = client.get(
        url="/mock/baserow/beds/", params={"department": "UCH T03 INTENSIVE CARE"}
    )
    assert response.status_code == 200
    beds = [Bed.parse_obj(row) for row in response.json()]
    assert len(beds) > 0
