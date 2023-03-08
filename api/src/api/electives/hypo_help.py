"""

The majority of the code to wrangle dataframes is shared between HyPO and HyUI.
This set of helper functions is designed to be transferrable
without issues with dependencies.

This aims to solve the issue that otherwise changes in individual functions
would need to be transferred manually between two github repos.

"""
from typing import Any
import numpy as np
import pandas as pd


import re


def camel_to_snake(df: pd.DataFrame) -> pd.DataFrame:
    """Convert column names of a DataFrame from camelCase to snake_case."""
    df.columns = [re.sub(r"(?<!^)(?=[A-Z])", "_", col).lower() for col in df.columns]
    return df


def make_utc(df: pd.DataFrame, suffixes: list[str] = ["instant"]) -> pd.DataFrame:
    """cast dataframe cols to utc where the col name is suffixed by one of suffixes"""
    for suffix in suffixes:
        for column in df.loc[:, df.columns.str.endswith(suffix)]:
            df[column + "_utc"] = pd.to_datetime(df[column], utc=True)
    return df


def wrangle_surgical(df: pd.DataFrame) -> pd.DataFrame:

    terms_dict = {
        "priority": {
            "Two Week Wait": "Cancer Pathway",
            "*Unspecified": "Unknown",
        },
        "primary_anaesthesia_type": {
            "Sedation by Anaesthetist": "Sedation",
            "Sedation by Physician Assistant (Anaesthesia)": "Sedation",
            "Sedation by Physician Assistant (Anaesthesia) ": "Sedation",
            "Sedation by Endoscopist": "Sedation",
            "*Unspecified": "Unknown",
        },
        "primary_service": {
            "Special Needs Dental": "Other",
            "Paediatric Surgery": "Other",
            "Thoracic Medicine": "Other",
            "Paediatric Oncology": "Other",
            "Interventional Radiology": "Other",
            "Emergency Surgery": "Other",
        },
        "post_operative_destination": {
            "Paediatric Ward": "Other",
            "Overnight Recovery": "Other",
            "*Unspecified": "Other",
            "Endoscopy Ward": "Other",
            "*Not Applicable": "Other",
            "NICU": "Other",
        },
    }

    df.pipe(make_utc).replace(terms_dict)

    df = df[
        (df["touch_time_start_instant"].isna() & df["touch_time_end_instant"].isna())
        | (
            ~df["touch_time_start_instant"].isna()
            & ~df["touch_time_end_instant"].isna()
        )
    ]

    df["op_duration_minutes"] = (
        df["planned_operation_end_instant"] - df["planned_operation_start_instant"]
    ).astype("timedelta64[m]")

    # df.drop(["Firstname", "Lastname", "BirthDate"], axis=1, inplace=True)

    return df


