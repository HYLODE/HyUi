from dash import Input, Output, State, callback
from web.pages.sitrep import ids


taps = ["electives", "emergencies", "discharges"]

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
    Output("mane_progress_bar", "sections"),
    Input(ids.DEPT_SELECTOR, "value"),
    # Input(ids.BEDS_STORE, "data"),
    Input("electives_adjustor", "value"),
    Input("electives_adjustor", "value"),
    Input("emergencies_adjustor", "value"),
    Input("discharges_adjustor", "value"),
)
def mane_progress_bar(
    dept: str,
    beds: list[dict],
    electives: int = 5,
    emergencies: int = 3,
    discharges: int = 4,
) -> list[dict]:
    if beds:
        n_beds = len([bed for bed in beds if bed.get("department") == dept])
    else:
        n_beds = 20
    norm = 30

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
