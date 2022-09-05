import dash_daq as daq
import pandas as pd
from dash import Input, Output, callback, get_app, html
from flask_caching import Cache

from apps import AppColors
from apps.pages.census.callbacks import store_depts_fn
from apps.pages.home import BPID, CACHE_TIMEOUT
from config.settings import settings

COLORS = AppColors()
BAR_SIZE = 16

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
    dept_name = DEPT_T03
    bar_label = "UCH T03"
    dept = df[df["department"] == dept_name]
    dept = dept.squeeze()  # force to series
    bar_val = dept["patients"]
    bar_max = bar_val + dept["empties"] - dept["closed"]
    bar_size = BAR_SIZE * bar_max
    bar_label = f"{bar_label}: {bar_val}/{bar_max} beds"
    # NOTE: this does not work? maybe a CSS thing??
    # green, amber, red = bar_max - BAR_SIZE, bar_max - 5, bar_max
    # bar_color={"gradient": True, "ranges":{"green":[0,green],"#FF851B":[green,amber],"#F012BE":[amber,red]}},
    # for debugging
    if bar_val >= bar_max - 1:
        bar_color = COLORS.red
    elif bar_val >= bar_max - 3:
        bar_color = COLORS.orange
    else:
        bar_color = COLORS.green
    bar = daq.GraduatedBar(
        value=bar_val,
        max=bar_max,
        size=bar_size,
        showCurrentValue=True,
        color=bar_color,
        label=bar_label,
    )
    res = html.Div([bar])
    return res


@callback(
    Output(f"{BPID}daq_bar_gwb", "children"),
    Input(f"{BPID}dept_data", "data"),
    prevent_initial_call=True,
)
def gen_daq_bar_gwb(data: list):
    df = pd.DataFrame.from_records(data)
    dept_name = DEPT_GWB
    bar_label = "Grafton Way"
    dept = df[df["department"] == dept_name]
    dept = dept.squeeze()  # force to series
    bar_val = dept["patients"]
    bar_max = bar_val + dept["empties"] - dept["closed"]
    bar_size = BAR_SIZE * bar_max
    bar_label = f"{bar_label}: {bar_val}/{bar_max} beds"
    # NOTE: this does not work? maybe a CSS thing??
    # green, amber, red = bar_max - 10, bar_max - 5, bar_max
    # bar_color={"gradient": True, "ranges":{"green":[0,green],"#FF851B":[green,amber],"#F012BE":[amber,red]}},
    # for debugging
    if bar_val >= bar_max - 1:
        bar_color = COLORS.red
    elif bar_val >= bar_max - 3:
        bar_color = COLORS.orange
    else:
        bar_color = COLORS.green
    bar = daq.GraduatedBar(
        value=bar_val,
        max=bar_max,
        size=bar_size,
        showCurrentValue=True,
        color=bar_color,
        label=bar_label,
    )
    res = html.Div([bar])
    return res


@callback(
    Output(f"{BPID}daq_bar_wms", "children"),
    Input(f"{BPID}dept_data", "data"),
    prevent_initial_call=True,
)
def gen_daq_bar_wms(data: list):
    df = pd.DataFrame.from_records(data)
    dept_name = DEPT_WMS
    bar_label = "Westmoreland St"
    dept = df[df["department"] == dept_name]
    dept = dept.squeeze()  # force to series
    bar_val = dept["patients"]
    bar_max = bar_val + dept["empties"] - dept["closed"]
    bar_size = 10 * bar_max
    bar_label = f"{bar_label}: {bar_val}/{bar_max} beds"
    # NOTE: this does not work? maybe a CSS thing??
    # green, amber, red = bar_max - 10, bar_max - 5, bar_max
    # bar_color={"gradient": True, "ranges":{"green":[0,green],"#FF851B":[green,amber],"#F012BE":[amber,red]}},
    # for debugging
    if bar_val >= bar_max - 1:
        bar_color = COLORS.red
    elif bar_val >= bar_max - 3:
        bar_color = COLORS.orange
    else:
        bar_color = COLORS.green
    bar = daq.GraduatedBar(
        value=bar_val,
        max=bar_max,
        size=bar_size,
        showCurrentValue=True,
        color=bar_color,
        label=bar_label,
    )
    res = html.Div([bar])
    return res


# @callback(
#     Output(f"{BPID}daq_bar_nhnn0", "children"),
#     Input(f"{BPID}dept_data", "data"),
#     prevent_initial_call=True,
# )
# def gen_daq_bar_nhnn0(data: list):
#     df = pd.DataFrame.from_records(data)
#     dept = df[df["department"] == DEPT_NHNN0]
#     res = (daq.GraduatedBar(value=dept["patients"], label="NHNN0"),)
#     return res


# @callback(
#     Output(f"{BPID}daq_bar_nhnn1", "children"),
#     Input(f"{BPID}dept_data", "data"),
#     prevent_initial_call=True,
# )
# def gen_daq_bar_nhnn1(data: list):
#     df = pd.DataFrame.from_records(data)
#     dept = df[df["department"] == DEPT_NHNN1]
#     res = (daq.GraduatedBar(value=dept["patients"], label="NHNN1"),)
#     return res
