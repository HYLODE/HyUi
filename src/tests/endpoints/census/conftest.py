# ./conftest.py
# for sharing fixtures between files
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

# this next step in turn runs api.models as an import
from api.main import app, get_session  # type: ignore
from mock.mock import (  # type: ignore
    make_mock_db_in_memory,
    make_mock_df,
    path_to_hdf_file,
)

ROUTE_NAME = "census"


# https://sqlmodel.tiangolo.com/tutorial/fastapi/tests
# NB: session arg is the _name_ not the _scope_ here and
# refers to the db session not the pytest session
@pytest.fixture(name="session")
def session_fixture():
    """
    Defaults to sitrep as the route as a simple route for most tests
    """
    # NOTE: use the same mock functions for testing as we do for development
    # NOTE: using sitrep route as the simplest
    engine = make_mock_db_in_memory(ROUTE_NAME)
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
def mock_minimal_df():
    data = dict(
        id=[1, 2, 3],
        age=[21, 31, 41],
        initials=["JJ", "KK", "LL"],
    )
    df = pd.DataFrame(data)
    return df


@pytest.fixture(scope="session")
def mock_df_sitrep():
    """
    Use sitrep data as baseline exemplar for testing
    """
    df = make_mock_df(path_to_hdf_file("sitrep"))
    return df


@pytest.fixture(scope="session")
def mock_df_census():
    """
    Generate data frame from mock census data for testing
    """
    df = make_mock_df(path_to_hdf_file("census"))
    return df