def model_preassess(df: pd.DataFrame) -> pd.DataFrame:
    categories = {
        "cardio": "PROBLEMS - CARDIOVASCULAR|EXERCISE L|CARDIAC|HEART|CHEST PAIN",
        "resp": "RESPIRATORY|COPD|BRONCHIECT",
        "airway": "AIRWAY|RIDOR|HENT|PHARYN|NECK|NASAL",
        "infectious": "INFECTIOUS|COVID",
        "endo": "ENDOCRIN",
        "neuro": "NEUROLOGICAL|MUSCULAR DYSTROPHY|SPINE|MYASTH",
        "haem": "HAEMATOLOGY|SICKLE|LEUKAEMIA|BLOOD",
        "renal": "GENITOURINARY",
        "gastro": "GASTROINTESTINAL|LIVER",
        "CPET": "CPET DONE?",
        "mets": "SYMPTOMS - CARDIOVASCULAR - EXERCISE TOLERANCE",
        "anaesthetic_alert": "PAC NURSING OUTCOME|ALERT ANAESTHETIST ON DAY OF SURGERY",
        "pacdest": "POST-OP DESTINATION",
        "asa": "WORKFLOW - ANAESTHESIA - ASA STATUS",
        "urgency": "PROCEDURAL - GENERAL - PROCEDURE URGENCY",
        "prioritisation": "PACU/ITU BED PRIORITISATION",
        "c_line": "CENTRAL LINE RISKS",
        "a_line": "ARTERIAL LINE RISKS",
        "expected_stay": "EXPECTED LENGTH OF STAY IN ICU",
    }
    categories_dicts = {
        "mets": {
            "fair (4-7 METS)": 5,
            "excellent (>7 METS)": 8,
            ">4 METS": 5,
            "poor (<4 METS)": 2,
            "<4 METS": 2,
            "unable to ascertain": np.nan,
            "unable to assess": np.nan,
        },
        "pacdest": {
            "Inpatient Ward": "Inpatient Ward",
            "ITU/PACU Bed": "ICU/PACU",
            "Day Surgery Ward": "Day Surgery Ward",
        },
        "urgency": {
            "Expedited": "expedited",
            "Urgent": "urgent",
            "Immediate": "immediate",
            "Elective": "elective",
        },
        "airway": {"inspiratory": 1, "expiratory": 1, "at rest": 1},
        "renal": {
            "No": 0,
            "AKI": 1,
            "Stage 1": 1,
            "Stage 2": 2,
            "Yes": 2,
            "CKD": 2,
            "Stage 3 CKD": 3,
            "Stage 3": 3,
            "Stage 4 CKD": 4,
            "Stage 4": 4,
            "kidney transplant": 5,
            "haemodialysis": 5,
            "dialysis dependent": 5,
            "Stage 5 CKD": 5,
            "Stage 5/ESRF": 5,
            "peritoneal dialysis": 5,
        },
        "anaesthetic_alert": {
            "OK to proceed": 0,
            "Fit for surgery": 0,
            "Referred to anaesthetist": 1,
            "Yes": 1,  # for "alert anaesthetist on day of surgery" field
            "Further tests / optimisation required": 2,
            "Not fit for surgery": 2,
        },
        "cardio": {
            "Breathing": 2,
            "Fatigue": 1,
            "Leg pain": 1,
            "Chest pain": 2,
            "hypertrophic (HCM)": 2,
            "dilated (DCM)": 2,
            "Joint pain": 0,  # exercise limited by
            "Other": 0,
            "Balance": 0,
            "mild": 1,
            "moderate": 2,
            "severe": 3,
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
        },
        "resp": {
            "mild": 1,
            "Yes": 1,
            "physiotherapy": 1,
            "antibiotics": 1,
            "inspiratory": 1,
            "expiratory": 1,
            "corticosteroids": 2,
            "moderate": 2,
            "at rest": 2,
            "hospitalisation": 2,
            "severe": 3,
            "home nebs": 3,
            "home oxygen": 3,
        },
        "gastro": {
            "non-alcoholic fatty liver disease": 1,
            "alcoholic fatty liver disease": 1,
            "cirrhosis": 2,
            "jaundice": 2,
            "portal hypertension": 2,
            "coagulopathy": 2,
        },
    }
    for c in categories:
        df[c] = df[df["name"].str.contains(categories[c])]["string_value"]

    df.replace(categories_dicts, inplace=True)

    df.loc[:, list(categories.keys())] = df[list(categories.keys())].replace("No", 0)
    df.loc[:, list(categories.keys())] = df[list(categories.keys())].replace("Yes", 1)
    df.loc[~df["a_line"].isna(), "a_line"] = 1
    df.loc[~df["c_line"].isna(), "c_line"] = 1

    df.loc[:, ["a_line", "c_line", "expected_stay", "asa"]] = df[
        ["a_line", "c_line", "expected_stay", "asa"]
    ].astype("float", errors="ignore")

    # df["creation_instant"] = pd.to_datetime(df["creation_instant"])

    note_nums = (
        df.groupby(["patient_durable_key", "creation_instant", "author_type"])
        .agg("sum", numeric_only=True)
        .reset_index()
        .drop("numeric_value", axis=1)
    )

    note_nums["a_line"] = note_nums["a_line"].astype(bool).astype(int)
    note_nums["c_line"] = note_nums["a_line"].astype(bool).astype(int)

    note_nums = note_nums[
        [
            "patient_durable_key",
            "creation_instant",
            "author_type",
            "cardio",
            "resp",
            "airway",
            "infectious",
            "endo",
            "neuro",
            "haem",
            "renal",
            "gastro",
            "CPET",
            "mets",
            "anaesthetic_alert",
            "asa",
            "a_line",
            "c_line",
            "expected_stay",
        ]
    ]

    note_strings = (
        df.groupby(["patient_durable_key", "creation_instant", "author_type"])
        .first()[["urgency", "pacdest", "prioritisation"]]
        .reset_index()
    )
    all_notes = note_nums.merge(
        note_strings.drop("author_type", axis=1),
        on=["patient_durable_key", "creation_instant"],
    )
    all_notes["preassess_date"] = all_notes["creation_instant"].dt.date

    return all_notes


