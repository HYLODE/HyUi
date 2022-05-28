import requests
import pandas as pd
from sqlmodel import SQLModel
from api.models import ResultsRead


def get_results_response(url: str) -> list[dict[str, str]]:
    """
    Given a URL return JSON
    """
    request_response = requests.get(url)
    return request_response.json()  # type: ignore


def validate_json(json_list: list[dict[str, str]], model: SQLModel) -> list[SQLModel]:
    """
    Validate list of json formatted strings
    """
    model_instances = [model(**i) for i in json_list]
    return model_instances


def df_from_models(model_list: list[SQLModel]) -> pd.DataFrame:
    """
    Generate a Pandas DataFrame from a list of SQLModels
    """
    list_dicts = [model_list[i].dict() for i, val in enumerate(model_list)]
    df = pd.DataFrame(list_dicts)
    return df


def df_from_url(url: str, model: SQLModel = ResultsRead) -> pd.DataFrame:
    """
    Generate a Pandas DataFrame for a URL
    A convenience function that wraps the separate steps above
    """
    resp = get_results_response(url)
    model_instances = validate_json(resp, model)
    df = df_from_models(model_instances)
    return df


def df_from_store(data: dict, model: SQLModel = ResultsRead) -> pd.DataFrame:
    """
    Generate a Pandas DataFrame for dictionary
    Necessary when using dcc.Store from Plotly Dash
    A convenience function that wraps the separate steps above
    """
    model_instances = validate_json(data, model)
    df = df_from_models(model_instances)
    return df
