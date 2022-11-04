from api.main import app
from fastapi.testclient import TestClient

from models.sitrep import SitrepRow

client = TestClient(app)


def test_get_mock_live_ui():
    response = client.get("/mock/sitrep/live/T03/ui")
    assert response.status_code == 200

    rows = [SitrepRow.parse_obj(row) for row in response.json()]
    assert len(rows) > 0
