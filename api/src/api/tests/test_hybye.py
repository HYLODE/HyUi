from api.main import app
from fastapi.testclient import TestClient

from models.hybye import DischargeRow

client = TestClient(app)


def test_get_mock_discharges_for_last_n_days():
    response = client.get("/mock/hybye/discharge/n_days/28")
    assert response.status_code == 200

    rendered_response = [DischargeRow.parse_obj(row) for row in response.json()]

    assert len(response.json()) == 28
