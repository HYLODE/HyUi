from dash import Input, Output, callback

from web.pages.sitrep import ids
from web.stores import ids as store_ids

import math
import random


@callback(
    Output(ids.ABACUS_CHART, "elements"),
    Input(ids.DEPT_SELECTOR, "value"),
    Input(store_ids.ABACUS_STORE, "data"),
)
def _make_abacus(dept: str, abacus_store: dict) -> list[dict]:
    """
    Make the Abacus
    Inputs
        - list[dict] where each [dict] a {date: list}
            eg. {
                    '2023-03-04' : [1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.8, ... ]
                    '2023-03-05' : [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, ... ]
                },
        - a dict of capacities per date (idea being this can be altered)
            eg. {
                    '2023-03-04' : 20,
                    '2023-03-05' : 18,
            }
    Outputs
        - cytoscape elements
            - set out like an abacus
            - opacity colour-coded probabilities
    """

    dept_abacus = abacus_store[dept]

    SPACING = 40
    ROW_HEIGHT = 60
    NUM_BEDS_RANGE = (15, 20)

    elements = []
    for i, individual_day_dict in enumerate(dept_abacus):
        date = individual_day_dict["date"]
        beds = individual_day_dict["probabilities"]

        capacity_node = {
            "data": {"id": date},
            "grabbable": False,
            "selectable": False,
        }
        elements.append(capacity_node)
        num_beds = random.randint(NUM_BEDS_RANGE[0], NUM_BEDS_RANGE[1])

        for j, bed in enumerate(beds):
            x = j * SPACING
            y = i * ROW_HEIGHT
            node_id = f"{date}-{i}-{j}"
            node = {
                "data": {
                    "id": node_id,
                    "label": date,
                    "prob": round(bed, 1),
                    "sqrt_prob": math.sqrt(bed),
                    "parent": date if j <= num_beds else "out",
                },
                "position": {"x": x, "y": y},
                "classes": f"abacus bed{j} {'in' if j <= num_beds else 'out'}",
                "grabbable": False,
                "selectable": True,
            }
            elements.append(node)
        edge = {
            "data": {
                "source": f"{date}-{i}-{0}",
                "target": f"{date}-{i}-{j}",
            },
            "grabbable": False,
            "selectable": False,
        }
        elements.append(edge)

    return elements