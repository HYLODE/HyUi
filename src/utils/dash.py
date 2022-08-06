from typing import Dict
import requests
import pandas as pd
from sqlmodel import SQLModel


def get_results_response(url: str, payload: Dict = {}):
    """
    Given a URL return JSON list of dictionaries
    """
    request_response = requests.get(url, params=payload)
    try:
        list_of_dicts = request_response.json()["data"]
    except (TypeError, KeyError) as e:
        # likely in dev environment where data is returned directly
        # so you have just tried to use a key to select from a list
        print(e)
        list_of_dicts = request_response.json()
    assert type(list_of_dicts) is list
    return list_of_dicts  # type: ignore


def validate_json(json_list, model: SQLModel, to_dict=False):
    """
    Validate list of json formatted strings
    """
    model_instances = [model(**i) for i in json_list]  # type: ignore
    if to_dict:
        model_instances =[i.dict() for i in model_instances]
    return model_instances


def df_from_models(model_list) -> pd.DataFrame:
    """
    Generate a Pandas DataFrame from a list of SQLModels
    """
    list_dicts = [model_list[i].dict() for i, val in enumerate(model_list)]
    df = pd.DataFrame(list_dicts)
    return df


def df_from_url(
    url: str, model: SQLModel, request_response: bool = False
) -> pd.DataFrame:
    """
    Generate a Pandas DataFrame for a URL
    A convenience function that wraps the separate steps above
    """
    resp = get_results_response(url)
    if request_response:
        # because packaged as dict via requests
        resp = resp["data"]  # type: ignore
    model_instances = validate_json(resp, model)
    df = df_from_models(model_instances)
    return df


def df_from_store(data: dict, model: SQLModel) -> pd.DataFrame:
    """
    Generate a Pandas DataFrame for dictionary
    Necessary when using dcc.Store from Plotly Dash
    A convenience function that wraps the separate steps above
    """
    model_instances = validate_json(data, model)  # type: ignore
    df = df_from_models(model_instances)
    return df
