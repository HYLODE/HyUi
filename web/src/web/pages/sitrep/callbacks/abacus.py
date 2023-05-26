import numpy as np
from dash import Input, Output, State, callback
from web.pages.sitrep import ids

TOTAL_BEDS = 24
EMERGENCY_AVG = 3
DISCHARGE_PROB = 0.1
OCCUPIED_BEDS = 18
ELECTIVE_TOTAL = 20
ELECTIVE_PROB = 0.1
N_TRIALS = 10000
EXTRA_BEDS = 5


class Abacus:
    def __init__(self, dept: str):
        self.dept = dept
        self.electives_data = self._get_electives_data()
        self.emergencies_data = self._get_emergencies_data()
        self.discharges_data = self._get_discharges_data()
        self.current_data = self._get_current_beds()

        self.electives_graph = self._generate_graph("electives", self.electives_data)
        self.emergencies_graph = self._generate_graph(
            "emergencies", self.emergencies_data
        )
        self.discharges_graph = self._generate_graph("discharges", self.discharges_data)
        self.current_graph = self._generate_graph("current_beds", self.current_data)

        self.overall_pmf = self._combine_probabilities()

        self.overall_graph = self._generate_graph("overall", self.overall_pmf)

    def _combine_probabilities(self) -> np.array:
        overall_pmf = np.convolve(
            np.convolve(
                np.convolve(self.electives_data, self.emergencies_data),
                self.discharges_data,
            ),
            self.current_data,
        )
        overall_cmf = np.cumsum(overall_pmf[::-1])
        overall_cmf = overall_cmf / overall_cmf[-1]
        return overall_cmf[::-1]

    def _get_electives_data(self) -> np.array:
        return np.histogram(
            np.random.binomial(ELECTIVE_TOTAL, ELECTIVE_PROB, N_TRIALS),
            bins=np.arange(0, TOTAL_BEDS + 1),
            density=True,
        )[0]

    def _get_emergencies_data(self) -> np.array:
        return np.histogram(
            np.random.poisson(EMERGENCY_AVG, N_TRIALS),
            bins=np.arange(0, TOTAL_BEDS + 1),
            density=True,
        )[0]

    def _get_discharges_data(self) -> np.array:
        return np.negative(
            np.histogram(
                np.random.binomial(OCCUPIED_BEDS, DISCHARGE_PROB, N_TRIALS),
                bins=np.arange(0, TOTAL_BEDS + 1),
                density=True,
            )[0]
        )

    def _get_current_beds(self) -> np.array:
        return np.where(np.arange(TOTAL_BEDS) == OCCUPIED_BEDS, 1, 0)

    def _generate_graph(self, tap: str, data: np.array) -> dict:
        return {
            "data": [
                {
                    "x": np.arange(0, (TOTAL_BEDS + EXTRA_BEDS)),
                    "y": data,
                    "type": "bar",
                    "name": "Probability",
                    "marker": {
                        "line": {
                            "color": "black",
                            "width": 1,
                        }
                    },
                    "width": 0.9,
                }
            ],
            "layout": {
                "title": tap.capitalize(),
                "xaxis": {"title": "Beds"},
                "yaxis": {"title": "Probability"},
                "bargap": 0,
                "bargroupgap": 0,
            },
        }


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
    abacus_instance = Abacus(dept)
    return abacus_instance.overall_graph


def create_callback(tap: str) -> tuple:
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
    def _show_graph(dept: str):  # type: ignore
        abacus_instance = Abacus(dept)
        return getattr(abacus_instance, f"{tap}_graph")

    return _modal, _show_graph


for tap in ["electives", "emergencies", "discharges"]:
    modal_callback, show_graph_callback = create_callback(tap)


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
