from dash import Input, Output, callback

from web.pages.sitrep import ids
import math
from web import TEST_ABACUS_PROBABILITIES, TEST_CAPACITY_DICT


@callback(Output(ids.ABACUS, "elements"), Input(ids.DEPT_SELECTOR, "value"))
def _make_abacus(dept: str) -> list[dict]:
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
    probs = TEST_ABACUS_PROBABILITIES  # sorry temporary
    num_beds = TEST_CAPACITY_DICT  # sorry temporary

    SPACING = 40
    ROW_HEIGHT = 60

    i = 0
    # elements = [
    #     {"data": {"id": "out"}},
    # ]
    elements = []
    for date, beds in dict(sorted(probs.items())).items():
        capacity_node = {"data": {"id": date}, "grabbable": False, "selectable": False}
        elements.append(capacity_node)
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
                    "parent": date if j <= num_beds[date] else "out",
                },
                "position": {"x": x, "y": y},
                "classes": f"abacus bed{j} {'in' if j <= num_beds[date] else 'out'}",
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
        i += 1
    return elements
