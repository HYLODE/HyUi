from config.settings import settings


BPID = "CENSUS_"
CENSUS_API_URL = f"{settings.API_URL}/census/beds"
CLOSED_BEDS_API_URL = f"{settings.API_URL}/census/beds/closed"
BED_LIST_API_URL = f"{settings.API_URL}/census/beds/list"
DEPARTMENTS_API_URL = f"{settings.API_URL}/census/departments"

MINUTES = 60 * 1000  # milliseconds
REFRESH_INTERVAL = 15 * MINUTES

CACHE_TIMEOUT = 5 * 60  # seconds!!!

BED_BONES_TABLE_ID = 261


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

CENSUS_COLS = [
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
    # {"id": "organ_icons", "name": "Organ Support", "presentation": "markdown"},
    # {"id": "wim_1", "name": "WIM", "type": "numeric"},
    # DISCHARGE
    # {"id": "episode_slice_id", "name": "Slice", "type": "numeric"},
    # {
    #     "id": "prediction_as_real",
    #     "name": "Dischargeable",
    #     "type": "numeric",
    #     "format": FormatTemplate.percentage(0),
    # },
    # {
    #     "id": "DischargeReady",
    #     "name": "Discharge decision",
    #     "presentation": "dropdown",
    #     "editable": True,
    # },
    # {"id": "pm_type", "name": "Epic bed request", "type": "text"},
    # {"id": "epic_bed_request", "name": "Epic bed request", "type": "text"},
    # {"id": "pm_dept", "name": "Bed assigned", "type": "text"},
    # {"id": "covid", "name": "COVID", "presentation": "markdown"},
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

DEPT_KEEP_COLS = [
    "department",
    "beds",
    "patients",
    "empties",
    "days_since_last_dc",
    "closed_temp",
    "closed_perm",
    "modified_at",
    "closed",  # only exists after merging with bed_bones
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
    "closed",  # only exists after merging with bed_bones
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
