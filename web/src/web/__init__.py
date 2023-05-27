SITREP_DEPT2WARD_MAPPING: dict = {
    "UCH T03 INTENSIVE CARE": "T03",
    "UCH T06 SOUTH PACU": "T06",
    "GWB L01 CRITICAL CARE": "GWB",
    "WMS W01 CRITICAL CARE": "WMS",
    "NHNN C0 NCCU": "NHNNC0",
    "NHNN C1 NCCU": "NHNNC1",
}

CAMPUSES = [
    {
        "value": "UNIVERSITY COLLEGE HOSPITAL CAMPUS",
        "label": "UCH",
        "default_dept": "UCH T03 INTENSIVE CARE",
    },
    {
        "value": "GRAFTON WAY BUILDING",
        "label": "GWB",
        "default_dept": "GWB L01 CRITICAL CARE",
    },
    {
        "value": "WESTMORELAND STREET",
        "label": "WMS",
        "default_dept": "WMS W01 CRITICAL CARE",
    },
    {"value": "QUEEN SQUARE CAMPUS", "label": "NHNN", "default_dept": "NHNN C1 NCCU"},
]
