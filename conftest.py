# ./conftest.py
# for sharing fixtures between files
import pytest
from pathlib import Path
from collections import namedtuple
from sqlmodel import Session, create_engine

from config.settings import settings

# this next step in turn runs api.models as an import
from api.main import app, get_session


# https://sqlmodel.tiangolo.com/tutorial/fastapi/tests
@pytest.fixture(name="session")
def session_fixture():
    # create an in memory database for the session
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
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


@pytest.fixture(scope="session")
def mock_api_records():
    # TODO: seems anti-DRI: this code already drives the API
    # would be better to monkeypath the environment as DEV
    # and then factor out the bits you need and reuse
    db_url = f"sqlite:///src/data/mock/mock.db"
    engine = create_engine(db_url, echo=True)
    f = "src/api/query-mock.sql"
    q = Path(f).read_text()
    with Session(engine) as session:
        results = session.execute(q)
        Record = namedtuple("Record", results.keys())
        records = [Record(*r) for r in results.fetchall()]
    return records
