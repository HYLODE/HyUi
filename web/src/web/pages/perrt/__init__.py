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
    "NHNN C0 NCCU": "NCCU0",
    "NHNN C1 NCCU": "NCCU1",
}

NEWS_SCORE_COLORS = {
    "1": "rgb(189, 230, 175)",
    "2": "rgb(189, 230, 175)",
    "3": "rgb(189, 230, 175)",
    "4": "rgb(189, 230, 175)",
    "5": "rgb(247, 215, 172)",
    "6": "rgb(247, 215, 172)",
    "7": "rgb(240, 158, 158)",
    "8": "rgb(240, 158, 158)",
    "9": "rgb(240, 158, 158)",
    "10": "rgb(240, 158, 158)",
    "11": "rgb(240, 158, 158)",
    "12": "rgb(240, 158, 158)",
    "13": "rgb(240, 158, 158)",
    "14": "rgb(240, 158, 158)",
    "15": "rgb(240, 158, 158)",
    "16": "rgb(240, 158, 158)",
    "17": "rgb(240, 158, 158)",
    "18": "rgb(240, 158, 158)",
    "19": "rgb(240, 158, 158)",
    "20": "rgb(240, 158, 158)",
    "21": "rgb(240, 158, 158)",
    "22": "rgb(240, 158, 158)",
    "23": "rgb(240, 158, 158)",
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
