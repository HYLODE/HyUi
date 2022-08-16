import dash_daq as daq
import pandas as pd
from dash import Input, Output, callback, get_app
from flask_caching import Cache

from apps.pages.census.callbacks import store_depts_fn
from apps.pages.home import BPID, CACHE_TIMEOUT

DEPT_T03 = "UCH T03 INTENSIVE CARE"
DEPT_GWB = "GWB L01 CRITICAL CARE"
DEPT_WMS = "WMS W01 CRITICAL CARE"
DEPT_NHNN0 = "NHNN C0 NCCU"
DEPT_NHNN1 = "NHNN C1 NCCU"

# this structure is necessary for flask_cache
app = get_app()
cache = Cache(
    app.server,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "cache-directory",
    },
)


@callback(
    Output(f"{BPID}dept_data", "data"),
    Input(f"{BPID}query-interval", "n_intervals"),
    # Input(f"{BPID}building_radio", "value"),
)
@cache.memoize(timeout=CACHE_TIMEOUT)
def store_depts(*args, **kwargs):
    args = args + ("",)  # pass empty string as building arg
    return store_depts_fn(*args, **kwargs)


@callback(
    Output(f"{BPID}daq_bar_t03", "children"),
    Input(f"{BPID}dept_data", "data"),
    prevent_initial_call=True,
)
def gen_daq_bar_t03(data: list):
    df = pd.DataFrame.from_records(data)
    dept = df[df["department"] == DEPT_T03]
    res = (daq.GraduatedBar(value=dept["patients"], label="T03"),)
    return res


@callback(
    Output(f"{BPID}daq_bar_gwb", "children"),
    Input(f"{BPID}dept_data", "data"),
    prevent_initial_call=True,
)
def gen_daq_bar_gwb(data: list):
    df = pd.DataFrame.from_records(data)
    dept = df[df["department"] == DEPT_GWB]
    res = (daq.GraduatedBar(value=dept["patients"], label="GWB"),)
    return res


@callback(
    Output(f"{BPID}daq_bar_wms", "children"),
    Input(f"{BPID}dept_data", "data"),
    prevent_initial_call=True,
)
def gen_daq_bar_wms(data: list):
    df = pd.DataFrame.from_records(data)
    dept = df[df["department"] == DEPT_WMS]
    res = (daq.GraduatedBar(value=dept["patients"], label="WMS"),)
    return res


@callback(
    Output(f"{BPID}daq_bar_nhnn0", "children"),
    Input(f"{BPID}dept_data", "data"),
    prevent_initial_call=True,
)
def gen_daq_bar_nhnn0(data: list):
    df = pd.DataFrame.from_records(data)
    dept = df[df["department"] == DEPT_NHNN0]
    res = (daq.GraduatedBar(value=dept["patients"], label="NHNN0"),)
    return res


@callback(
    Output(f"{BPID}daq_bar_nhnn1", "children"),
    Input(f"{BPID}dept_data", "data"),
    prevent_initial_call=True,
)
def gen_daq_bar_nhnn1(data: list):
    df = pd.DataFrame.from_records(data)
    dept = df[df["department"] == DEPT_NHNN1]
    res = (daq.GraduatedBar(value=dept["patients"], label="NHNN1"),)
    return res
