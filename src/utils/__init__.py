# src/utils/__init__.py

import collections
import importlib
from pathlib import Path

from sqlmodel import Session, create_engine

from config.settings import settings  # type: ignore

emap_engine = create_engine(settings.DB_URL, echo=True)
caboodle_engine = create_engine(settings.CABOODLE_URL, echo=True)


def get_caboodle_session():
    with Session(caboodle_engine) as caboodle_session:
        yield caboodle_session


def get_emap_session():
    with Session(emap_engine) as emap_session:
        yield emap_session


def prepare_query(module: str, env: str = settings.ENV) -> str:
    choice = {"prod": "LIVE", "dev": "MOCK"}
    module_path = gen_module_path(module)
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


def gen_module_path(name: str, root: str = settings.MODULE_ROOT) -> str:
    """
    Concatenates strings into a module path
    e.g. 'api' and 'consults' becomes 'api.consults'
    """
    return f"{root}.{name}"


def get_model_from_route(route: str, subclass: str = None):
    """
    Uses the route to define the (sub)package storing the model e.g. if route =
    `foo` then the model will be in `foo/model.py` and called `foo`

    :param      route:     The route
    :type       route:     str
    :param      subclass:  The subclass
    :type       subclass:  str

    :returns:   The model from route.
    :rtype:     { return_type_description }
    """
    model_path = gen_module_path(route.lower()) + ".model"
    route_title_case = route.title()
    if subclass:
        route_title_case = f"{route_title_case}{subclass}"
    model = getattr(importlib.import_module(model_path), route_title_case)  # noqa
    return model


def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    via https://stackoverflow.com/a/30655448/992999
    """
    for key, value in overrides.items():
        if isinstance(value, collections.abc.Mapping) and value:
            # note recursive
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


def get_dict_from_list(llist, kkey, vval):
    """
    Given a list of dictionaries, and a key:value pair, will return the matching
    dictionary
    """
    matches = 0
    for ddict in llist:
        if ddict[kkey] == vval:
            res = ddict
            matches += 1
    if matches == 0:
        return {}
    elif matches == 1:
        return res
    else:
        raise ValueError(f"{matches} matches for {kkey}={vval}; expected only 1")
