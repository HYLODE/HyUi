BPID = "CENSUS_"

MINUTES = 60 * 1000  # milliseconds
REFRESH_INTERVAL = 15 * MINUTES

CACHE_TIMEOUT = 5 * 60  # seconds!!!


DEPT_COLS = [
    {"id": "department", "name": "department"},
    {"id": "beds", "name": "beds"},
    {"id": "closed", "name": "closed"},
    {"id": "patients", "name": "patients"},
    {"id": "empties", "name": "empties"},
    {"id": "days_since_last_dc", "name": "Days since d/c"},
    {"id": "closed_temp", "name": "closed_temp"},
    {"id": "closed_perm", "name": "closed_perm"},
    {"id": "modified_at", "name": "modified_at"},
]

CENSUS_STYLE_CELL_CONDITIONAL = [
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
    # {"if": {"column_id": "organ_icons"}, "textAlign": "left"},
    {"if": {"column_id": "name"}, "fontWeight": "bold"},
    # {"if": {"column_id": "DischargeReady"}, "textAlign": "left"},
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
    "closed",  # only exists after merging with beds
]
