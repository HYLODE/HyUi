# import requests
import numpy as np
from dash import Input, Output, State, callback

# from datetime import date, timedelta

# from models.sitrep import Abacus
from web.pages.sitrep import ids

# from web.convert import parse_to_data_frame
# from web.config import get_settings

# from web import ids as store_ids


# temporary variables
TOTAL_BEDS = 24
EMERGENCY_AVG = 3
DISCHARGE_PROB = 0.1
OCCUPIED_BEDS = 18
ELECTIVE_TOTAL = 20
ELECTIVE_PROB = 0.1


# Collect aggregated Electives data for tomorrow only
def _get_electives_data(dept: str) -> np.array:
    # all_elective_pmf = parse_to_data_frame(
    #     requests.get(url=f"{get_settings().api_url}/electives/aggregate/").json(),
    #     Abacus,
    # )

    # # grouped_stores = {
    # #     "UCH": store_ids.SITREP_STORE["T03"] + store_ids.SITREP_STORE["T06"],
    # #     "WMS": store_ids.SITREP_STORE["WMS"],
    # #     "GWB": store_ids.SITREP_STORE["GWB"],
    # #     "NHNN": store_ids.SITREP_STORE["NHNNC1"] + store_ids.SITREP_STORE["NHNNC0"],
    # # }

    # elective_pmf = all_elective_pmf[
    #     (all_elective_pmf["date"] == date.today() + timedelta(days=1))
    #     & (all_elective_pmf["department"].isin(dept))
    # ]

    # return np.array(elective_pmf["probabilities"].values[0])
    return np.random.binomial(ELECTIVE_TOTAL, ELECTIVE_PROB, TOTAL_BEDS)


# Collect aggregated Emergencies data for tomorrow only
def _get_emergencies_data(dept: str) -> np.array:  # noqa
    # get from API
    return np.random.poisson(3, TOTAL_BEDS)


# Collect aggregated Discharges data for tomorrow only
def _get_discharges_data(dept: str) -> np.array:  # noqa
    return np.negative(np.random.binomial(TOTAL_BEDS, DISCHARGE_PROB, TOTAL_BEDS))


def _get_current_beds(dept: str) -> np.array:  # noqa
    return np.ones(OCCUPIED_BEDS)


# Callback for Overall combined chart
@callback(
    Output("overall_graph", "figure"),
    Input(ids.DEPT_SELECTOR, "value"),
    # Input(ids.BEDS_STORE, "data"),
)
def overall_graph(
    dept: str,
    #    beds: list
) -> dict:
    electives = _get_electives_data(dept)
    emergencies = _get_emergencies_data(dept)
    discharges = _get_discharges_data(dept)
    current = _get_current_beds(dept)

    overall_pmf = np.convolve(
        np.convolve(np.convolve(electives, emergencies), discharges), current
    )

    overall_cmf = np.cumsum(overall_pmf)
    if np.sum(overall_cmf) < 0:
        overall_cmf = overall_cmf + 1

    return {
        "data": [overall_cmf],
        "layout": {
            "title": "Overall",
            "xaxis": {"title": "Beds"},
            "yaxis": {"title": "Probability"},
        },
    }


taps = ["electives", "emergencies", "discharges"]
data_funcs = {
    "electives": _get_electives_data,
    "emergencies": _get_emergencies_data,
    "discharges": _get_discharges_data,
}

for tap in taps:

    @callback(
        Output(f"{tap}_model_card", "opened"),
        Input(f"{tap}_button", "n_clicks"),
        State(f"{tap}_model_card", "opened"),
        prevent_initial_call=True,
    )
    def _modal(_: int, opened: bool) -> bool:
        return not opened

    @callback(
        Output(f"{tap}_graph", "figure"),
        Input(ids.DEPT_SELECTOR, "value"),
    )
    def generate_graph(dept: str) -> dict:
        data = data_funcs[tap](dept)
        return {
            "data": [data],
            "layout": {
                "title": tap.capitalize(),
                "xaxis": {"title": "Beds"},
                "yaxis": {"title": "Probability"},
            },
        }


# Callback for progress bar
@callback(
    Output("mane_progress_bar", "sections"),
    Input(ids.DEPT_SELECTOR, "value"),
    # Input(ids.BEDS_STORE, "data"),
    Input("electives_adjustor", "value"),
    Input("emergencies_adjustor", "value"),
    Input("discharges_adjustor", "value"),
)
def mane_progress_bar(
    dept: str,
    # beds: list[dict],
    electives: int,
    emergencies: int,
    discharges: int,
) -> list[dict]:
    norm = TOTAL_BEDS
    n_beds = OCCUPIED_BEDS

    admitted_element = {
        "value": ((n_beds - discharges) / norm),
        "color": "blue",
        "label": "Admitted",
    }
    elective_element = {
        "value": (electives / norm),
        "color": "green",
        "label": "Electives",
    }
    emergency_element = {
        "value": (emergencies / norm),
        "color": "red",
        "label": "Emergencies",
    }
    discharge_element = {
        "value": (discharges / norm),
        "color": "gray",
        "label": "Discharges",
    }

    return [admitted_element, elective_element, emergency_element, discharge_element]