def merge_surg_preassess(
    surg_data: pd.DataFrame, preassess_data: pd.DataFrame
) -> pd.DataFrame:
    data_surg = wrangle_surgical(surg_data)

    data_preassess = model_preassess(preassess_data)

    linked_notes = data_surg.merge(
        data_preassess, on="patient_durable_key", how="left"
    ).query("surgery_date >= preassess_date")

    merged_df = linked_notes[
        linked_notes["creation_instant"]
        == linked_notes.groupby(["patient_durable_key", "surgery_date"])[
            "creation_instant"
        ].transform(max)
    ]
    return merged_df


def wrangle_labs(labs: pd.DataFrame) -> pd.DataFrame:
    # this takes some particular lab results from 4 months prior to the operation.

    labs_limits = {
        "crea": (49, 112),
        "hb": (115, 170),
        "wcc": (3, 10),
        "plt": (150, 400),
        "na": (135, 145),
        "alb": (34, 50),
        "crp": (0, 5),
        "bili": (0, 20),
        "inr": (0.8, 1.3),
    }
    lab_names = {
        "na": "Sodium",
        "crea": "Creatinine",
        "wcc": "White cell count",
        "hb": "Haemoglobin (g/L)",
        "plt": "Platelet count",
        "alb": "Albumin",
        "bili": "Bilirubin (total)",
        "inr": "INR",
        "crp": "C-reactive protein",
    }

    op_dict = {
        "mean": "_mean_value",
        "min": "_min_value",
        "max": "_max_value",
        "count": "_measured_count",
    }

    df = labs.copy()

    df.loc[:, "value"] = pd.to_numeric(
        df["value"].str.replace("<|(result checked)", "", regex=True),
        errors="coerce",
    ).dropna()
    df["name"] = df["name"].replace({v: k for k, v in lab_names.items()})
    df = df.join(df.pivot(columns="name", values="value"))

    for key in lab_names:
        df[key + "_abnormal_count"] = df[key].groupby(
            df["patient_durable_key"]
        ).transform(lambda x: x > labs_limits[key][1]) | df[key].groupby(
            df["patient_durable_key"]
        ).transform(
            lambda x: x < labs_limits[key][0]
        )

        for op in op_dict:
            df[key + op_dict[op]] = (
                df[key].groupby(df["patient_durable_key"]).transform(op)
            )
    gdf = df.groupby("patient_durable_key").sum(numeric_only=True)
    gdf = gdf.loc[:, gdf.columns.str.contains("_abnormal")]

    hdf = df.groupby("patient_durable_key").mean(numeric_only=True)
    hdf = hdf.loc[:, hdf.columns.str.contains("_m")]

    idf = df.sort_values("result_instant").groupby("patient_durable_key").last()
    idf = idf.loc[:, list(lab_names.keys())]

    final_df = gdf.join(hdf).join(idf.add_suffix("_last_value")).reset_index()

    return final_df


