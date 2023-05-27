import requests
import numpy as np

# from web.stores import ids as store_ids
from web.convert import parse_to_data_frame
from web.config import get_settings

from models.electives import MergedData


EMERGENCY_AVG = 3
DISCHARGE_PROB = 0.1

ELECTIVE_TOTAL = 20
ELECTIVE_PROB = 0.1
N_TRIALS = 10000
EXTRA_BEDS = 5

BED_NUMBERS = {
    "UCH T03 INTENSIVE CARE": {"occupied": 18, "total": 30},
    "UCH T06 SOUTH PACU": {"occupied": 5, "total": 12},
    "GWB L01 CRITICAL CARE": {"occupied": 7, "total": 10},
    "WMS W01 CRITICAL CARE": {"occupied": 6, "total": 9},
    "NHNN C0 NCCU": {"occupied": 0, "total": 4},
    "NHNN C1 NCCU": {"occupied": 0, "total": 3},
}


def aggregate_probabilities(
    success_probs: np.array,
) -> np.array:
    number_trials = len(success_probs)
    omega = 2 * np.pi / (number_trials + 1)
    chi = np.empty(number_trials + 1, dtype=complex)
    chi[0] = 1
    half_number_trials = int(number_trials / 2 + number_trials % 2)

    exp_value = np.exp(omega * np.arange(1, half_number_trials + 1) * 1j)

    xy = 1 - success_probs + success_probs * exp_value[:, np.newaxis]

    argz_sum = np.arctan2(xy.imag, xy.real).sum(axis=1)

    exparg = np.log(np.abs(xy)).sum(axis=1)
    d_value = np.exp(exparg)
    chi[1 : half_number_trials + 1] = d_value * np.exp(argz_sum * 1j)

    # set second half of chis:
    chi[half_number_trials + 1 : number_trials + 1] = np.conjugate(
        chi[1 : number_trials - half_number_trials + 1][::-1]
    )

    chi /= number_trials + 1
    xi = np.fft.fft(chi)
    xi += np.finfo(type(xi[0])).eps
    return xi.real


class Abacus:
    def __init__(self, dept: str):
        self.dept = dept

        self.bed_numbers = BED_NUMBERS.get(dept)
        self.total_beds = self.bed_numbers["total"]  # type: ignore
        self.occupied_beds = self.bed_numbers["occupied"]  # type:ignore

        self.electives_pmf = self._get_electives_pmf()
        self.emergencies_pmf = self._get_emergencies_pmf()
        self.discharges_pmf = self._get_discharges_pmf()
        self.current_data = self._get_current_beds()

        self.overall_pmf = self._combine_probabilities()
        self.overall_graph = self.generate_graph(
            "overall", self.overall_pmf, self.occupied_beds
        )

    def _simulate(self, num_simulations: int) -> np.array:
        sim = np.zeros(num_simulations)
        self.total_admissions = np.convolve(self.electives_pmf, self.emergencies_pmf)

        for i in range(num_simulations):
            state = self.occupied_beds  # start with current state
            adm = np.random.choice(
                len(self.total_admissions), p=self.total_admissions
            )  # pick a number of admissions
            dc = np.random.choice(
                len(self.discharges_pmf), p=np.negative(self.discharges_pmf)
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
        #
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

    def _get_electives_pmf(self) -> np.array:
        elective_df = parse_to_data_frame(
            requests.get(url=f"{get_settings().api_url}/electives/").json(), MergedData
        )
        elective_df = elective_df[elective_df["department_name"] == self.dept]
        # elective_pmf = aggregate_probabilities(
        #     np.array(elective_df["icu_prob"].values
        #              ))
        # return elective_pmf
        return np.histogram(
            np.random.binomial(ELECTIVE_TOTAL, ELECTIVE_PROB, N_TRIALS),
            bins=np.arange(0, self.total_beds + 1),
            density=True,
        )[0]

    def _get_emergencies_pmf(self) -> np.array:
        return np.histogram(
            np.random.poisson(EMERGENCY_AVG, N_TRIALS),
            bins=np.arange(0, self.total_beds + 1),
            density=True,
        )[0]

    def _get_discharges_pmf(self) -> np.array:
        return np.negative(
            np.histogram(
                np.random.binomial(self.occupied_beds, DISCHARGE_PROB, N_TRIALS),
                bins=np.arange(0, self.total_beds + 1),
                density=True,
            )[0]
        )

    def _get_current_beds(self) -> np.array:
        return np.where(np.arange(self.total_beds) == self.occupied_beds, 1, 0)

    def generate_graph(self, tap: str, data: np.array, slider_value: int) -> dict:
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
