"""
utils for working with the mock json data
"""
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session


def _get_json_rows(this_file, filename: str):
    """
    Return mock data from adjacent mock.json file
    Assumes that data in nested object 'rows'
    """
    with open(this_file.parent / filename, "r") as f:
        mock_json = json.load(f)
    mock_table = mock_json["rows"]
    return mock_table


def _parse_query(
    this_file, query_file: str, session: Session, model: BaseModel, params: Dict = {}
) -> List[BaseModel]:
    """
    generic function that reads a text query from a file, handles parameters
    within the query and then returns after parsing through a pydantic model

    :param query_file:
    :param params:
    :param model:
    :return:
    """
    query = text((this_file.parent / query_file).read_text())
    df = pd.read_sql(query, session.connection(), params=params)
    return [model.parse_obj(row) for row in df.to_dict(orient="records")]