def j_wrangle_obs(caboodle_obs: pd.DataFrame) -> pd.DataFrame:

    caboodle_obs.loc[:, "month_pre_theatre"] = caboodle_obs.loc[
        :, "planned_operation_start_instant"
    ] - pd.to_timedelta(16, unit="W")

    caboodle_obs = caboodle_obs[
        (
            caboodle_obs.loc[:, "taken_instant"]
            < caboodle_obs.loc[:, "planned_operation_start_instant"]
        )
        & (
            caboodle_obs.loc[:, "first_documented_instant"]
            < caboodle_obs.loc[:, "planned_operation_start_instant"]
        )
        & (
            caboodle_obs.loc[:, "taken_instant"]
            > caboodle_obs.loc[:, "month_pre_theatre"]
        )
        & (
            caboodle_obs.loc[:, "first_documented_instant"]
            > caboodle_obs.loc[:, "month_pre_theatre"]
        )
    ]

    numerical_obs_list = ["Resp", "Temp", "SpO2", "Pulse", "BMI (Calculated)"]

    text_obs_list = ["BP", "Room Air or Oxygen"]

    # Split to numerical and text obs for processing
    numerical_obs = caboodle_obs[
        caboodle_obs.loc[:, "display_name"].isin(numerical_obs_list)
    ]
    numerical_obs = numerical_obs[~numerical_obs["numeric_value"].isna()]

    text_obs = caboodle_obs[caboodle_obs.loc[:, "display_name"].isin(text_obs_list)]
    text_obs = text_obs[text_obs["value"] != ""]

    # Process text obs
    text_obs[["SYS_BP", "DIAS_BP"]] = text_obs[text_obs.loc[:, "display_name"] == "BP"][
        "value"
    ].str.split("/", 1, expand=True)

    text_obs.loc[:, "SYS_BP"].fillna(value=np.nan, inplace=True)
    text_obs.loc[:, "DIAS_BP"].fillna(value=np.nan, inplace=True)

    text_obs.loc[:, "SYS_BP"] = text_obs.loc[:, "SYS_BP"].apply(lambda x: float(x))
    text_obs.loc[:, "DIAS_BP"] = text_obs.loc[:, "DIAS_BP"].apply(lambda x: float(x))

    oxygen_conditions = [
        (text_obs.loc[:, "display_name"] == "Room Air or Oxygen")
        & (text_obs.loc[:, "value"] == "Supplemental Oxygen"),
        (text_obs.loc[:, "display_name"] == "Room Air or Oxygen")
        & (text_obs.loc[:, "value"] == "Room air"),
        (text_obs.loc[:, "display_name"] != "Room Air or Oxygen"),
    ]

    oxygen_codes = (1, 0, np.nan)

    text_obs.loc[:, "ON_OXYGEN_BIN"] = np.select(oxygen_conditions, oxygen_codes)

    text_obs = text_obs.drop(
        columns=["value", "numeric_value", "display_name", "month_pre_theatre"]
    )

    bp_obs = text_obs[
        [
            "surgical_case_key",
            "first_documented_instant",
            "taken_instant",
            "planned_operation_start_instant",
            "SYS_BP",
            "DIAS_BP",
        ]
    ]

    bp_obs = bp_obs[~bp_obs["SYS_BP"].isna()]
    bp_obs = bp_obs.drop_duplicates()

    o2_obs = text_obs[
        [
            "surgical_case_key",
            "first_documented_instant",
            "taken_instant",
            "planned_operation_start_instant",
            "ON_OXYGEN_BIN",
        ]
    ]

    o2_obs = o2_obs[~o2_obs["ON_OXYGEN_BIN"].isna()]
    o2_obs = o2_obs.drop_duplicates()

    text_obs = bp_obs.merge(
        o2_obs,
        on=[
            "surgical_case_key",
            "first_documented_instant",
            "taken_instant",
            "planned_operation_start_instant",
        ],
        how="outer",
    )

    text_obs.loc[text_obs["SYS_BP"] == 0, "SYS_BP"] = 120
    text_obs.loc[text_obs["SYS_BP"] < 60, "SYS_BP"] = 60
    text_obs.loc[text_obs["SYS_BP"] > 240, "SYS_BP"] = 240
    text_obs.loc[text_obs["DIAS_BP"] == 0, "DIAS_BP"] = 70
    text_obs.loc[text_obs["DIAS_BP"] < 40, "DIAS_BP"] = 40
    text_obs.loc[text_obs["DIAS_BP"] > 160, "DIAS_BP"] = 160

    # Process numerical obs

    obs_long_names_conditions = [
        (numerical_obs["display_name"] == "SpO2"),
        (numerical_obs["display_name"] == "Pulse"),
        (numerical_obs["display_name"] == "Resp"),
        (numerical_obs["display_name"] == "Temp"),
        (numerical_obs["display_name"] == "BMI (Calculated)"),
    ]

    values_obs_codes = ("SPO2", "PULSE", "RR", "TEMP", "BMI")

    numerical_obs.loc[:, "obs_code"] = np.select(
        obs_long_names_conditions, values_obs_codes
    )

    numerical_obs = numerical_obs.drop(
        columns=["value", "display_name", "month_pre_theatre"]
    )

    numerical_obs = numerical_obs.pivot_table(
        index=[
            "surgical_case_key",
            "planned_operation_start_instant",
            "first_documented_instant",
            "taken_instant",
        ],
        values="numeric_value",
        columns="obs_code",
    )

    numerical_obs.reset_index(inplace=True)
    numerical_obs.columns.name = None

    # convert temp to deg C

    numerical_obs.loc[:, "TEMP"] = (numerical_obs.loc[:, "TEMP"] - 32) * (5 / 9)

    numerical_obs.loc[numerical_obs["BMI"] == 0, "BMI"] = 25
    numerical_obs.loc[numerical_obs["BMI"] < 16, "BMI"] = 16
    numerical_obs.loc[numerical_obs["BMI"] > 60, "BMI"] = 60
    numerical_obs.loc[numerical_obs["PULSE"] == 0, "PULSE"] = 60
    numerical_obs.loc[numerical_obs["PULSE"] < 40, "PULSE"] = 40
    numerical_obs.loc[numerical_obs["PULSE"] > 200, "PULSE"] = 200
    numerical_obs.loc[numerical_obs["RR"] == 0, "RR"] = 12
    numerical_obs.loc[numerical_obs["RR"] < 6, "RR"] = 6
    numerical_obs.loc[numerical_obs["RR"] > 60, "RR"] = 6
    numerical_obs.loc[numerical_obs["SPO2"] == 0, "SPO2"] = 98
    numerical_obs.loc[numerical_obs["SPO2"] < 80, "SPO2"] = 80
    numerical_obs.loc[numerical_obs["TEMP"] == 0, "TEMP"] = 36
    numerical_obs.loc[numerical_obs["TEMP"] < 34, "TEMP"] = 34
    numerical_obs.loc[numerical_obs["TEMP"] > 42, "TEMP"] = 42

    # remerge obs

    all_obs = text_obs.merge(
        numerical_obs,
        on=[
            "surgical_case_key",
            "first_documented_instant",
            "taken_instant",
            "planned_operation_start_instant",
        ],
        how="outer",
    )

    # create abnormal flag

    preadm_obs_list = [
        "SYS_BP",
        "DIAS_BP",
        "ON_OXYGEN_BIN",
        "PULSE",
        "RR",
        "SPO2",
        "TEMP",
    ]
    obs_low_limit = (100, 50, 0, 50, 8, 94, 35.5)
    obs_high_limit = (160, 100, 0, 90, 20, 100, 37.5)

    for ob, low, high in zip(preadm_obs_list, obs_low_limit, obs_high_limit):
        all_obs[ob + "_abnormal_flag"] = np.where(
            np.logical_or(all_obs[ob] > high, all_obs[ob] < low), 1, 0
        )

    # print("Abnormal", ob, "results: ", str(all_obs[ob+"_abnormal_flag"].sum()))

    # process aggregate stats

    for ob in preadm_obs_list:
        all_obs[ob + "_abnormal_count"] = all_obs.groupby(["surgical_case_key"])[
            ob + "_abnormal_flag"
        ].transform(sum)

    for ob in preadm_obs_list:
        all_obs[ob + "_measured_count"] = all_obs.groupby(["surgical_case_key"])[
            ob
        ].transform("count")

    for ob in preadm_obs_list:
        all_obs[ob + "_last_value"] = (
            all_obs.sort_values("taken_instant")
            .groupby(["surgical_case_key"])[ob]
            .transform("last")
        )

    for ob in preadm_obs_list:
        all_obs[ob + "_mean_value"] = all_obs.groupby(["surgical_case_key"])[
            ob
        ].transform("mean")

    for ob in preadm_obs_list:
        all_obs[ob + "_min_value"] = all_obs.groupby(["surgical_case_key"])[
            ob
        ].transform(min)

    for ob in preadm_obs_list:
        all_obs[ob + "_max_value"] = all_obs.groupby(["surgical_case_key"])[
            ob
        ].transform(max)

    all_obs["bmi_max_value"] = all_obs.groupby(["surgical_case_key"])["BMI"].transform(
        max
    )

    # Drop cols not using as predictors
    cols_to_drop_obs = (
        preadm_obs_list
        + [ob + "_abnormal_flag" for ob in preadm_obs_list]
        + ["first_documented_instant", "taken_instant", "BMI"]
    )

    obs = all_obs.drop(columns=cols_to_drop_obs).drop_duplicates()

    return obs


