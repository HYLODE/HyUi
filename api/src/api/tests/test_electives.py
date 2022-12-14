from api.main import app
from fastapi.testclient import TestClient

from models.electives import (
    SurgData,
    PreassessData,
    MergedData,
    LabData,
    EchoData,
    ObsData,
)

client = TestClient(app)


def test_get_mock_preassess():
    response = client.get("/mock/electives/preassessment/")
    assert response.status_code == 200

    rows = [PreassessData.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_get_mock_cases():
    response = client.get("/mock/electives/case_booking/")
    assert response.status_code == 200

    rows = [SurgData.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_get_mock_labs():
    response = client.get("/mock/electives/labs/")
    assert response.status_code == 200

    elective_rows = [LabData.parse_obj(row) for row in response.json()]
    assert len(elective_rows) > 0


def test_get_mock_electives():
    response = client.get("/mock/electives/")
    assert response.status_code == 200

    elective_rows = [MergedData.parse_obj(row) for row in response.json()]
    assert len(elective_rows) > 0


def test_mock_echo():
    response = client.get("/mock/electives/echo/")
    assert response.status_code == 200

    rows = [EchoData.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_mock_obs():
    response = client.get("/mock/electives/obs/")
    assert response.status_code == 200

    rows = [ObsData.parse_obj(row) for row in response.json()]
    assert len(rows) > 0
