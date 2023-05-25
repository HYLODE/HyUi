from pathlib import Path
from web.config import get_settings
from web import ids as web_ids
from web.pages.ed import ids as ed_ids

FONTS_GOOGLE = "https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;900&display=swap"
FONTS_FA = "https://use.fontawesome.com/releases/v5.8.1/css/all.css"
with Path(__file__).parent / "index.html" as f:
    INDEX_STRING = f.open().read()

# URLS to prepopulate redis cache
# Pass either strings or functions
API_URLS = {
    "campus_url": "http://api:8000/baserow/campus?campuses=uclh",
    web_ids.DEPT_STORE: f"{get_settings().api_url}/baserow/departments/",
    web_ids.ROOM_STORE: f"{get_settings().api_url}/baserow/rooms/",
    web_ids.BEDS_STORE: f"{get_settings().api_url}/baserow/beds/",
    web_ids.ELECTIVES_STORE: f"{get_settings().api_url}/electives/",
    ed_ids.PATIENTS_STORE: f"{get_settings().api_url}/ed/individual/",
    ed_ids.AGGREGATE_STORE: f"{get_settings().api_url}/ed/aggregate/",
}


SITREP_DEPT2WARD_MAPPING: dict = {
    "UCH T03 INTENSIVE CARE": "T03",
    "UCH T06 SOUTH PACU": "T06",
    "GWB L01 CRITICAL CARE": "GWB",
    "WMS W01 CRITICAL CARE": "WMS",
    "NHNN C0 NCCU": "NHNNC0",
    "NHNN C1 NCCU": "NHNNC1",
}
