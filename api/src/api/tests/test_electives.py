# type: ignore
from api.main import app
from fastapi.testclient import TestClient

from models.electives import (
    SurgData,
    PreassessData,
    MergedData,
    LabData,
    EchoWithAbnormalData,
    ObsData,
)

client = TestClient(app)


def test_get_mock_preassess() -> None:
    response = client.get("/mock/electives/preassessment/")
    assert response.status_code == 200

    rows = [PreassessData.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_get_mock_cases() -> None:
    response = client.get("/mock/electives/case_booking/")
    assert response.status_code == 200

    rows = [SurgData.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_get_mock_labs() -> None:
    response = client.get("/mock/electives/labs/")
    assert response.status_code == 200

    elective_rows = [LabData.parse_obj(row) for row in response.json()]
    assert len(elective_rows) > 0


def test_get_mock_electives() -> None:
    response = client.get("/mock/electives/")
    assert response.status_code == 200

    elective_rows = [MergedData.parse_obj(row) for row in response.json()]
    assert len(elective_rows) > 0


def test_mock_echo() -> None:
    response = client.get("/mock/electives/echo/")
    assert response.status_code == 200

    rows = [EchoWithAbnormalData.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_mock_obs() -> None:
    response = client.get("/mock/electives/obs/")
    assert response.status_code == 200

    rows = [ObsData.parse_obj(row) for row in response.json()]
    assert len(rows) > 0
