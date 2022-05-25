# ./conftest.py
# for sharing fixtures between files
import pytest

# from pathlib import Path
# from collections import namedtuple
from fastapi.testclient import TestClient
from sqlmodel import Session

# this next step in turn runs api.models as an import
from api.main import app, get_session
from mock.mock import make_mock_db_in_memory


# https://sqlmodel.tiangolo.com/tutorial/fastapi/tests
# NB: session arg is the _name_ not the _scope_ here and
# refers to the db session not the pytest session
@pytest.fixture(name="session")
def session_fixture():
    # NOTE: use the same mock functions for testing as we do for development
    engine = make_mock_db_in_memory()
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_env_uds_vars(monkeypatch):
    # https://docs.pytest.org/en/latest/how-to/monkeypatch.html#monkeypatching-environment-variables
    monkeypatch.setenv("UDS_USER", "BigBird")
    monkeypatch.setenv("UDS_PWD", "Sesame")
    monkeypatch.setenv("UDS_HOST", "172.16.149.132")
