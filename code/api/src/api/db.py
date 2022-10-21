import importlib
from functools import lru_cache
from pathlib import Path

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from api.config import get_settings


@lru_cache()
def _caboodle_engine(settings=Depends(get_settings)) -> Engine:
    return create_engine(settings.caboodle_dsn, echo=True, future=True)


def get_caboodle_session(engine=Depends(_caboodle_engine)) -> Session:
    with Session(engine) as session:
        yield session


@lru_cache()
def _star_engine(settings=Depends(get_settings)) -> Engine:
    return create_engine(settings.star_dsn, echo=True, future=True)


def get_star_session(engine=Depends(_star_engine)) -> Session:
    with Session(engine) as session:
        yield session


@lru_cache()
def _clarity_engine(settings=Depends(get_settings)) -> Engine:
    return create_engine(settings.clarity_dsn, echo=True, future=True)


def get_clarity_session(engine=Depends(_clarity_engine)) -> Session:
    with Session(engine) as session:
        yield session


# TODO: Remove this function and env.
def prepare_query(module: str, env: str = get_settings().env) -> str:
    """
    Returns a string version of the query as defined in the module

    :param      module:  The module
    :type       module:  str
    :param      env:     The environment
    :type       env:     str

    :returns:   { description_of_the_return_value }
    :rtype:     str
    """
    choice = {"prod": "LIVE", "dev": "MOCK"}
    module_path = f"api.{module}"
    query_name = f"QUERY_{choice[env]}_PATH"
    try:
        q = getattr(importlib.import_module(module_path), query_name)
    except AttributeError as e:
        print(
            f"!!! Check that you have provided a SQL file {choice[env].lower()}.sql in src/api/{module}"  # noqa
        )
        raise e
    print(f"--- INFO: running {choice[env]} query")
    query = Path(q).read_text()
    return query
