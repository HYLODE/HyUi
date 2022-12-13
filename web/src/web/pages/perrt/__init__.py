BPID = "PERRT_"

REFRESH_INTERVAL = 10 * 60 * 1000  # milliseconds

BED_BONES_TABLE_ID = 261

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
    # "DischargeReady",
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
    "hv_admission_dt",
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

CPR_COLS = {
    "status_change_datetime": "CPR status timestamp",
    "name": "CPR status",
    "encounter": "CSN",
}

PERRT_CONSULTS_COLS = {
    # 'consultation_request_id',
    "status_change_datetime": "Consult status timestamp",
    "name": "Consult",
    "encounter": "CSN",
}

PERRT_VITALS_WIDE = {
    "encounter": "CSN",
    "news_scale_1_max": "NEWS1MAX",
    "news_scale_2_max": "NEWS2MAX",
}