def wrangle_echo(df: pd.DataFrame) -> pd.DataFrame:

    """

    this is clearly much simpler than jen's wrangle_echo above.
    I have written a different .sql script
    that also pulls the 'IsAbnormal' flag from EPIC.
    For now, this then only tells us how many echos patients have had,
    and how many of those were flagged as abnormal by the person doing the scan.

    This is not ideal as IsAbnormal does not necessarily seem to be accurate.
    It also removes lots of potentially useful information.
    """
    wrangled = (
        df.groupby("patient_durable_key")
        .agg({"patient_durable_key": "size", "is_abnormal": "sum"})
        .rename(
            columns={"patient_durable_key": "num_echo", "is_abnormal": "abnormal_echo"}
        )
        .reset_index()
        .merge(
            df[["patient_durable_key", "narrative", "date_value"]],
            how="left",
            on="patient_durable_key",
        )
        .sort_values("date_value")
        .drop_duplicates("patient_durable_key", keep="last")
        .rename(
            columns={"narrative": "last_echo_narrative", "date_value": "last_echo_date"}
        )
    )
    return wrangled


def fill_na(df: pd.DataFrame) -> pd.DataFrame:

    df.loc[:, df.columns.str.contains("_count")] = df.loc[
        :, df.columns.str.contains("_count")
    ].fillna(0)

    replace_dict = {"num_echo": 0, "abnormal_echo": 0, "bmi_max_value": 22.5}
    lab_obs_dict = {
        "SPO2": 98,
        "PULSE": 70,
        "RR": 12,
        "TEMP": 36.5,
        "SYS_BP": 120,
        "DIAS_BP": 80,
        "ON_OXYGEN_BIN": 0,
        "crea": 70,
        "hb": 130,
        "wcc": 6.5,
        "plt": 275,
        "na": 140,
        "alb": 42,
        "crp": 0.6,
        "bili": 10,
        "inr": 1,
    }

    for k, v in lab_obs_dict.items():
        replace_dict.update(
            {
                k + "_last_value": v,
                k + "_mean_value": v,
                k + "_min_value": v,
                k + "_max_value": v,
            }
        )

    df.fillna(value=replace_dict, inplace=True)
    return df


