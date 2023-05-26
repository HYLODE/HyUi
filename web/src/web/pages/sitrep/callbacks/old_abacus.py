# from dash import Input, Output, callback

# from web.pages.sitrep import ids, CAMPUSES
# from web.stores import ids as store_ids

# # import math
# import random


# @callback(
#     Output(ids.ABACUS_CHART, "elements"),
#     Input(ids.CAMPUS_SELECTOR, "value"),
#     Input(store_ids.ABACUS_STORE, "data"),
# )
# def _make_abacus(dept: str, abacus_store: list[dict]) -> list[dict]:
#     campus_dict = {i.get("value"): i.get("label") for i in CAMPUSES}

#     dept_abacus = [
#         row for row in abacus_store if campus_dict.get(dept, "") in row["campus"]
#     ]

#     SPACING = 40
#     ROW_HEIGHT = 60
#     NUM_BEDS_RANGE = (15, 20)

#     elements = []
#     for i, individual_day_dict in enumerate(dept_abacus):
#         date = individual_day_dict["date"]
#         beds = individual_day_dict["probabilities"]

#         capacity_node = {
#             "data": {"id": date},
#             "grabbable": False,
#             "selectable": False,
#         }
#         elements.append(capacity_node)
#         num_beds = random.randint(NUM_BEDS_RANGE[0], NUM_BEDS_RANGE[1])

#         for j, bed in enumerate(beds):
#             x = j * SPACING
#             y = i * ROW_HEIGHT
#             node_id = f"{date}-{i}-{j}"
#             node = {
#                 "data": {
#                     "id": node_id,
#                     "label": date,
#                     "prob": round(bed, 1),
#                     # "sqrt_prob": math.sqrt(bed),
#                     "parent": date if j <= num_beds else "out",
#                 },
#                 "position": {"x": x, "y": y},
#                 "classes": f"abacus bed{j} {'in' if j <= num_beds else 'out'}",
#                 "grabbable": False,
#                 "selectable": True,
#             }
#             elements.append(node)
#         edge = {
#             "data": {
#                 "source": f"{date}-{i}-{0}",
#                 "target": f"{date}-{i}-{j}",
#             },
#             "grabbable": False,
#             "selectable": False,
#         }
#         elements.append(edge)

#     return elements
