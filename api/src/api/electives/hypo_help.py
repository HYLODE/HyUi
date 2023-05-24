"""
2022-12-20 hypo_help.py

The majority of the code to wrangle dataframes is shared between HyPO and HyUI.
This set of helper functions is designed to be transferrable
without issues with dependencies.

This aims to solve the issue that otherwise changes in individual functions
would need to be transferred manually between two github repos.

"""
from typing import Any
import numpy as np
import pandas as pd

from datetime import datetime, timezone


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


def simple_sum(df: pd.DataFrame) -> pd.DataFrame:
    surg_columns: list[str] = []
    preassess_columns = [
        # "cardio",
        "resp",
        "airway",
        "infectious",
        "endo",
        "neuro",
        "haem",
        "renal",
        "gastro",
        "CPET",
        # "mets",
        "anaesthetic_alert",
        "asa",
        "c_line",
        "a_line",
    ]
    lab_names = ["na", "crea", "wcc", "hb", "plt", "alb", "bili", "inr", "crp"]
    lab_columns = [ln + "_abnormal_count" for ln in lab_names]
    echo_columns = ["echo_abnormal"]
    obs_columns = [
        "bmi_max_value",
    ]  # TODO actually write this

    columns_to_sum = (
        surg_columns + preassess_columns + lab_columns + echo_columns + obs_columns
    )
    df["simple_score"] = (
        df[columns_to_sum].replace(np.nan, 0).astype("bool").sum(axis=1)
    )
    return df


