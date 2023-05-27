import numpy as np
from dash import Input, Output, State, callback
from web.pages.sitrep import ids


BED_NUMBERS = {
    "UCH T03 INTENSIVE CARE": {"occupied": 18, "total": 30},
    "UCH T06 SOUTH PACU": {"occupied": 5, "total": 12},
    "GWB L01 CRITICAL CARE": {"occupied": 7, "total": 10},
    "WMS W01 CRITICAL CARE": {"occupied": 6, "total": 9},
    "NHNN C0 NCCU": {"occupied": 0, "total": 4},
    "NHNN C1 NCCU": {"occupied": 0, "total": 3},
}

EMERGENCY_AVG = 3
DISCHARGE_PROB = 0.1

ELECTIVE_TOTAL = 20
ELECTIVE_PROB = 0.1
N_TRIALS = 10000
EXTRA_BEDS = 5


class Abacus:
    def __init__(self, dept: str):
        self.dept = dept

        self.bed_numbers = BED_NUMBERS.get(dept)
        self.total_beds = self.bed_numbers["total"]  # type: ignore
        self.occupied_beds = self.bed_numbers["occupied"]  # type:ignore

        self.electives_data = self._get_electives_data()
        self.emergencies_data = self._get_emergencies_data()
        self.discharges_data = self._get_discharges_data()
        self.current_data = self._get_current_beds()

        self.electives_graph = self._generate_graph("electives", self.electives_data, 0)
        self.emergencies_graph = self._generate_graph(
            "emergencies", self.emergencies_data, 0
        )
        self.discharges_graph = self._generate_graph(
            "discharges", self.discharges_data, 0
        )
        self.current_graph = self._generate_graph("current_beds", self.current_data, 0)
        self.overall_pmf = self._combine_probabilities()
        self.overall_graph = self._generate_graph(
            "overall", self.overall_pmf, self.occupied_beds
        )

    def _simulate(self, num_simulations: int) -> np.array:
        sim = np.zeros(num_simulations)
        self.total_admissions = np.convolve(self.electives_data, self.emergencies_data)

        for i in range(num_simulations):
            state = self.occupied_beds  # start with current state
            adm = np.random.choice(
                len(self.total_admissions), p=self.total_admissions
            )  # pick a number of admissions
            dc = np.random.choice(
                len(self.discharges_data), p=np.negative(self.discharges_data)
            )  # pick a number of discharges
            state = state + adm - dc  # update state
            state = max(0, state)  # don't go below 0
            sim[i] = state  # store state
        return sim

    def _combine_probabilities(self) -> np.array:
        ##
        # overall_pmf = np.convolve(
        #     np.convolve(
        #         np.convolve(self.electives_data, self.emergencies_data),
        #         self.discharges_data,
        #     ),
        #     self.current_data,
        # )
        ##

        ##
        #  HJV: Just lots of convolves leads to probs being too high
        # which makes sense because it's saying
        # "tomorrow we will definitely have all the beds as today"
        # not sure the negative convoles works with discharges either...
        # I think this is wrong because of the negative convoles...
        # So, we could run it as a monte carlo?
        # So essentially we would
        #  * first convolve the electives and emergencies, and this is the
        # probability distribution for the admissions
        #  * then add to current beds and subtract discharges
        # to lead to a predicted tomorrow number
        # we do this a bunch of times and then we have a distribution of
        # tomorrow's number of beds
        ##

        sim = self._simulate(N_TRIALS)
        overall_pmf = np.histogram(
            sim, bins=np.arange(0, self.total_beds + 1), density=True
        )[0]
        overall_cmf = np.cumsum(overall_pmf[::-1])
        overall_cmf = overall_cmf / overall_cmf[-1]
        return overall_cmf[::-1]

    def _get_electives_data(self) -> np.array:
        return np.histogram(
            np.random.binomial(ELECTIVE_TOTAL, ELECTIVE_PROB, N_TRIALS),
            bins=np.arange(0, self.total_beds + 1),
            density=True,
        )[0]

    def _get_emergencies_data(self) -> np.array:
        return np.histogram(
            np.random.poisson(EMERGENCY_AVG, N_TRIALS),
            bins=np.arange(0, self.total_beds + 1),
            density=True,
        )[0]

    def _get_discharges_data(self) -> np.array:
        return np.negative(
            np.histogram(
                np.random.binomial(self.occupied_beds, DISCHARGE_PROB, N_TRIALS),
                bins=np.arange(0, self.total_beds + 1),
                density=True,
            )[0]
        )

    def _get_current_beds(self) -> np.array:
        return np.where(np.arange(self.total_beds) == self.occupied_beds, 1, 0)

    def _generate_graph(self, tap: str, data: np.array, slider_value: int) -> dict:
        shapes = []
        if slider_value is not None:
            shapes.append(
                {
                    "type": "line",
                    "xref": "x",
                    "yref": "paper",
                    "x0": slider_value - 0.5,
                    "y0": 0,
                    "x1": slider_value - 0.5,
                    "y1": 1,
                    "line": {"color": "Black", "width": 5},
                }
            )
        return {
            "data": [
                {
                    "x": np.arange(0, (self.total_beds)),  # + EXTRA_BEDS)),
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
                # "title": tap.capitalize(),
                "xaxis": {"title": "Beds"},
                "yaxis": {"title": "Probability", "side": "right"},
                "bargap": 0,
                "bargroupgap": 0,
                "shapes": shapes,
                "autosize": True,
                "margin": {"l": 0, "r": 0, "t": 10, "b": 0},
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
        Input(f"{tap}_adjustor", "value"),
    )
    def _show_graph(dept: str, adj_value: int):  # type: ignore
        abacus_instance = Abacus(dept)
        tap_data = getattr(abacus_instance, f"{tap}_data")
        return abacus_instance._generate_graph(tap, tap_data, adj_value)

    @callback(
        Output(f"{tap}_adjustor", "value"),
        Output(f"{tap}_adjustor", "max"),
        Input(ids.DEPT_SELECTOR, "value"),
    )
    def _set_adjustor(dept: str) -> tuple:
        abacus_instance = Abacus(dept)
        max_prob_index = np.argmax(np.abs(getattr(abacus_instance, f"{tap}_data")))
        return (
            max_prob_index,
            abacus_instance.total_beds,
        )

    return _modal, _show_graph, _set_adjustor


for tap in ["electives", "emergencies", "discharges"]:
    modal_callback, show_graph_callback, adjustor_callback = create_callback(tap)


@callback(
    Output("mane_progress_bar", "sections"),
    Output("mane_progress_bar", "max"),
    Output(ids.PROGRESS_WARD, "max"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input("electives_adjustor", "value"),
    Input("emergencies_adjustor", "value"),
    Input("discharges_adjustor", "value"),
)
def mane_progress_bar(
    dept: str,
    electives: int,
    emergencies: int,
    discharges: int,
) -> tuple:
    abacus_instance = Abacus(dept)

    n_beds = abacus_instance.occupied_beds
    expected_beds = n_beds - discharges
    total_beds = abacus_instance.total_beds

    admitted_element = {
        "value": (expected_beds / total_beds) * 100,
        "color": "blue",
        "label": f"{expected_beds} staying in",
    }
    elective_element = {
        "value": (electives / total_beds) * 100,
        "color": "green",
        "label": f"{electives} Electives",
    }
    emergency_element = {
        "value": (emergencies / total_beds) * 100,
        "color": "red",
        "label": f"{emergencies} Emergencies",
    }

    return (
        [admitted_element, elective_element, emergency_element],
        total_beds,
        total_beds,
    )