def wrangle_pas(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values(["patient_durable_key", "creation_instant"])
        .drop_duplicates("patient_durable_key", keep="last")
        .loc[:, ["patient_durable_key", "creation_instant"]]
        .merge(df, on=["patient_durable_key", "creation_instant"], how="left")
        .replace(
            {
                "name": {
                    "PAC NURSING ISSUES FOR FOLLOW UP": "pac_nursing_issues",
                    "PAC NURSING OUTCOME": "pac_nursing_outcome",
                    "PRE-ASSESSMENT ANAESTHETIC REVIEW": "pac_dr_review",
                }
            }
        )
        .sort_values(["patient_durable_key", "name", "line_num"])
        .groupby(["patient_durable_key", "name", "creation_instant"])
        .agg({"string_value": "".join})
        .pivot_table(
            index=["patient_durable_key", "creation_instant"],
            columns=["name"],
            values="string_value",
            aggfunc="".join,
        )
        .reset_index()
        .rename(columns={"creation_instant": "pac_date"})
    )


def wrangle_hx(hx: pd.DataFrame) -> pd.DataFrame:
    icd_codes = (
        ("A00", "B99", "I"),
        ("C00", "D48", "II"),
        ("D50", "D89", "III"),
        ("E00", "E90", "IV"),
        ("F00", "F99", "V"),
        ("G00", "G99", "VI"),
        ("H00", "H59", "VII"),
        ("H60", "H95", "VIII"),
        ("I00", "I99", "IX"),
        ("J00", "J99", "X"),
        ("K00", "K93", "XI"),
        ("L00", "L99", "XII"),
        ("M00", "M99", "XIII"),
        ("N00", "N99", "XIV"),
        ("O00", "O99", "XV"),
        ("P00", "P96", "XVI"),
        ("Q00", "Q99", "XVII"),
        ("R00", "R99", "XVIII"),
        ("S00", "T98", "XIX"),
        ("U00", "U99", "XX"),
        ("V01", "Y98", "XXI"),
        ("Z00", "Z99", "XXII"),
    )

    def _get_class(code: str, icd_codes: dict) -> Any:
        for icd in icd_codes:
            if code >= icd[0] and code <= icd[1]:
                return icd[2]
        return None

    hx = hx.drop(hx[hx["value"] == "#NC"].index)
    hx["class"] = hx["value"].str.slice(0, 3).apply(_get_class, icd_codes=icd_codes)

    one_hot = pd.get_dummies(hx["class"])
    one_hot["patient_durable_key"] = hx["patient_durable_key"]
    counts = one_hot.groupby("patient_durable_key").sum()

    return counts
