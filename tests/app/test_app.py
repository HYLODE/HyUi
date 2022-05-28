from fastapi.testclient import TestClient
from sqlmodel import Session
import pandas as pd

from api.models import ResultsRead
import app.utils as utils


def test_request_json_data(session: Session, client: TestClient):
    """
    Checks that the data from the mock API matches the model
    """
    resp = client.get("/results/")
    assert resp.status_code == 200
    model_instances = utils.validate_json(resp.json(), ResultsRead)
    assert isinstance(model_instances[0], ResultsRead)


def test_df_from_models(session: Session, client: TestClient):
    """
    Checks we can generate a Pandas data frame from the requests JSON
    """
    resp = client.get("/results/")
    assert resp.status_code == 200
    model_instances = utils.validate_json(resp.json(), ResultsRead)
    df = utils.df_from_models(model_instances)
    assert isinstance(df, pd.DataFrame)
    assert df.empty is False
