# Steve Harris
# 2022-07-18
# built by hand reviewing the tower flow map July 2022
# then adding in WMS
# ward names represent department names in star.departments

wards = [
    # where n = number of distinct locations in EMAP
    #    NAME                           # n      seq
    "UCH T01 ACUTE MEDICAL",  # 86     1
    "UCH T01 ENHANCED CARE",  # 20     2
    "UCH T03 INTENSIVE CARE",  # 37     3
    "UCH T06 HEAD (T06H)",  # 27     4
    "UCH T06 CENTRAL (T06C)",  # 25     5
    "UCH T06 SOUTH PACU",  # 22     6
    "UCH T06 GYNAE (T06G)",  # 18     7
    "UCH T07 NORTH (T07N)",  # 45     8
    "UCH T07 CV SURGE",  # 37     9
    "UCH T07 SOUTH",  # 33    10
    "UCH T07 SOUTH (T07S)",  # 23    11
    "UCH T07 HDRU",  # 20    12
    "UCH T08 NORTH (T08N)",  # 28    13
    "UCH T08 SOUTH (T08S)",  # 25    14
    "UCH T08S ARCU",  # 6    15
    "UCH T09 SOUTH (T09S)",  # 34    16
    "UCH T09 NORTH (T09N)",  # 32    17
    "UCH T09 CENTRAL (T09C)",  # 25    18
    "UCH T10 SOUTH (T10S)",  # 34    19
    "UCH T10 NORTH (T10N)",  # 32    20
    "UCH T10 MED (T10M)",  # 16    21
    "UCH T11 SOUTH (T11S)",  # 27    22
    "UCH T11 NORTH (T11N)",  # 25    23
    "UCH T11 EAST (T11E)",  # 16    24
    "UCH T11 NORTH (T11NO)",  # 8    25
    "UCH T12 SOUTH (T12S)",  # 32    26
    "UCH T12 NORTH (T12N)",  # 23    27
    "UCH T13 SOUTH (T13S)",  # 31    28
    "UCH T13 NORTH ONCOLOGY",  # 26    29
    "UCH T13 NORTH (T13N)",  # 26    30
    "UCH T14 NORTH TRAUMA",  # 28    31
    "UCH T14 NORTH (T14N)",  # 28    32
    "UCH T14 SOUTH ASU",  # 22    33
    "UCH T14 SOUTH (T14S)",  # 17    34
    "UCH T15 SOUTH DECANT",  # 21    35
    "UCH T15 SOUTH (T15S)",  # 21    36
    "UCH T15 NORTH (T15N)",  # 16    37
    "UCH T15 NORTH DECANT",  # 15    38
    "UCH T16 NORTH (T16N)",  # 19    39
    "UCH T16 SOUTH (T16S)",  # 18    40
    "UCH T16 SOUTH WINTER",  # 17    41
    "GWB L01 ELECTIVE SURG",  # 37    42
    "GWB L01 CRITICAL CARE",  # 12    43
    "GWB L02 NORTH (L02N)",  # 19    44
    "GWB L02 EAST (L02E)",  # 19    45
    "GWB L03 NORTH (L03N)",  # 19    46
    "GWB L03 EAST (L03E)",  # 19    47
    "GWB L04 NORTH (L04N)",  # 20    48
    "GWB L04 EAST (L04E)",  # 17    49
    "WMS W01 CRITICAL CARE",  # 11    50
    "WMS W02 SHORT STAY",  # 20    51
    "WMS W03 WARD",  # 27    52
    "WMS W04 WARD",  # 28    53
    # NOTE: 2022-08-07 Adding in NHNN critical care areas ONLY for now
    "NHNN C0 NCCU",
    "NHNN C1 NCCU",
]

# beds that don't have a department and needed to be added in by hand
departments_missing_beds = {"UCH T06 CENTRAL (T06C)": ["T06C^T06C BY08^BY08-36"]}
