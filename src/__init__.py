# src/wrangle/__init__.py

import pandas as pd
import requests

def get_hylode_data(file_or_url: str, dtype: dict = conf.COLS_DTYPE, dev: bool = False) -> pd.DataFrame:
    """
    Reads a data.

    :param      file_or_url:  The file or url
    :param      dev:    if True works on a file else uses requests and the API
    :param      dtype:  as per dtype in pd.from_dict or pd.read_json
                        enforces datatypes

    :returns:   pandas dataframe
    :rtype:     pandas dataframe
    """
    if not dev:
        r = requests.get(file_or_url)
        assert r.status_code == 200
        df = pd.DataFrame.from_dict(r.json()["data"])
    else:
        df = pd.read_json(file_or_url)
    for k, v in dtype.items():
        df[k] = df[k].astype(v)
    return df
