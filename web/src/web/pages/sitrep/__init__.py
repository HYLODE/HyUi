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

DISCHARGE_DECISIONS = [
    dict(label="READY", value="ready", description="Ready now"),
    dict(label="REVIEW", value="review", description="Ready soon"),
    dict(label="NOT READY", value="not ready", description="Not ready"),
]
