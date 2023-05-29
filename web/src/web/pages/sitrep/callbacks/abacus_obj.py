import numpy as np
from dash import Input, Output, State, callback
from web.pages.sitrep import ids
from web.stores import ids as store_ids
from datetime import datetime
from web import CAMPUSES


from web.pages.sitrep.callbacks.abacus_funcs import (
    Abacus,
    BED_NUMBERS,
    COLOUR,
)

abaci = {}
for dept in BED_NUMBERS.keys():
    abaci[dept] = Abacus(dept)


@callback(
    Output("overall_graph", "figure"),
    Input(ids.DEPT_SELECTOR, "value"),
)
def overall_graph(
    dept: str,
) -> dict:
    return abaci[dept].overall_graph


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
        abacus_instance = abaci[dept]
        tap_data = getattr(abacus_instance, f"{tap}_pmf")
        return abacus_instance.generate_graph(tap, tap_data, adj_value)

    _set_adjustor = None

    if tap != "electives":

        @callback(
            Output(f"{tap}_adjustor", "value"),
            Output(f"{tap}_adjustor", "max"),
            Input(ids.DEPT_SELECTOR, "value"),
        )
        def _set_adjustor(dept: str) -> tuple:
            abacus_instance = abaci[dept]
            max_prob_index = np.argmax(np.abs(getattr(abacus_instance, f"{tap}_pmf")))
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
    abacus_instance = abaci[dept]

    n_beds = abacus_instance.occupied_beds
    expected_beds = n_beds - discharges
    total_beds = abacus_instance.total_beds

    admitted_element = {
        "value": (expected_beds / total_beds) * 100,
        "color": f"{COLOUR['overall']} 1)",
        "label": f"{expected_beds} staying in",
    }
    elective_element = {
        "value": (electives / total_beds) * 100,
        "color": f"{COLOUR['electives']} 1)",
        "label": f"{electives} Electives",
    }
    emergency_element = {
        "value": (emergencies / total_beds) * 100,
        "color": f"{COLOUR['emergencies']} 1)",
        "label": f"{emergencies} Emergencies",
    }

    return (
        [admitted_element, elective_element, emergency_element],
        total_beds,
        total_beds,
    )


@callback(
    Output("electives_list", "data"),
    Output("electives_adjustor", "value"),
    Output("electives_adjustor", "max"),
    Output("electives_title", "children"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input(store_ids.ELECTIVES_STORE, "data"),
)
def _store_electives(
    campus: str,
    electives: list[dict],
) -> tuple[list[dict], int, int, str]:
    date = datetime.today().strftime("%Y-%m-%d")

    campus_dict = {i.get("default_dept"): i.get("label") for i in CAMPUSES}
    icu_cut_off = [0, 0.60]

    electives = [
        row
        for row in electives
        if campus_dict.get(campus, "") in row["department_name"]
    ]

    electives = [row for row in electives if row["surgery_date"] == date]

    i = 0
    pacu_booked_count = 0
    for row in electives:
        row["id"] = i
        i += 1

        # add front-end columns

        row["full_name"] = "{first_name} {last_name}".format(**row)
        row["age_sex"] = "{age_in_years}{sex[0]}".format(**row)

        if row["pacu"] and row["icu_prob"] > icu_cut_off[0]:
            row["pacu_yn"] = "✅ BOOKED"
            pacu_booked_count += 1
        elif row["pacu"] and row["icu_prob"] <= icu_cut_off[0]:
            row["pacu_yn"] = "✅🤷BOOKED"
            pacu_booked_count += 1
        elif not row["pacu"] and row["icu_prob"] > icu_cut_off[1]:
            row["pacu_yn"] = "⚠️ No - consider?"
        else:
            row["pacu_yn"] = "🏥 No"

    adjustor_max = len(abaci[campus].electives_pmf)
    adjustor_value = pacu_booked_count
    return (
        electives,
        adjustor_value,
        adjustor_max,
        f"Electives ({pacu_booked_count} PACU bed(s) booked)",
    )
