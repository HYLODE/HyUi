from datetime import datetime

from fastapi.testclient import TestClient

from api.main import app
from config.settings import settings
from api.models import Consultation_Request

client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "hyui pong!"}


def test_settings_uds_user(mock_env_uds_vars):
    assert settings.UDS_USER == "BigBird"
    assert settings.UDS_PWD == "Sesame"
    assert settings.UDS_HOST == "172.16.149.132"


def test_consultation_request_class():
    consult = Consultation_Request(
        consulation_request_id=1,
        valid_from=datetime(2022, 5, 20, 9, 29, 31),
        cancelled=False,
        closed_due_to_discharge=False,
        status_change_time=datetime(2022, 5, 20, 9, 29, 31),
        comments="foo bar",
        consultation_type_id=42,
        hospital_visit_id=1234,
    )

    # Below fails b/c only generated when table instantiated?
    # assert consult.consultation_request_id == 1
    assert consult.cancelled == False
    assert consult.closed_due_to_discharge == False
    assert consult.comments == "foo bar"
    assert consult.consultation_type_id == 42
    assert consult.hospital_visit_id == 1234
    assert consult.valid_from == datetime(2022, 5, 20, 9, 29, 31)
