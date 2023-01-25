"""
Prepare
- bed_defaults.json
to be loaded into baserow from an extract of data from Epic and EMAP
plus hand collated data
"""
# Runs from a Python console in this directory
import pandas as pd

df = pd.read_json("../../../data/beds.json")
bed_fields = [
    "department",
    "room",
    "hl7_bed",
    "location_id",
    "location",
    "hl7_department",
    "hl7_room",
    "department_id",
    "room_id",
    "bed_id",
]
beds = df[bed_fields]
beds.rename(columns={"location": "location_string"}, inplace=True)
beds[["bed_split_1", "bed_split_2"]] = beds["hl7_bed"].str.split("-", expand=True)

departments = pd.read_json("json/department_defaults.json")
floors = departments.loc[:, ["department", "floor", "location_name"]]
beds = beds.merge(floors, how="left", on="department")
beds["bed_number"] = beds.loc[:, "bed_split_2"].str.extract(r"(\d+)")
beds.sort_values(
    ["location_name", "floor", "department", "bed_number"],
    inplace=True,
    na_position="last",
)
beds["bed_number"] = beds["bed_number"].fillna(-1).astype(int)
beds.drop(columns=["bed_split_1", "bed_split_2"], inplace=True)
df = pd.read_json("json/beds.json")
df.drop(
    columns=[
        "department",
        "hl7_bed",
        "covid",
    ],
    inplace=True,
)
df["closed"] = df["closed"].str.contains("True|1|TRUE")
df["blocked"] = df["blocked"].str.contains("True|1|TRUE")
df["xpos"] = df["xpos"].fillna(-1).astype(int)
df["ypos"] = df["ypos"].fillna(-1).astype(int)
beds = beds.merge(df, on="location_string", how="left")
beds["closed"].fillna(False, inplace=True)
beds["blocked"].fillna(False, inplace=True)

# beds.to_excel("bed_defaults.xlsx", index=False)
# Now hand edit if you wish, read back in, and then save as json
# beds = pd.read_excel("bed_defaults.xlsx")
beds["xpos"] = beds["xpos"].fillna(-1).astype(int)
beds["ypos"] = beds["ypos"].fillna(-1).astype(int)
beds["floor"] = beds["floor"].fillna(-1).astype(int)
beds.loc[beds["bed_number"] == -1, "closed"] = True
beds.to_json("json/bed_defaults.json", orient="records")
