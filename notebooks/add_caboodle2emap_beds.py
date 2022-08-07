"""
Join
- caboodle.caboodle_report.DepartmentDim
- emap.star.location

Notes
- don't attempt joins where there is no room/bed level data (b/c they're not physical locations
- you need a multi-key join
    - EMAP 'name' (department.name) joins on to Caboodle 'DepartmentName'
    - EMAP 'bed' (derived by splitting location.location_string) joins on to Caboodle 'Name'
- drop 'wait' beds since these duplicate and block a one-to-one merge
- try to be rigorous in `pd.merge`
    - `indicator=True` to allow inspection post merge
    - `validate='one_to_one'` to throw an error if duplicates found
- sometimes (in Caboodle) DepartmentName and Name are duplicated so pick the most recently 'created'

Set-up the tables as follows (given an engine/connection)
```python
q = "SELECT lo.location_id, lo.location_string, lo.department_id, lo.room_id, lo.bed_id, dept.name, dept.speciality FROM star.location lo LEFT JOIN star.department dept ON lo.department_id = dept.department_id"
dfe = pd.read_sql_query(q, emap_engine)
dfe.head()

q = "SELECT *FROM dbo.DepartmentDim"
dfc = pd.read_sql_query(q, caboodle_engine)
dfc.head()
```

Issues
- 2022-08-07 approach fails where EMAP does not hold a department/room/bed record
  e.g. `1020200074^C0NCCU HDU SR30^HDU-30 SR` does not exist in EMAP other than as a location string


"""
import pandas as pd
from typing import List


def bed_merge(
    df_emap: pd.DataFrame,
    df_caboodle: pd.DataFrame,
    departments: List = [],
) -> pd.DataFrame:
    """

    Field Names for matching
    Caboodle : EMAP

    DepartmentDim.DepartmentName : department.name
    DepartmentDim.DepartmentSpecialty : department.speciality
    DepartmentDim.RoomName : room.name
    DepartmentDim.BedName : 3rd fragment of location.location_string

    """
    # make copies of the dataframe so you don't accidentally mutate the original
    dfe = df_emap.copy()
    dfc = df_caboodle.copy()
    if departments:
        maskc = dfc["DepartmentName"].isin(departments)
        dfc = dfc[maskc]
        maske = dfe["department"].isin(departments)
        dfe = dfe[maske]

    # clean emap data
    # drop locations that don't have a room or a bed
    dfe = dfe.loc[
        ~dfe.bed_id.isnull() | ~dfe.room_id.isnull() | dfe.department_id.isnull()
    ]
    dfe[["dept", "room_hl7", "bed"]] = dfe["location_string"].str.split(
        "^", expand=True
    )

    # drop non bed locations
    # incomplete list ... but I don't think this is so important if once you've removed non-bed/non-rooms above
    emap_virtual_rooms = [
        "WAITING",
        "CHAIRS",
        "POOL ROOM",
        "DENTAL CHAIRS",
        "ADULT TRIAGE",
        "LOUNGE",
        "ARRIVED",
        "DISCHARGE",
        "WAIT",
        "VIRTUAL GI",
        "VIRTUAL T&O",
        "POOL",
        "CLINIC",
        "OTF",
        "L&D PACU",
        "MAJAX P03 RECOVERY",
        "VIRTUAL UROLOGY",
        "REVIEW AND BLOOD TEST BAY",
        "PHYSIO",
        "PROC",
        "IR",
        "LITHOTRIPSY ROOM",
        "IN TREATMENT",
        "CORRIDOR",
        "LEAVE OF ABSCENCE",
        "KITCHEN",
        "HOME",
        "WAITING ROOM",
        "VIRTUAL ENDOSCOPY",
        "DAYCASE",
        "MAJAX P01 SURGICAL RECEPTION",
        "MAJAX P02 ENDOSCOPY",
    ]
    emap_virtual_beds = [
        "POOL",
        "NONE",
        "ENDO",
        "IMG",
        "OUT PG",
        "IR",
        "WAIT",
        "IR",
        "THR",
        "WAITING",
        "OTF",
        "ARRIVED",
        "CHAIR",
        "VIRTUAL",
        "-",
        "PLASTER ROOM",
        "TREATMENT ROOM",
        "OPHTHALMOLOGY ROOM",
    ]

    dfe = dfe[(~dfe["bed"].isin(emap_virtual_beds)) & (~dfe["department_id"].isnull())]

    # make key to merge and force to lower etc
    dfe["loc2merge"] = dfe.agg(
        lambda x: f"{x['speciality']} __ {x['department']} __ {x['room']} __ {x['bed']}".lower(),
        axis=1,
    )
    print(dfe.loc2merge)

    # clean caboodle data
    dfc = dfc[
        (dfc["IsBed"] == 1)  # only 'beds'
        & (
            dfc["Name"] != "WAIT"
        )  # drop 'waiting areas' TODO: this list should be longer?
        & (~dfc["DepartmentType"].isin(["OR"]))  # excluding OR (Operating Room)
    ]

    # still left with dups so now choose the most recent
    dfc.sort_values(
        by=["DepartmentName", "RoomName", "BedName", "_CreationInstant"], inplace=True
    )
    dfc.drop_duplicates(
        subset=["DepartmentName", "RoomName", "BedName"], keep="last", inplace=True
    )

    # make key to merge and force to lower etc
    dfc["loc2merge"] = dfc.agg(
        lambda x: f"{x['DepartmentSpecialty']} __ {x['DepartmentName']} __ {x['RoomName']} __ {x['Name']}".lower(),
        axis=1,
    )
    print(dfc.loc2merge)

    # merge
    dfm = dfe.merge(
        dfc, on="loc2merge", how="left", indicator=True, validate="one_to_one"
    )
    return dfm
