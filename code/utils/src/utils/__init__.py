import collections


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
