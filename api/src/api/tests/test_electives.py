from datetime import date, datetime

from api.convert import to_data_frame
from api.electives.wrangle import prepare_electives
from api.main import app
from fastapi.testclient import TestClient

from models.electives import (
    CaboodleCaseBooking,
    ClarityPostopDestination,
    CaboodlePreassessment,
    ElectiveSurgCase,
)

client = TestClient(app)


def test_get_mock_preassess():
    response = client.get("/mock/electives/preassessment")
    assert response.status_code == 200

    rows = [CaboodlePreassessment.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_get_mock_pod():
    response = client.get("/mock/electives/postop_destination")
    assert response.status_code == 200

    rows = [ClarityPostopDestination.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_get_mock_cases():
    response = client.get("/mock/electives/case_booking")
    assert response.status_code == 200

    rows = [CaboodleCaseBooking.parse_obj(row) for row in response.json()]
    assert len(rows) > 0


def test_get_mock_electives():
    response = client.get("/mock/electives")
    assert response.status_code == 200

    elective_rows = [ElectiveSurgCase.parse_obj(row) for row in response.json()]
    assert len(elective_rows) > 0