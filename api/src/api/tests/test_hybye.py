from api.main import app
from fastapi.testclient import TestClient

from models.hybye import HospitalFlowRow

client = TestClient(app)


def test_get_mock_discharges_for_last_n_days() -> None:
    response = client.get("/mock/hybye/discharge/n_days/28?campuses=UCH")
    assert response.status_code == 200

    assert len(response.json()) == 28

    rendered_response = [HospitalFlowRow.parse_obj(row) for row in response.json()]
    assert rendered_response is not None


def test_mock_no_campuses_behaviour() -> None:
    response = client.get("/mock/hybye/discharge/n_days/28")
    assert response.status_code == 200

    assert len(response.json()) == 0


def test_mock_invalid_campus_behaviour() -> None:
    response = client.get("/mock/hybye/discharge/n_days/100?campuses=KCH")
    assert response.status_code == 400
