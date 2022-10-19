import importlib
from pathlib import Path

from sqlalchemy import create_engine
from sqlmodel import Session

from config.settings import settings

emap_engine = create_engine(settings.STAR_URL, echo=True)
caboodle_engine = create_engine(settings.CABOODLE_URL, echo=True)
clarity_engine = create_engine(settings.CLARITY_URL, echo=True)


def get_caboodle_session():
    with Session(caboodle_engine) as caboodle_session:
        yield caboodle_session


def get_clarity_session():
    with Session(clarity_engine) as clarity_session:
        yield clarity_session


def get_emap_session():
    with Session(emap_engine) as emap_session:
        yield emap_session


def prepare_query(module: str, env: str = settings.ENV) -> str:
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
