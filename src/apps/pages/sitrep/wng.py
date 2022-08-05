# src/apps/pages/sitrep/wng.py
# wrangling and other functions for the sitrep page
# just so the logic in the main page is clearer
from config.settings import settings

# NB: the order of this list determines the order of the table
COLS = [
    {"id": "unit_order", "name": "", "type": "numeric"},
    # {"id": "closed", "name": "Closed"},
    {"id": "sideroom", "name": ""},
    # {"id": "sideroom_suffix", "name": ""},
    # {"id": "ward_code", "name": "Ward"},
    # {"id": "bay_code", "name": "Bay"},
    # {"id": "room", "name": "Bay"},
    # {"id": "bed_code", "name": "Bed code"},
    # {"id": "bed", "name": "Bed"},
    # {"id": "admission_dt", "name": "Admission"},
    # {"id": "elapsed_los_td", "name": "LoS"},
    {"id": "mrn", "name": "MRN", "type": "text"},
    {"id": "name", "name": "Full Name"},
    # {"id": "admission_age_years", "name": "Age"},
    # {"id": "sex", "name": "Sex"},
    {"id": "age_sex", "name": "Age Sex"},
    # {"id": "dob", "name": "DoB"},
    {"id": "wim_1", "name": "WIM"},
    # {"id": "bed_empty", "name": "Empty"},
    # {"id": "team", "name": "Side"},
    # {"id": "vent_type_1_4h", "name": "Ventilation"},
    # {"id": "n_inotropes_1_4h", "name": "Cardiovascular"},
    # {"id": "had_rrt_1_4h", "name": "Renal"},
    {"id": "organ_icons", "name": "Organ Support", "presentation": "markdown"},
    {
        "id": "DischargeReady",
        "name": "D/C",
        "presentation": "dropdown",
        "editable": True,
    },
    {"id": "open", "name": "", "presentation": "markdown"},
    # {"id": "covid", "name": "COVID"},
]

beds_keep_cols = [
    "id",  # needed for merge on discharge status
    "location_id",
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

census_keep_cols = [
    "location_id",
    "ovl_admission",
    "ovl_hv_id",
    "cvl_discharge",
    "occupied",
    "mrn",
    "encounter",
    "date_of_birth",
    "lastname",
    "firstname",
]

sitrep_keep_cols = [
    "department",
    "bay_code",
    "bed_code",
    "discharge_ready_1_4h",
    "n_inotropes_1_4h",
    "had_rrt_1_4h",
    "vent_type_1_4h",
    "wim_1",
    "sex",
]

def build_sitrep_url(ward: str = None) -> str:
    """Construct API based on environment and requested ward"""
    if settings.ENV == "prod":
        ward = ward.upper() if ward else "TO3"
        API_URL = f"{settings.BASE_URL}:5006/live/icu/{ward}/ui"
    else:
        API_URL = f"{settings.API_URL}/sitrep/"
    return API_URL
