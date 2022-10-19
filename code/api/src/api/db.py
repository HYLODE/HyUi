import importlib
from pathlib import Path

from config.settings import settings


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
