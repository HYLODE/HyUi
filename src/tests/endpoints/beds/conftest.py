# ./conftest.py
# for sharing fixtures between files
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

# this next step in turn runs api.models as an import
from api.main import app
from utils.api import get_emap_session
from mock.mock import (  # type: ignore
    make_mock_db_in_memory,
    df_from_file,
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

    app.dependency_overrides[get_emap_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def mock_df_beds():
    """
    Use electives data as baseline exemplar for testing
    """
    df = df_from_file("census")
    return df