def j_wrangle_echo(df: pd.DataFrame) -> pd.DataFrame:
    df["finding"] = df["finding_type"] + " " + df["finding_name"]

    findings_categorical = [
        "Aortic Valve regurgitation severity",
        "Aortic Valve stenosis",
        "Left Ventricle left ventricular cavity size",
        "Left Ventricle diastolic filling",
        "Left Ventricle ejection fraction",
        "Left Ventricle impaired",
        "Mitral Valve regurgitation severity",
        "Mitral Valve stenosis severity",
        "Pulmonary Hypertension moderate",
        "Pulmonary Hypertension severe",
        "Pulmonic Valve regurgitation severity",
        "Pulmonic Valve stenosis severity",
        "Right Ventricle cavity size",
        "Right Ventricle global systolic function",
        "Tricuspid Valve regurgitation severity",
        "Tricuspid Valve stenosis severity",
        "Pulmonary Hypertension Probability of pulmonary hypertension",
    ]

    findings_string = [
        "Left Ventricle Comment",
        "Left Ventricle ejection fraction comments",
        "Pulmonary Hypertension pulmonary hypertension",
    ]

    findings_numerical = [
        "*Not Applicable RV TAPSE (TV annulus)",
        "*Not Applicable Echo EF Estimated",
        "*Not Applicable EF (Mod BP)",
        "*Not Applicable PASP",
        "Pulmonary Hypertension estimated PA systolic pressure",
    ]

    # split findings into those of interest by data type
    df_numeric = df[df["finding"].isin(findings_numerical)]
    df_string = df[df["finding"].isin(findings_string)]
    df_cat = df[df["finding"].isin(findings_categorical)]

    # extract EF values from LV comments strings
    df_string.loc[:, "lv_string_value"] = df_string.loc[
        df_string["finding"] == "Left Ventricle Comment", "string_value"
    ].apply(lambda x: re.findall(r"\d*[%]", x))
    df_string.loc[:, "lv_string_value"] = df_string.loc[:, "lv_string_value"].apply(
        lambda d: d if isinstance(d, list) else []
    )
    df_string.loc[:, "lv_string_value"] = df_string.loc[:, "lv_string_value"].str[0]
    df_string.loc[
        ~df_string["lv_string_value"].isna(), "lv_string_value"
    ] = df_string.loc[~df_string["lv_string_value"].isna(), "lv_string_value"].apply(
        lambda x: x.replace("%", "")
    )
    df_string.loc[:, "lv_string_value"] = (
        df_string.loc[:, "lv_string_value"]
        .replace(r"^\s*$", np.nan, regex=True)
        .apply(float)
    )
    df_string.loc[
        ~df_string["lv_string_value"].isna(), "lv_string_value"
    ] = df_string.loc[~df_string["lv_string_value"].isna(), "lv_string_value"].apply(
        lambda x: float(x)
    )

    # extract EF values from LVEF comments strings
    df_string.loc[:, "lv_string_value_2"] = df_string.loc[
        df_string["finding"] == "Left Ventricle ejection fraction comments",
        "string_value",
    ].apply(lambda x: re.findall(r"\d*[%]", x))
    df_string.loc[:, "lv_string_value_2"] = df_string.loc[:, "lv_string_value_2"].apply(
        lambda d: d if isinstance(d, list) else []
    )
    df_string.loc[:, "lv_string_value_2"] = df_string.loc[:, "lv_string_value_2"].str[0]
    df_string.loc[
        ~df_string["lv_string_value_2"].isna(), "lv_string_value_2"
    ] = df_string.loc[
        ~df_string["lv_string_value_2"].isna(), "lv_string_value_2"
    ].apply(
        lambda x: x.replace("%", "")
    )
    df_string.loc[:, "lv_string_value_2"] = (
        df_string.loc[:, "lv_string_value_2"]
        .replace(r"^\s*$", np.nan, regex=True)
        .apply(float)
    )
    df_string.loc[
        ~df_string["lv_string_value_2"].isna(), "lv_string_value_2"
    ] = df_string.loc[
        ~df_string["lv_string_value_2"].isna(), "lv_string_value_2"
    ].apply(
        lambda x: float(x)
    )

    # Extract PASP strings from PH comments
    df_string.loc[:, "contains PASP value"] = df_string.loc[
        df_string["finding"] == "Pulmonary Hypertension pulmonary hypertension",
        "string_value",
    ].apply(lambda x: np.where(("PASP" in x) | ("systolic pressure" in x), 1, 0))
    df_string.loc[:, "PH_string_value"] = df_string.loc[
        (
            (df_string["finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["contains PASP value"] == 1)
        ),
        "string_value",
    ].apply(lambda x: re.findall(r"\d*\.?\d+", x))
    df_string.loc[:, "PH_string_value"] = df_string.loc[
        (
            (df_string["finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["contains PASP value"] == 1)
        ),
        "PH_string_value",
    ].apply(lambda x: [float(i) for i in x])

    def get_first_above_8(list_of_nos: list[float]) -> float:
        item = next((x for x in list_of_nos if ((x > 8) & (x < 80))), np.nan)
        return item

    df_string.loc[:, "PH_string_value"] = df_string.loc[
        (
            (df_string["finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["contains PASP value"] == 1)
        ),
        "PH_string_value",
    ].apply(lambda x: get_first_above_8(x))
    df_string = df_string.drop(columns=["contains PASP value"])

    # convert selected PH comment strings to binary vars
    df_string["pulm_HTN_string_bin"] = np.where(
        (
            (df_string["finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["string_value"] == "1")
        ),
        1,
        np.nan,
    )
    df_string["pulm_HTN_string_moderate"] = np.where(
        (
            (df_string["finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["string_value"] == "moderate")
        ),
        1,
        np.nan,
    )
    df_string["pulm_HTN_string_severe"] = np.where(
        (
            (df_string["finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["string_value"] == "severe")
        ),
        1,
        np.nan,
    )

    # keep only features generated from string columns
    df_string = df_string.drop(
        columns=[
            "finding_type",
            "finding_name",
            "string_value",
            "numeric_value",
            "unit",
            "finding",
        ]
    )

    # rename numeric values and pivot table
    df_numeric = df_numeric.replace(
        {
            "finding": {
                "*Not Applicable RV TAPSE (TV annulus)": "TAPSE_num",
                "*Not Applicable Echo EF Estimated": "EF_est_num",
                "*Not Applicable EF (Mod BP)": "EF_mbp_num",
                "*Not Applicable PASP": "PASP_num",
                "Pulmonary Hypertension estimated PA systolic pressure": "est_PASP_num",
            }
        }
    )

    df_numeric = df_numeric.drop(
        columns=["finding_type", "finding_name", "string_value", "unit"]
    )

    df_numeric_pivot = df_numeric.pivot_table(
        index=[
            "patient_durable_key",
            "surgical_case_key",
            "imaging_key",
            "echo_start_date",
            "echo_finalised_date",
            "planned_operation_start_instant",
        ],
        values="numeric_value",
        columns="finding",
    )

    df_numeric_pivot.reset_index(inplace=True)
    df_numeric_pivot.columns.name = None

    num_col_names = [
        "TAPSE_num",
        "EF_est_num",
        "EF_mbp_num",
        "PASP_num",
        "est_PASP_num",
    ]

    for col in num_col_names:
        if col not in list(df_numeric_pivot.columns):
            df_numeric_pivot[col] = np.nan

    # rename categorical values and pivot table
    df_cat = df_cat.replace(
        {
            "finding": {
                "Aortic Valve regurgitation severity": "AVR",
                "Aortic Valve stenosis": "AVS",
                "Left Ventricle left ventricular cavity size": "LV_size_cat",
                "Left Ventricle diastolic filling": "LV_diast_fill_cat",
                "Left Ventricle ejection fraction": "LVEF_cat",
                "Left Ventricle impaired": "LV_imp_cat",
                "Mitral Valve regurgitation severity": "MVR",
                "Mitral Valve stenosis severity": "MVS",
                "Pulmonary Hypertension moderate": "PH_mod_cat",
                "Pulmonary Hypertension severe": "PH_sev_cat",
                "Pulmonic Valve regurgitation severity": "PVR",
                "Pulmonic Valve stenosis severity": "PVS",
                "Right Ventricle cavity size": "RV_size_cat",
                "Right Ventricle global systolic function": "RV_func_cat",
                "Tricuspid Valve regurgitation severity": "TVR",
                "Tricuspid Valve stenosis severity": "TVS",
                "Pulmonary Hypertension Probability\
                     of pulmonary hypertension": "PH_prob_cat",
            }
        }
    )

    df_cat = df_cat.drop(
        columns=["finding_type", "finding_name", "numeric_value", "unit"]
    )

    df_cat_pivot = df_cat.pivot_table(
        index=[
            "patient_durable_key",
            "surgical_case_key",
            "imaging_key",
            "echo_start_date",
            "echo_finalised_date",
            "planned_operation_start_instant",
        ],
        values="string_value",
        columns="finding",
        aggfunc=lambda x: " ".join(x),
    )

    df_cat_pivot.reset_index(inplace=True)
    df_cat_pivot.columns.name = None

    cat_col_names = [
        "AVR",
        "AVS",
        "LV_size_cat",
        "LV_diast_fill_cat",
        "LVEF_cat",
        "LV_imp_cat",
        "MVR",
        "MVS",
        "PH_mod_cat",
        "PH_sev_cat",
        "PVR",
        "PVS",
        "RV_size_cat",
        "RV_func_cat",
        "TVR",
        "TVS",
        "PH_prob_cat",
    ]

    for col in cat_col_names:
        if col not in list(df_cat_pivot.columns):
            df_cat_pivot[col] = np.nan

    # merge sets of features together, one row for each echo performed

    df_cases = df[
        [
            "patient_durable_key",
            "surgical_case_key",
            "imaging_key",
            "echo_start_date",
            "echo_finalised_date",
            "planned_operation_start_instant",
        ]
    ].drop_duplicates()

    df_results = df_cases.merge(
        df_cat_pivot,
        on=[
            "patient_durable_key",
            "surgical_case_key",
            "imaging_key",
            "echo_start_date",
            "echo_finalised_date",
            "planned_operation_start_instant",
        ],
        how="left",
    )

    df_results = df_results.merge(
        df_numeric_pivot,
        on=[
            "patient_durable_key",
            "surgical_case_key",
            "imaging_key",
            "echo_start_date",
            "echo_finalised_date",
            "planned_operation_start_instant",
        ],
        how="left",
    )

    string_cols_to_join = [
        "lv_string_value",
        "lv_string_value_2",
        "PH_string_value",
        "pulm_HTN_string_bin",
        "pulm_HTN_string_moderate",
        "pulm_HTN_string_severe",
    ]

    for col in string_cols_to_join:
        cols = [
            "patient_durable_key",
            "surgical_case_key",
            "imaging_key",
            "echo_start_date",
            "echo_finalised_date",
            "planned_operation_start_instant",
        ] + [col]

        to_join = df_string[cols]

        to_join = to_join.drop_duplicates()
        to_join = to_join[~to_join[col].isna()]

        df_results = df_results.merge(
            to_join,
            on=[
                "patient_durable_key",
                "surgical_case_key",
                "imaging_key",
                "echo_start_date",
                "echo_finalised_date",
                "planned_operation_start_instant",
            ],
            how="left",
        )

    # create categories based on abnormal values
    # Note here cutoffs for moderately abnormal are used to flag an abnormal value
    # - mildly abnormal is not flagged

    df_results["valve_abnormal"] = np.where(
        (df_results["AVR"] == "severe")
        | (df_results["AVR"] == "critical")
        | (df_results["AVR"] == "moderate-to-severe")
        | (df_results["AVS"] == "severe")
        | (df_results["AVS"] == "critical")
        | (df_results["AVS"] == "moderate-to-severe")
        | (df_results["MVR"] == "severe")
        | (df_results["MVR"] == "critical")
        | (df_results["MVR"] == "moderate-to-severe")
        | (df_results["MVS"] == "severe")
        | (df_results["MVS"] == "critical")
        | (df_results["MVS"] == "moderate-to-severe")
        | (df_results["PVR"] == "severe")
        | (df_results["PVR"] == "critical")
        | (df_results["PVR"] == "moderate-to-severe")
        | (df_results["PVS"] == "severe")
        | (df_results["PVS"] == "critical")
        | (df_results["PVS"] == "moderate-to-severe")
        | (df_results["TVR"] == "severe")
        | (df_results["TVR"] == "critical")
        | (df_results["TVR"] == "moderate-to-severe")
        | (df_results["TVS"] == "severe")
        | (df_results["TVS"] == "critical")
        | (df_results["TVS"] == "moderate-to-severe"),
        1,
        0,
    )
    df_results["lv_function_abnormal"] = np.where(
        (df_results["EF_est_num"] <= 30)
        | (df_results["EF_mbp_num"] <= 30)
        | (df_results["lv_string_value"] <= 30)
        | (df_results["lv_string_value_2"] <= 30)
        | (df_results["LVEF_cat"] == "decreased")
        | (df_results["LV_diast_fill_cat"] == "abnormal")
        | (df_results["LV_imp_cat"] == "1")
        | (df_results["LV_size_cat"] == "severe"),
        1,
        0,
    )

    df_results["rv_function_abnormal"] = np.where(
        (df_results["RV_func_cat"] == "severely reduced")
        | (df_results["RV_size_cat"] == "severely enlarged")
        | (df_results["TAPSE_num"] <= 1.7),
        1,
        0,
    )

    df_results["pulm_htn"] = np.where(
        (df_results["PH_prob_cat"] == "intermediate")
        | (df_results["PH_sev_cat"] == "1")
        | (df_results["PH_string_value"] > 60)
        | (df_results["PASP_num"] > 60)
        | (df_results["est_PASP_num"] > 60)
        | (df_results["pulm_HTN_string_bin"] == 1)
        | (df_results["pulm_HTN_string_severe"] == 1),
        1,
        0,
    )

    # create variables for echo performed and echo abnormal
    df_results["echo_performed"] = 1
    df_results["echo_abnormal"] = np.where(
        (df_results["valve_abnormal"] == 1)
        | (df_results["lv_function_abnormal"] == 1)
        | (df_results["rv_function_abnormal"] == 1)
        | (df_results["pulm_htn"] == 1),
        1,
        0,
    )

    # select only engineered features
    df_results = df_results[
        [
            "patient_durable_key",
            "surgical_case_key",
            "imaging_key",
            "echo_start_date",
            "echo_finalised_date",
            "planned_operation_start_instant",
            "valve_abnormal",
            "lv_function_abnormal",
            "rv_function_abnormal",
            "pulm_htn",
            "echo_performed",
            "echo_abnormal",
        ]
    ]

    # select only most recent echo per surgical case and return this

    df_last_echo = (
        df_results.sort_values("echo_finalised_date")
        .groupby(
            [
                "patient_durable_key",
                "surgical_case_key",
                "planned_operation_start_instant",
            ]
        )
        .tail(1)
    )

    df_last_echo = df_last_echo[
        [
            "surgical_case_key",
            "planned_operation_start_instant",
            "valve_abnormal",
            "lv_function_abnormal",
            "rv_function_abnormal",
            "pulm_htn",
            "echo_performed",
            "echo_abnormal",
        ]
    ]

    return df_last_echo


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


def generate_icu_binary_from_emap(
    data: pd.DataFrame,  # consider adding more locations here if appropriate.
    old: bool = False,
) -> pd.DataFrame:
    # generate_all_theatres_flag
    print("generate_all_theatres_flag")

    covdate = datetime(2020, 6, 1, tzinfo=timezone.utc)

    conds = [
        (data["name"] == "UCH P03 THEATRE SUITE"),
        (data["name"] == "WMS W01 THEATRE SUITE"),
        (data["name"] == "GWB B-1 THEATRE SUITE"),
        (
            (data["name"] == "UCH T02 DAY SURG THR")
            & (data["admission_time"] >= covdate)
        ),
    ]
    data["main_theatre"] = np.select(conds, ["Yes"] * 4, default="No")

    condis = [
        (data["name"] == "UCH P03 THEATRE SUITE") & (data["admission_time"] <= covdate),
        (data["name"] == "UCH P03 THEATRE SUITE") & (data["admission_time"] >= covdate),
        (data["name"] == "UCH T02 DAY SURG THR") & (data["admission_time"] >= covdate),
        (data["name"] == "WMS W01 THEATRE SUITE"),
        (data["name"] == "GWB B-1 THEATRE SUITE"),
    ]
    choices = [
        "T03 Pre COVID Theatre",
        "T02 Green Theatre",
        "T03 Blue Theatre",
        "Westmoreland Street",
        "Grafton Way",
    ]
    data["main_theatre_cat"] = np.select(condis, choices, default="Not Theatre")

    # generate_time_features
    data.loc[:, "duration_hours"] = data.loc[:, "duration"] / pd.to_timedelta(
        1, unit="H"
    )

    data.loc[:, "duration_hours"] = np.where(
        np.logical_and(
            data.loc[:, "duration_hours"] > 24,
            data.loc[:, "main_theatre"] == "Yes",
        ),
        24,
        data.loc[:, "duration_hours"],
    )
    data.loc[:, "duration_hours"] = np.where(
        np.logical_and(
            data.loc[:, "duration_hours"] < 0.3,
            data.loc[:, "main_theatre"] == "Yes",
        ),
        0.3,
        data.loc[:, "duration_hours"],
    )

    data.loc[:, "adm_datetime_dt64"] = pd.to_datetime(
        data.loc[:, "admission_time"], utc=True
    ) + pd.to_timedelta(1, unit="H")
    data.loc[:, "disch_datetime_dt64"] = pd.to_datetime(
        data.loc[:, "discharge_time"], utc=True
    ) + pd.to_timedelta(1, unit="H")
    data.loc[:, "adm_date"] = data.loc[:, "adm_datetime_dt64"].apply(datetime.date)

    data.loc[:, "adm_day"] = data.loc[:, "adm_datetime_dt64"].apply(datetime.weekday)
    data.loc[:, "adm_month"] = pd.DatetimeIndex(data.loc[:, "adm_datetime_dt64"]).month

    lockdown_1_start = datetime(2020, 3, 23, tzinfo=timezone.utc)
    lockdown_1_end = datetime(2020, 6, 23, tzinfo=timezone.utc)

    lockdown_2_start = datetime(2021, 1, 6, tzinfo=timezone.utc)
    lockdown_2_end = datetime(2021, 4, 12, tzinfo=timezone.utc)

    conditions_lockdown = [
        (data["admission_time"] < lockdown_1_start),
        (data["admission_time"] > lockdown_1_start)
        & (data["admission_time"] < lockdown_1_end),
        (data["admission_time"] > lockdown_1_end)
        & (data["admission_time"] < lockdown_2_start),
        (data["admission_time"] > lockdown_2_start)
        & (data["admission_time"] < lockdown_2_end),
        (data["admission_time"] > lockdown_2_end),
    ]

    values_lockdown = ("precovid", "surge1", "nosurge", "surge2", "nosurge")
    data.loc[:, "covid_period"] = np.select(conditions_lockdown, values_lockdown)

    # prev_and_next_wards
    print("prev_and_next_wards")

    if old:
        data = (
            data.sort_values("admission_time")
            .groupby("hospital_visit_id")
            .apply(lambda x: x.assign(prev_ward=lambda x: x["name"].shift(1)))
        )
        data = (
            data.sort_values("admission_time")
            .groupby("hospital_visit_id")
            .apply(lambda x: x.assign(next_ward=lambda x: x["name"].shift(-1)))
        )
        data = (
            data.sort_values("admission_time")
            .groupby("hospital_visit_id")
            .apply(lambda x: x.assign(prev_ward2=lambda x: x["name"].shift(2)))
        )
        data = (
            data.sort_values("admission_time")
            .groupby("hospital_visit_id")
            .apply(
                lambda x: x.assign(
                    ward_after_theatre_duration_hours=lambda x: np.where(
                        x["main_theatre"] == "Yes",
                        x["duration_hours"].shift(-1),
                        pd.NaT,
                    )
                )
            )
        )
    else:
        data = data.sort_values(["admission_time", "discharge_time"])
        data["prev_ward"] = data.groupby(["hospital_visit_id"])["name"].shift(1)
        data["next_ward"] = data.groupby(["hospital_visit_id"])["name"].shift(-1)
        data["prev_ward2"] = data.groupby(["hospital_visit_id"])["name"].shift(2)
        data["ward_after_theatre_duration_hours"] = data.groupby("hospital_visit_id")[
            "duration_hours"
        ].shift(-1)
        data.loc[
            data["main_theatre"] == "No", "ward_after_theatre_duration_hours"
        ] = pd.NaT

    # filter out patients for whom there is no discharge time

    data = data[
        (data.loc[:, "main_theatre"] == "Yes") & (~data.loc[:, "discharge_time"].isna())
    ]

    # generate_icu_pacu_label
    print("generate_icu_pacu_label")

    ward_cols = ["prev_ward", "next_ward"]
    for ward in ward_cols:
        conditions_pacu = [
            data[ward] == "UCH T03 INTENSIVE CARE",
            data[ward] == "WMS W01 CRITICAL CARE",
            data[ward] == "GWB L01 CRITICAL CARE",
            (
                data["admission_time"]
                >= datetime(2020, 11, 30, 0, 0, 1, tzinfo=timezone.utc)
            )
            & (
                data["admission_time"]
                <= datetime(2020, 12, 20, 23, 59, 59, tzinfo=timezone.utc)
            )
            & (data[ward] == "UCH T07 SOUTH (T07S)"),
            (
                data["admission_time"]
                >= datetime(2021, 4, 19, 0, 0, 1, tzinfo=timezone.utc)
            )
            & (
                data["admission_time"]
                <= datetime(2021, 5, 30, 23, 59, 59, tzinfo=timezone.utc)
            )
            & (data[ward] == "UCH T07 SOUTH (T07S)"),
            (
                data["admission_time"]
                >= datetime(2020, 11, 30, 0, 0, 1, tzinfo=timezone.utc)
            )
            & (
                data["admission_time"]
                <= datetime(2020, 12, 20, 23, 59, 59, tzinfo=timezone.utc)
            )
            & (data[ward] == "UCH T07 SOUTH"),
            (
                data["admission_time"]
                >= datetime(2021, 4, 19, 0, 0, 1, tzinfo=timezone.utc)
            )
            & (
                data["admission_time"]
                <= datetime(2021, 5, 30, 23, 59, 59, tzinfo=timezone.utc)
            )
            & (data[ward] == "UCH T07 SOUTH"),
            (
                data["admission_time"]
                >= datetime(2021, 5, 31, 0, 0, 1, tzinfo=timezone.utc)
            )
            & (
                data["admission_time"]
                <= datetime(2021, 7, 19, 23, 59, 59, tzinfo=timezone.utc)
            )
            & (data[ward] == "UCH T06 SOUTH PACU"),
        ]

        values_pacu = ["ICU/PACU"] * 8

        data.loc[:, "ICU_PACU_" + ward] = np.select(conditions_pacu, values_pacu)
        data.loc[:, "ICU_PACU_" + ward] = data.loc[:, "ICU_PACU_" + ward].replace(
            {"0": "Not ICU/PACU"}
        )

    if old:
        lambda x: x.assign(
            icu_pacu_duration_hours=lambda x: np.where(
                np.logical_and(
                    x["main_theatre"] == "Yes",
                    x["ICU_PACU_next_ward"] == "ICU/PACU",
                ),
                x["ward_after_theatre_duration_hours"],
                pd.NaT,
            )
        )

    else:
        data["icu_pacu_duration_hours"] = data["ward_after_theatre_duration_hours"]
        data.loc[data["main_theatre"] == "No", "icu_pacu_duration_hours"] = pd.NaT
        data.loc[
            data["ICU_PACU_next_ward"] == "Not ICU/PACU",
            "icu_pacu_duration_hours",
        ] = pd.NaT

    # merge_split_theatre_visits
    print("merge_split_theatre_visits")

    counts_visit_date = (
        data.groupby(["hospital_visit_id", "adm_date", "location_id"])
        .size()
        .reset_index()
        .rename(columns={0: "count"})
    )

    duplicates = counts_visit_date[counts_visit_date["count"] > 1]

    theatre_data_single = data[
        ~data["hospital_visit_id"].isin(duplicates["hospital_visit_id"])
    ]

    dupes = data[data["hospital_visit_id"].isin(duplicates["hospital_visit_id"])]

    dupes = (
        dupes.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])
        .apply(
            lambda x: x.assign(prev_adm_time=lambda x: x["adm_datetime_dt64"].shift(1))
        )
    )

    dupes = (
        dupes.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])
        .apply(
            lambda x: x.assign(
                prev_disch_time=lambda x: x["disch_datetime_dt64"].shift(1)
            )
        )
    )

    dupes = (
        dupes.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])
        .apply(
            lambda x: x.assign(next_adm_time=lambda x: x["adm_datetime_dt64"].shift(-1))
        )
    )

    dupes = (
        dupes.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])
        .apply(
            lambda x: x.assign(
                next_disch_time=lambda x: x["disch_datetime_dt64"].shift(-1)
            )
        )
    )

    dupes["since_prev_discharge"] = (
        dupes["adm_datetime_dt64"] - dupes["prev_disch_time"]
    ) / pd.to_timedelta(1, unit="m")

    dupes["to_next_admission"] = (
        dupes["next_adm_time"] - dupes["disch_datetime_dt64"]
    ) / pd.to_timedelta(1, unit="m")

    dupes["to_merge"] = np.where(
        ((dupes["since_prev_discharge"] < 15) | (dupes["to_next_admission"] < 15)),
        1,
        0,
    )

    dupes_not_merged = dupes[dupes["to_merge"] == 0]
    dupes_to_merge = dupes[dupes["to_merge"] == 1]

    dupes_to_merge = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])
        .apply(lambda x: x.assign(min_adm_dt64=lambda x: x["adm_datetime_dt64"].min()))
    )

    dupes_to_merge["min_adm_time"] = dupes_to_merge["min_adm_dt64"].astype(str)

    # get latest admission time for group
    dupes_to_merge = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])
        .apply(
            lambda x: x.assign(max_disch_dt64=lambda x: x["disch_datetime_dt64"].max())
        )
    )

    dupes_to_merge["max_disch_time"] = dupes_to_merge["max_disch_dt64"].astype(str)

    # get lv_id corresponding to longest admission
    dupes_to_merge["longest_adm"] = dupes_to_merge.index.isin(
        dupes_to_merge.groupby(["hospital_visit_id", "adm_date", "location_id"])[
            "duration_hours"
        ].idxmax()
    ).astype(int)

    dupes_to_merge = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])
        .apply(
            lambda x: x.assign(
                lv_id_longest_adm=lambda x: x.loc[
                    x["longest_adm"] == 1, ["location_visit_id"]
                ]
            )
        )
    )

    dupes_to_merge["lv_id_longest_adm"] = dupes_to_merge["lv_id_longest_adm"].fillna(
        dupes_to_merge.groupby(["hospital_visit_id", "adm_date", "location_id"])[
            "lv_id_longest_adm"
        ].transform("max")
    )

    # get prev and next admissions for groups
    # recreate same columns from original df

    dupes_to_merge["prev_ward_group"] = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])["prev_ward"]
        .transform("first")
    )

    dupes_to_merge["next_ward_group"] = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])["next_ward"]
        .transform("last")
    )

    dupes_to_merge["next_ward_duration_group"] = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])[
            "ward_after_theatre_duration_hours"
        ]
        .transform("last")
    )

    dupes_to_merge["prev_ward_2_group"] = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])["prev_ward2"]
        .transform("first")
    )

    dupes_to_merge["ICU_PACU_prev_ward_group"] = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])["ICU_PACU_prev_ward"]
        .transform("first")
    )

    dupes_to_merge["ICU_PACU_next_ward_group"] = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])["ICU_PACU_next_ward"]
        .transform("last")
    )

    dupes_to_merge["icu_pacu_duration_hours_group"] = (
        dupes_to_merge.sort_values("admission_time")
        .groupby(["hospital_visit_id", "adm_date", "location_id"])[
            "icu_pacu_duration_hours"
        ]
        .transform("last")
    )

    # ICU_PACU_next_ward
    # icu_pacu_duration_hours

    dupes_to_merge = dupes_to_merge.drop(
        columns=[
            "admission_time",
            "discharge_time",
            "adm_datetime_dt64",
            "disch_datetime_dt64",
            "duration",
            "duration_hours",
            "prev_ward",
            "prev_ward2",
            "next_ward",
            "ICU_PACU_prev_ward",
            "ICU_PACU_next_ward",
            "icu_pacu_duration_hours",
            "location_visit_id",
            "prev_adm_time",
            "prev_disch_time",
            "next_adm_time",
            "next_disch_time",
            "ward_after_theatre_duration_hours",
            "since_prev_discharge",
            "to_next_admission",
            "to_merge",
            "longest_adm",
        ]
    )

    dupes_merged = dupes_to_merge.drop_duplicates()

    dupes_merged.loc[:, "max_disch_time"] = pd.to_datetime(
        dupes_merged.loc[:, "max_disch_time"], utc=True
    )
    dupes_merged.loc[:, "min_adm_time"] = pd.to_datetime(
        dupes_merged.loc[:, "min_adm_time"], utc=True
    )

    dupes_merged.loc[:, "duration"] = (
        dupes_merged.loc[:, "max_disch_time"] - dupes_merged.loc[:, "min_adm_time"]
    )
    dupes_merged.loc[:, "duration_hours"] = dupes_merged.loc[
        :, "duration"
    ] / pd.to_timedelta(1, unit="H")

    name_dict = {
        "min_adm_dt64": "adm_datetime_dt64",
        "max_disch_dt64": "disch_datetime_dt64",
        "min_adm_time": "admission_time",
        "max_disch_time": "discharge_time",
        "prev_ward_group": "prev_ward",
        "next_ward_group": "next_ward",
        "prev_ward_2_group": "prev_ward2",
        "lv_id_longest_adm": "location_visit_id",
        "next_ward_duration_group": "ward_after_theatre_duration_hours",
        "ICU_PACU_next_ward_group": "ICU_PACU_next_ward",
        "ICU_PACU_prev_ward_group": "ICU_PACU_prev_ward",
        "icu_pacu_duration_hours_group": "icu_pacu_duration_hours",
    }

    dupes_merged.rename(columns=name_dict, inplace=True)

    dupes_not_merged = dupes_not_merged.drop(
        columns=[
            "prev_adm_time",
            "prev_disch_time",
            "next_adm_time",
            "next_disch_time",
            "since_prev_discharge",
            "to_next_admission",
            "to_merge",
        ]
    )

    data = pd.concat(
        [theatre_data_single, dupes_not_merged, dupes_merged],
        ignore_index=True,
    )

    # clean_wards_for_theatre_data
    print("clean_wards_for_theatre_data")

    data.loc[:, "prev_ward_clean"] = data.loc[:, "prev_ward"]

    data.loc[
        (data["prev_ward"].isna()) & (data["prev_ward2"].notna()),
        "prev_ward_clean",
    ] = data.loc[:, "prev_ward2"]

    data.loc[
        (data["prev_ward"] == "UCH P03 THEATRE SUITE")
        & (data["name"] == "UCH P03 THEATRE SUITE")
        & (data["prev_ward2"].notna()),
        "prev_ward_clean",
    ] = data.loc[:, "prev_ward2"]

    data.loc[
        (data["prev_ward"] == "UCH T02 DAY SURG THR")
        & (data["name"] == "UCH T02 DAY SURG THR")
        & (data["prev_ward2"].notna()),
        "prev_ward_clean",
    ] = data.loc[:, "prev_ward2"]

    data.loc[
        (data["prev_ward"] == "GWB B-1 THEATRE SUITE")
        & (data["name"] == "GWB B-1 THEATRE SUITE")
        & (data["prev_ward2"].notna()),
        "prev_ward_clean",
    ] = data.loc[:, "prev_ward2"]

    data.loc[
        (data["prev_ward"] == "WMS W01 THEATRE SUITE")
        & (data["name"] == "WMS W01 THEATRE SUITE")
        & (data["prev_ward2"].notna()),
        "prev_ward_clean",
    ] = data.loc[:, "prev_ward2"]

    data.loc[:, "prev_ward_clean"] = data.loc[:, "prev_ward_clean"].fillna("HOME")
    data.loc[:, "prev_location"] = np.where(
        data.loc[:, "prev_ward_clean"] == "HOME", "HOME", "HOSPITAL"
    )

    # generate ICU binary
    print("generating ICU binary")
    data.loc[:, "ICU_binary"] = np.where(
        data.loc[:, "ICU_PACU_next_ward"] == "ICU/PACU", 1, 0
    )

    return data


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
