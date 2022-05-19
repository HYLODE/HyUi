from fastapi.testclient import TestClient

from src.api.main import app
from src.api.main import Settings

client = TestClient(app)


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "hyui pong!"}


def test_settings_uds_user(mock_env_uds_vars):
    settings = Settings()
    assert settings.UDS_USER == "BigBird"
    assert settings.UDS_PWD == "Sesame"
    assert settings.UDS_HOST == "172.16.149.132"
