import pytest

from fastapi.testclient import TestClient
from sqlmodel import Session
import pandas as pd

from utils import get_model_from_route
from utils.dash import validate_json, df_from_models


@pytest.mark.app
def test_request_json_data(session: Session, client: TestClient):
    """
    Checks that the data from the mock API matches the model
    """
    resp = client.get("/sitrep")
    assert resp.status_code == 200
    model = get_model_from_route("sitrep", "read")
    model_instances = validate_json(resp.json(), model)
    assert isinstance(model_instances[0], model)


@pytest.mark.app
def test_df_from_models(session: Session, client: TestClient):
    """
    Checks we can generate a Pandas data frame from the requests JSON
    """
    resp = client.get("/sitrep")
    assert resp.status_code == 200
    model = get_model_from_route("sitrep", "read")
    model_instances = validate_json(resp.json(), model)
    df = df_from_models(model_instances)
    assert isinstance(df, pd.DataFrame)
    assert df.empty is False
