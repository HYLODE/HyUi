# ./conftest.py
# for sharing fixtures between files
import pytest


@pytest.fixture
def mock_env_uds_vars(monkeypatch):
    # https://docs.pytest.org/en/latest/how-to/monkeypatch.html#monkeypatching-environment-variables
    monkeypatch.setenv("UDS_USER", "BigBird")
    monkeypatch.setenv("UDS_PWD", "Sesame")
    monkeypatch.setenv("UDS_HOST", "172.16.149.132")
