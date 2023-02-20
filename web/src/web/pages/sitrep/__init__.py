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
