# ./conftest.py
# for sharing fixtures between files
import pytest
from sqlmodel import Session, create_engine

sqlite_file_name = "data/raw/sample.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}


@pytest.fixture
def mock_env_uds_vars(monkeypatch):
    # https://docs.pytest.org/en/latest/how-to/monkeypatch.html#monkeypatching-environment-variables
    monkeypatch.setenv("UDS_USER", "BigBird")
    monkeypatch.setenv("UDS_PWD", "Sesame")
    monkeypatch.setenv("UDS_HOST", "172.16.149.132")


@pytest.fixture
def mock_sample_db():
    engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)
    with Session(engine) as session:
        yield session
