# src/apps/pages/sitrep/__init__.py
# set the sitrep level of maturity/development here as this is a sub-app
# rather than in the main app settings
SITREP_ENV="test"  # test (staging red) or prod 

BPID = "sit_"

BED_BONES_TABLE_ID = 261
REFRESH_INTERVAL = 30 * 60 * 1000  # milliseconds
DEPT2WARD_MAPPING = {
    "UCH T03 INTENSIVE CARE": "T03",
    "UCH T06 SOUTH PACU": "T06",
    "GWB L01 CRITICAL CARE": "GWB",
    "WMS W01 CRITICAL CARE": "WMS",
}

COLS = [
    # {"id": "unit_order", "name": "", "type": "numeric"},
    # {"id": "ward_code", "name": "Ward"},
    # {"id": "bay_code", "name": "Bay"},
    # {"id": "bed_code", "name": "Bed code"},
    # {"id": "room", "name": ""},
    # {"id": "bed", "name": "Bed"},
    {"id": "open", "name": "", "presentation": "markdown"},
    {"id": "bed_label", "name": "Bed", "type": "text"},
    {"id": "room_label", "name": ""},
    # {"id": "closed", "name": "Closed"},
    # {"id": "sideroom", "name": ""},
    # {"id": "admission_dt", "name": "Admission"},
    # {"id": "elapsed_los_td", "name": "LoS"},
    {"id": "age_sex", "name": ""},
    {"id": "name", "name": "Full Name"},
    {"id": "mrn", "name": "MRN", "type": "text"},
    # {"id": "admission_age_years", "name": "Age"},
    # {"id": "sex", "name": "Sex"},
    # {"id": "dob", "name": "DoB"},
    # {"id": "bed_empty", "name": "Empty"},
    # {"id": "team", "name": "Side"},
    # {"id": "vent_type_1_4h", "name": "Ventilation"},
    # {"id": "n_inotropes_1_4h", "name": "Cardiovascular"},
    # {"id": "had_rrt_1_4h", "name": "Renal"},
    {"id": "organ_icons", "name": "Organ Support", "presentation": "markdown"},
    {"id": "wim_1", "name": "WIM", "type": "numeric"},
    {
        "id": "DischargeReady",
        "name": "D/C",
        "presentation": "dropdown",
        "editable": True,
    },
    # {"id": "covid", "name": "COVID"},
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
]

SITREP_KEEP_COLS = [
    "department",
    "bay_code",
    "bed_code",
    "discharge_ready_1_4h",
    "n_inotropes_1_4h",
    "had_rrt_1_4h",
    "vent_type_1_4h",
    "wim_1",
]


