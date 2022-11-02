BPID = "ELE_"

# Caboodle data so refresh only needs to happen first thing
REFRESH_INTERVAL = 6 * 60 * 60 * 1000  # milliseconds

COLS = [
    {"id": "SurgeryDate", "name": "Date"},
    {"id": "pacu", "name": "pacu"},
    {"id": "SurgicalService", "name": "Specialty"},
    {"id": "RoomName", "name": "Theatre"},
    {"id": "age_sex", "name": ""},
    {"id": "name", "name": "Full Name"},
    {"id": "PrimaryMrn", "name": "MRN"},
    # {"id": "Priority", "name": "Priority"},
    # {"id": "Status", "name": "Status"},
    {"id": "PatientFriendlyName", "name": "Procedure"},
    {"id": "most_recent_ASA", "name": "ASA"},
    {"id": "most_recent_METs", "name": "METS"},
    # {"id": "FirstName", "name": "FirstName"},
    # {"id": "LastName", "name": "LastName"},
    # {"id": "Sex", "name": "Sex"},
    # {"id": "AgeInYears", "name": "Age"},
    # {"id": "PrimaryAnesthesiaType", "name": "PrimaryAnesthesiaType"},
    # {"id": "pod_orc", "name": "Post-op booking"},
    # {"id": "pod_preassessment", "name": "Post-op pre-assess"},
    # {"id": "PlacedOnWaitingListDate", "name": "PlacedOnWaitingListDate"},
    # {"id": "DecidedToAdmitDate", "name": "DecidedToAdmitDate"},
    # {"id": "AdmissionService", "name": "AdmissionService"},
    # {"id": "PrimaryService", "name": "PrimaryService"},
    # {"id": "Type", "name": "Type"},
    # {"id": "Classification", "name": "Classification"},
    # {"id": "SurgeryPatientClass", "name": "SurgeryPatientClass"},
    # {"id": "AdmissionPatientClass", "name": "AdmissionPatientClass"},
    # {"id": "ReasonNotPerformed", "name": "ReasonNotPerformed"},
    # {"id": "Canceled", "name": "Canceled"},
    # {"id": "CaseScheduleStatus", "name": "CaseScheduleStatus"},
    # {"id": "CancelDate", "name": "CancelDate"},
    # {"id": "PlannedOperationStartInstant", "name": "PlannedOperationStartInstant"},
    # {"id": "DepartmentName", "name": "DepartmentName"},
]


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
