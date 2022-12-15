from api.main import app
from fastapi.testclient import TestClient

from models.beds import Bed

client = TestClient(app)


def test_get_mock_beds_closed() -> None:
    response = client.get("/mock/beds/closed/")
    assert response.status_code == 200

    closed_beds_rows = [Bed.parse_obj(row) for row in response.json()]
    assert len(closed_beds_rows) > 0
