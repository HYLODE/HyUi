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

SITREP_DEPT2WARD_MAPPING: dict = {
    "UCH T03 INTENSIVE CARE": "T03",
    "UCH T06 SOUTH PACU": "T06",
    "GWB L01 CRITICAL CARE": "GWB",
    "WMS W01 CRITICAL CARE": "WMS",
    "NHNN C0 NCCU": "NHNNC0",
    "NHNN C1 NCCU": "NHNNC1",
}

DISCHARGE_DECISIONS = [
    dict(label="HOLD", value="blocked", description="Not for discharge"),
    dict(
        label="REVIEW",
        value="review",
        description="Review for possible " "discharge later",
    ),
    dict(
        label="DISCHARGE",
        value="discharge",
        description="Ready for " "discharge " "now",
    ),
    dict(
        label="EXCELLENCE",
        value="excellence",
        description="Excellence in " "the " "End of Life " "pathway",
    ),
    dict(
        label="BLOCKED",
        value="blocked",
        description="Block the bed (not " "available for " "admissions)",
    ),
]
