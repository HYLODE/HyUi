"""
Prepare
- room_defaults.json
to be loaded into baserow from an extract of data from Epic and EMAP
plus hand collated data
"""
# Runs from a Python console in this directory
import pandas as pd
import warnings

df = pd.read_json("../../../data/beds.json")
df.sort_values(["department", "room", "hl7_bed"], inplace=True)
df.info()

# prep department defaults
rooms = df[
    [
        "room",
        "room_id",
        "hl7_room",
        "department",
    ]
].drop_duplicates()

# locally saved starter values
df = pd.read_json("rooms.json")
df = df[["hl7_room", "has_beds"]]
try:
    rooms = rooms.merge(df, on="hl7_room", how="left")
except KeyError as e:
    print(e)
    warnings.warn("Unable to merge rooms.json; possible that rooms.json is " "empty?")

rooms["is_sideroom"] = rooms["room"].str.contains(r"SR")
rooms["has_beds"] = rooms["has_beds"] != False  # noqa: E712

# rooms.to_excel("room_defaults.xlsx")
# Now hand edit the Excel sheet
# then save the result and re-import
# rooms = pd.read_excel("room_defaults.xlsx")
# quality control and save

rooms.to_json("room_defaults.json", orient="records")
