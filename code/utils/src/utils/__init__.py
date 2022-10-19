import collections
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
    module_path = gen_module_path(module, "api")
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
