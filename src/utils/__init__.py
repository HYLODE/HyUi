# src/utils/__init__.py

import collections
from importlib import import_module
from config.settings import settings  # type: ignore


def gen_module_path(name: str, root: str = settings.MODULE_ROOT) -> str:
    """
    Concatenates strings into a module path
    e.g. 'api' and 'consults' becomes 'api.consults'
    """
    return f"{root}.{name}"


def get_model_from_route(route: str, subclass: str = None):
    route_title_case = route.title()
    if subclass:
        subclass = subclass.title()
        route_title_case = f"{route_title_case}{subclass}"
    model_path = gen_module_path(route.lower()) + ".model"
    model = getattr(import_module(model_path), route_title_case)  # noqa
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
    Given a list of dictionaries, and a key:value pair, will return the matching dictionary
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
