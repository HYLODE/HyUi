"""
Prepare
- department_defaults.json
to be loaded into baserow from an extract of data from Epic and EMAP
plus hand collated data
"""
# Runs from a Python console in this directory
import pandas as pd

df = pd.read_json("../../../data/beds.json")
df.sort_values(["department", "room", "hl7_bed"], inplace=True)

# prep department defaults
departments = df[
    [
        "hl7_department",
        "department_id",
        "department",
        "department_external_name",
        "department_speciality",
        "department_service_grouper",
        "department_level_of_care_grouper",
        "location_name",
    ]
].drop_duplicates()
departments.sort_values("department", inplace=True)
departments.set_index("department", inplace=True)

# locally saved starter values
df = pd.read_json("departments.json")
departments = departments.merge(df, on="department", how="left")
departments["closed_perm_01"] = departments["closed_perm_01"].str.contains(
    "True|1|TRUE"
)

# departments.to_excel("department_defaults.xlsx")
# Now hand edit the excel sheet
# then save the result and re-import
# departments = pd.read_excel("department_defaults.xlsx")
# quality control and save

departments.to_json("department_defaults.json", orient="records")
