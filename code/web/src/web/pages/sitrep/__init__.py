from dash.dash_table import FormatTemplate


SITREP_ENV = "test"  # test (staging red) or prod
# GREEN = TCN model
# RED = original model

STAGING_COLOUR = "RED"  # or RED or BLUE

if STAGING_COLOUR == "GREEN":
    HYCASTLE_API_PORT = "5906"
    HYMIND_API_PORT = "5907"
elif STAGING_COLOUR == "RED":
    HYCASTLE_API_PORT = "5207"
    HYMIND_API_PORT = "5208"
# elif STAGING_COLOUR == "BLUE":
#     HYCASTLE_API_PORT =
#     HYMIND_API_PORT =
else:
    raise ValueError("STAGING not defined")

BPID = "sit_"

BED_BONES_TABLE_ID = 261
CACHE_TIMEOUT = 5 * 60  # seconds!!!
REFRESH_INTERVAL = 30 * 60 * 1000  # milliseconds
DEPT2WARD_MAPPING = {
    "UCH T03 INTENSIVE CARE": "T03",
    "UCH T06 SOUTH PACU": "T06",
    "GWB L01 CRITICAL CARE": "GWB",
    "WMS W01 CRITICAL CARE": "WMS",
    "NHNN C0 NCCU": "NCCU0",
    "NHNN C1 NCCU": "NCCU1",
}

COLS = [
    # {"id": "unit_order", "name": "", "type": "numeric"},
    # {"id": "ward_code", "name": "Ward"},
    # {"id": "bay_code", "name": "Bay"},
    # {"id": "bed_code", "name": "Bed code"},
    # {"id": "room", "name": ""},
    # {"id": "bed", "name": "Bed"},
    # ROOM STATUS
    # {"id": "open", "name": "", "presentation": "markdown"},
    {"id": "bed_icons", "name": "", "presentation": "markdown"},
    {"id": "bed_label", "name": "Bed", "type": "text"},
    {"id": "room_label", "name": ""},
    # {"id": "closed", "name": "Closed"},
    # {"id": "sideroom", "name": ""},
    # {"id": "admission_dt", "name": "Admission"},
    # {"id": "elapsed_los_td", "name": "LoS"},
    # DEMOGRAPHICS
    {"id": "age_sex", "name": ""},
    {"id": "name", "name": "Full Name"},
    {"id": "mrn", "name": "MRN", "type": "text"},
    # {"id": "admission_age_years", "name": "Age"},
    # {"id": "sex", "name": "Sex"},
    # {"id": "dob", "name": "DoB"},
    # {"id": "bed_empty", "name": "Empty"},
    # {"id": "team", "name": "Side"},
    # PHYSIOLOGY
    # {"id": "vent_type_1_4h", "name": "Ventilation"},
    # {"id": "n_inotropes_1_4h", "name": "Cardiovascular"},
    # {"id": "had_rrt_1_4h", "name": "Renal"},
    {"id": "organ_icons", "name": "Organ Support", "presentation": "markdown"},
    {"id": "wim_1", "name": "WIM", "type": "numeric"},
    # DISCHARGE
    # {"id": "episode_slice_id", "name": "Slice", "type": "numeric"},
    {
        "id": "prediction_as_real",
        "name": "Exit?",
        "type": "numeric",
        "format": FormatTemplate.percentage(0),
    },
    {
        "id": "DischargeReady",
        "name": "Discharge decision",
        "presentation": "dropdown",
        "editable": True,
    },
    {"id": "pm_type", "name": "Epic bed request", "type": "text"},
    # {"id": "epic_bed_request", "name": "Epic bed request", "type": "text"},
    {"id": "pm_dept", "name": "Bed assigned", "type": "text"},
    # {"id": "covid", "name": "COVID", "presentation": "markdown"},
]

STYLE_CELL_CONDITIONAL = [
    {
        "if": {"column_id": "bed_label"},
        "textAlign": "right",
        "fontWeight": "bold",
        # "fontSize": 14,
    },
    {
        "if": {"column_id": "room_label"},
        "textAlign": "left",
        "width": "60px",
        "minWidth": "60px",
        "maxWidth": "60px",
        "whitespace": "normal",
    },
    {"if": {"column_id": "open"}, "textAlign": "left", "width": "20px"},
    {
        "if": {"column_id": "mrn"},
        "textAlign": "left",
        "font-family": "monospace",
    },
    {
        "if": {"column_id": "name"},
        "textAlign": "left",
        "font-family": "sans-serif",
        "fontWeight": "bold",
        "width": "100px",
    },
    {
        "if": {"column_id": "age_sex"},
        "textAlign": "right",
    },
    {"if": {"column_id": "organ_icons"}, "textAlign": "left"},
    {"if": {"column_id": "name"}, "fontWeight": "bold"},
    {"if": {"column_id": "DischargeReady"}, "textAlign": "left"},
]

BEDS_KEEP_COLS = [
    "id",  # needed for merge on discharge status
    "location_id",
    "location_string",
    "department",
    "room",
    "bed",
    "unit_order",
    "closed",
    "covid",
    "bed_functional",
    "bed_physical",
    "DischargeReady",
]

CENSUS_KEEP_COLS = [
    "location_string",
    "location_id",
    "ovl_admission",
    "ovl_hv_id",
    "cvl_discharge",
    "occupied",
    "ovl_ghost",
    "mrn",
    "encounter",
    "date_of_birth",
    "lastname",
    "firstname",
    "sex",
    "planned_move",
    "pm_datetime",
    "pm_type",
    "pm_dept",
    "pm_location_string",
]

SITREP_KEEP_COLS = [
    "episode_slice_id",
    "csn",
    # "department",
    "bay_code",
    "bed_code",
    "discharge_ready_1_4h",
    "n_inotropes_1_4h",
    "had_rrt_1_4h",
    "vent_type_1_4h",
    "wim_1",
]

HYMIND_ICU_DISCHARGE_COLS = [
    # "prediction_id",
    "episode_slice_id",
    # "model_name",
    # "model_version",
    "prediction_as_real",
    # "predict_dt",
]

PROBABILITY_COLOUR_SCALE = [
    {
        "if": {
            "column_id": "prediction_as_real",
            "filter_query": (
                f"{{prediction_as_real}} >= {c / 10} "
                f"&& {{prediction_as_real}} < {c / 10 + 0.1}"
            ),
        },
        "backgroundColor": f"rgba(46, 204, 64, {c / 10})",
    }
    for c in range(0, 11)
]
