BPID = "ELE_"


STYLE_CELL_CONDITIONAL = [
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
    {"if": {"column_id": "name"}, "fontWeight": "bold"},
    {"if": {"column_id": "pacu"}, "fontWeight": "bold"},
]

SPECIALTY_SHORTNAMES = {
    "Upper Gastro-Intestinal Surgery": "Upper GI",
    "Bronchoscopy/Thoracoscopy": "Bronchoscopy",
}
