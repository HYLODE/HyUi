from typing import Dict, List

import numpy as np
import pandas as pd
from api.convert import parse_to_data_frame

from models.electives import (
    CaboodleCaseBooking,
    ClarityPostopDestination,
    CaboodlePreassessment,
    SurgData,
    PreassessData,
    LabData,
    EchoData,
    # ObsData,
)
import re


def _get_most_recent_value(label: str, preassess_data: pd.DataFrame) -> pd.DataFrame:
    """
    Gets the most recent value from pre-assessment data since this is a long EAV table

    :param      label:            The label of the attribute
    :param      preassess_data:  The preassess data
    """

    # filter name column of pre-assessment data to most recent attribute
    pod_data = preassess_data[preassess_data["name"] == label]

    idx = (
        pod_data.groupby("patient_durable_key")["creation_instant"].transform(max)
        == pod_data["creation_instant"]
    )

    data = pod_data[idx]

    return data


def process_join_preassess_data(
    electives_df: pd.DataFrame,
    preassess_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge the preassessment data with the cases
    Jen Hunter 2022-08-01

    The function above gets data for post-op destination decided at
    preassessment, ASA, and exercise tolerance (METs) based on patient
    history.

    The below code gets the most recent value of each data item individually,
    rather than getting the most recent note, because for some patients there
    are multiple notes, with different pieces of information complete. These
    pieces of information may therefore be from different preassessment
    notes.

    When merging, the creation instant of the note providing the post recent
    postop destination plan is included, as this may be relevant
    operationally, whereas the date of the creation of the note with the most
    recent ASA and METs value is less important. This merge is based on
    PatientDurableKey(unique patient identifier), rather than a surgical case
    identifier, which is not available for preassessment note data.

    preassess_data - derived from preassment query against caboodle
    """

    pod_data = _get_most_recent_value("POST-OP DESTINATION", preassess_df)
    asa_data = _get_most_recent_value(
        "WORKFLOW - ANAESTHESIA - ASA STATUS", preassess_df
    )
    mets_data = _get_most_recent_value(
        "SYMPTOMS - CARDIOVASCULAR - EXERCISE TOLERANCE", preassess_df
    )

    pod_data = pod_data[["patient_durable_key", "creation_instant", "string_value"]]
    pod_data = pod_data.rename(
        columns={
            "creation_instant": "most_recent_pod_dt",
            "string_value": "pod_preassessment",
        }
    )

    asa_data = asa_data[["patient_durable_key", "string_value"]]
    asa_data = asa_data.rename(columns={"string_value": "most_recent_asa"})

    mets_data = mets_data[["patient_durable_key", "string_value"]]
    mets_data = mets_data.rename(columns={"string_value": "most_recent_mets"})

    electives_df = electives_df.merge(pod_data, on="patient_durable_key", how="left")
    electives_df = electives_df.merge(asa_data, on="patient_durable_key", how="left")
    electives_df = electives_df.merge(mets_data, on="patient_durable_key", how="left")

    return electives_df


def prepare_electives(
    electives: List[Dict],
    pod: List[Dict],
    preassess: List[Dict],
) -> pd.DataFrame:
    """
    Prepare elective case list

    :param      electives:  list of dicts with surgical cases
    :param      pod:    list of dicts with postop destination
    :param      preassess:    list of dicts with preassessment info

    :returns:   merged dataframe
    """
    electives_df = parse_to_data_frame(electives, CaboodleCaseBooking)
    # electives_df = parse_to_data_frame(electives, SurgData)
    preassess_df = parse_to_data_frame(preassess, CaboodlePreassessment)
    pod_df = parse_to_data_frame(pod, ClarityPostopDestination)

    # join caboodle case booking to preassess case
    dfca = process_join_preassess_data(electives_df, preassess_df)

    # join on post op destinations from clarity
    df = dfca.merge(
        pod_df,
        left_on="surgical_case_epic_id",
        right_on="or_case_id",
        how="left",
    )

    # create pacu label
    df["pacu"] = False
    df["pacu"] = np.where(
        df["pod_orc"].astype(str).str.contains("PACU"), True, df["pacu"]
    )
    df["pacu"] = np.where(
        df["pod_preassessment"].astype(str).str.contains("PACU"), True, df["pacu"]
    )

    # drop cancellations
    df = df[~(df["canceled"] == 1)]

    return df


def make_UTC(df):
    for i in df.loc[:, df.columns.str.endswith("Instant")]:
        df.loc[:, i + "UTC"] = pd.to_datetime(df[i], utc=True)
    return df


def wrangle_surgical(df):
    terms_dict = {
        "Priority": {
            "Two Week Wait": "Cancer Pathway",
            "*Unspecified": "Unknown",
        },
        "PrimaryAnesthesiaType": {
            "Sedation by Anaesthetist": "Sedation",
            "Sedation by Physician Assistant (Anaesthesia)": "Sedation",
            "Sedation by Physician Assistant (Anaesthesia) ": "Sedation",
            "Sedation by Endoscopist": "Sedation",
            "*Unspecified": "Unknown",
        },
        "PrimaryService": {
            "Special Needs Dental": "Other",
            "Paediatric Surgery": "Other",
            "Thoracic Medicine": "Other",
            "Paediatric Oncology": "Other",
            "Interventional Radiology": "Other",
            "Emergency Surgery": "Other",
        },
        "PostOperativeDestination": {
            "Paediatric Ward": "Other",
            "Overnight Recovery": "Other",
            "*Unspecified": "Other",
            "Endoscopy Ward": "Other",
            "*Not Applicable": "Other",
            "NICU": "Other",
        },
    }

    df.pipe(make_UTC).replace(terms_dict)

    df = df[
        (df["TouchTimeStartInstant"].isna() & df["TouchTimeEndInstant"].isna())
        | (~df["TouchTimeStartInstant"].isna() & ~df["TouchTimeEndInstant"].isna())
    ]

    # df["PlannedOperationEndInstant"]
    # = pd.to_datetime(df["PlannedOperationEndInstant"])
    # df["PlannedOperationStartInstant"] = pd.to_datetime(
    #     df["PlannedOperationStartInstant"]
    # )

    # df["SurgeryDate"] = pd.to_datetime(df["SurgeryDate"])

    df.loc[:, "op_duration_minutes"] = (
        df.loc[:, "PlannedOperationEndInstant"]
        - df.loc[:, "PlannedOperationStartInstant"]
    ).astype("timedelta64[m]")

    # df.drop(["FirstName", "LastName", "BirthDate"], axis=1, inplace=True)

    return df


def wrangle_preassess(df):
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
        df[c] = df[df["Name"].str.contains(categories[c])]["StringValue"]

    df.replace(categories_dicts, inplace=True)

    df.loc[:, list(categories.keys())] = df[list(categories.keys())].replace("No", 0)
    df.loc[:, list(categories.keys())] = df[list(categories.keys())].replace("Yes", 1)
    df.loc[~df["a_line"].isna(), "a_line"] = 1
    df.loc[~df["c_line"].isna(), "c_line"] = 1

    df.loc[:, ["a_line", "c_line", "expected_stay", "asa"]] = df[
        ["a_line", "c_line", "expected_stay", "asa"]
    ].astype("float", errors="ignore")

    # df["CreationInstant"] = pd.to_datetime(df["CreationInstant"])

    note_nums = (
        df.groupby(["PatientDurableKey", "CreationInstant", "AuthorType"])
        .agg("sum", numeric_only=True)
        .reset_index()
    )

    note_nums["a_line"] = note_nums["a_line"].astype(bool).astype(int)
    note_nums["c_line"] = note_nums["a_line"].astype(bool).astype(int)

    note_strings = (
        df.groupby(["PatientDurableKey", "CreationInstant", "AuthorType"])
        .first()[["urgency", "pacdest", "prioritisation"]]
        .reset_index()
    )
    all_notes = note_nums.merge(
        note_strings, on=["PatientDurableKey", "CreationInstant"]
    )
    all_notes["preassess_date"] = all_notes["CreationInstant"].dt.date

    return all_notes


def merge_surg_preassess(surg_data, preassess_data):
    data_surg = wrangle_surgical(surg_data)

    data_preassess = wrangle_preassess(preassess_data)

    linked_notes = data_surg.merge(
        data_preassess, on="PatientDurableKey", how="inner"
    ).query("SurgeryDate >= preassess_date")

    merged_df = linked_notes[
        linked_notes["CreationInstant"]
        == linked_notes.groupby(["PatientDurableKey", "SurgeryDate"])[
            "CreationInstant"
        ].transform(max)
    ]
    return merged_df


def wrangle_labs(df):
    # this takes some particular lab results from 4 months prior to the operation.

    labs_limits = {
        "CREA": (49, 112),
        "HB": (115, 170),
        "WCC": (3, 10),
        "PLT": (150, 400),
        "NA": (135, 145),
        "ALB": (34, 50),
        "CRP": (0, 5),
        "BILI": (0, 20),
        "INR": (0.8, 1.3),
    }
    lab_names = {
        "NA": "Sodium",
        "CREA": "Creatinine",
        "WCC": "White cell count",
        "HB": "Haemoglobin (g/L)",
        "PLT": "Platelet count",
        "ALB": "Albumin",
        "BILI": "Bilirubin (total)",
        "INR": "INR",
        "CRP": "C-reactive protein",
    }

    op_dict = {
        "mean": "_mean_value",
        "min": "_min_value",
        "max": "_max_value",
        "count": "_measured_count",
    }

    # df.loc[:, "Value"] = pd.to_numeric(
    #     df["Value"].str.replace("<|(result checked)", "", regex=True),
    #     errors="coerce",
    # .dropna() ## TOFIX why doesn't this work?
    df["Name"] = df["Name"].replace({v: k for k, v in lab_names.items()})
    df = df.join(df.pivot(columns="Name", values="Value"))

    for key in lab_names:
        df[key + "_abnormal_count"] = df[key].groupby(
            df["PatientDurableKey"]
        ).transform(lambda x: x > labs_limits[key][1]) | df[key].groupby(
            df["PatientDurableKey"]
        ).transform(
            lambda x: x < labs_limits[key][0]
        )

        for op in op_dict:
            df[key + op_dict[op]] = (
                df[key].groupby(df["PatientDurableKey"]).transform(op)
            )
    gdf = df.groupby("PatientDurableKey").sum(numeric_only=True)
    gdf = gdf.loc[:, gdf.columns.str.contains("_abnormal")]

    hdf = df.groupby("PatientDurableKey").mean(numeric_only=True)
    hdf = hdf.loc[:, hdf.columns.str.contains("_m")]

    idf = df.sort_values("ResultInstant").groupby("PatientDurableKey").last()
    idf = idf.loc[:, list(lab_names.keys())]

    final_df = gdf.join(hdf).join(idf.add_suffix("_last_value")).reset_index()

    return final_df


def simple_sum(df):
    surg_columns = []
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
    lab_names = ["NA", "CREA", "WCC", "HB", "PLT", "ALB", "BILI", "INR", "CRP"]
    lab_columns = [ln + "_abnormal_count" for ln in lab_names]
    columns_to_sum = surg_columns + preassess_columns + lab_columns
    df["simple_score"] = (
        df[columns_to_sum].replace(np.nan, 0).astype("bool").sum(axis=1)
    )
    return df


def j_wrangle_echo(df):
    df["Finding"] = df["FindingType"] + " " + df["FindingName"]

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
    df_numeric = df[df["Finding"].isin(findings_numerical)]
    df_string = df[df["Finding"].isin(findings_string)]
    df_cat = df[df["Finding"].isin(findings_categorical)]

    # extract EF values from LV comments strings
    df_string.loc[:, "LV_string_value"] = df_string.loc[
        df_string["Finding"] == "Left Ventricle Comment", "StringValue"
    ].apply(lambda x: re.findall(r"\d*[%]", x))
    df_string.loc[:, "LV_string_value"] = df_string.loc[:, "LV_string_value"].apply(
        lambda d: d if isinstance(d, list) else []
    )
    df_string.loc[:, "LV_string_value"] = df_string.loc[:, "LV_string_value"].str[0]
    df_string.loc[
        ~df_string["LV_string_value"].isna(), "LV_string_value"
    ] = df_string.loc[~df_string["LV_string_value"].isna(), "LV_string_value"].apply(
        lambda x: x.replace("%", "")
    )
    df_string.loc[:, "LV_string_value"] = (
        df_string.loc[:, "LV_string_value"]
        .replace(r"^\s*$", np.nan, regex=True)
        .apply(float)
    )
    df_string.loc[
        ~df_string["LV_string_value"].isna(), "LV_string_value"
    ] = df_string.loc[~df_string["LV_string_value"].isna(), "LV_string_value"].apply(
        lambda x: float(x)
    )

    # extract EF values from LVEF comments strings
    df_string.loc[:, "LV_string_value_2"] = df_string.loc[
        df_string["Finding"] == "Left Ventricle ejection fraction comments",
        "StringValue",
    ].apply(lambda x: re.findall(r"\d*[%]", x))
    df_string.loc[:, "LV_string_value_2"] = df_string.loc[:, "LV_string_value_2"].apply(
        lambda d: d if isinstance(d, list) else []
    )
    df_string.loc[:, "LV_string_value_2"] = df_string.loc[:, "LV_string_value_2"].str[0]
    df_string.loc[
        ~df_string["LV_string_value_2"].isna(), "LV_string_value_2"
    ] = df_string.loc[
        ~df_string["LV_string_value_2"].isna(), "LV_string_value_2"
    ].apply(
        lambda x: x.replace("%", "")
    )
    df_string.loc[:, "LV_string_value_2"] = (
        df_string.loc[:, "LV_string_value_2"]
        .replace(r"^\s*$", np.nan, regex=True)
        .apply(float)
    )
    df_string.loc[
        ~df_string["LV_string_value_2"].isna(), "LV_string_value_2"
    ] = df_string.loc[
        ~df_string["LV_string_value_2"].isna(), "LV_string_value_2"
    ].apply(
        lambda x: float(x)
    )

    # Extract PASP strings from PH comments
    df_string.loc[:, "contains PASP value"] = df_string.loc[
        df_string["Finding"] == "Pulmonary Hypertension pulmonary hypertension",
        "StringValue",
    ].apply(lambda x: np.where(("PASP" in x) | ("systolic pressure" in x), 1, 0))
    df_string.loc[:, "PH_string_value"] = df_string.loc[
        (
            (df_string["Finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["contains PASP value"] == 1)
        ),
        "StringValue",
    ].apply(lambda x: re.findall(r"\d*\.?\d+", x))
    df_string.loc[:, "PH_string_value"] = df_string.loc[
        (
            (df_string["Finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["contains PASP value"] == 1)
        ),
        "PH_string_value",
    ].apply(lambda x: [float(i) for i in x])

    def get_first_above_8(list_of_nos):
        item = next((x for x in list_of_nos if ((x > 8) & (x < 80))), np.nan)
        return item

    df_string.loc[:, "PH_string_value"] = df_string.loc[
        (
            (df_string["Finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["contains PASP value"] == 1)
        ),
        "PH_string_value",
    ].apply(lambda x: get_first_above_8(x))
    df_string = df_string.drop(columns=["contains PASP value"])

    # convert selected PH comment strings to binary vars
    df_string["pulm_HTN_string_bin"] = np.where(
        (
            (df_string["Finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["StringValue"] == "1")
        ),
        1,
        np.nan,
    )
    df_string["pulm_HTN_string_moderate"] = np.where(
        (
            (df_string["Finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["StringValue"] == "moderate")
        ),
        1,
        np.nan,
    )
    df_string["pulm_HTN_string_severe"] = np.where(
        (
            (df_string["Finding"] == "Pulmonary Hypertension pulmonary hypertension")
            & (df_string["StringValue"] == "severe")
        ),
        1,
        np.nan,
    )

    # keep only features generated from string columns
    df_string = df_string.drop(
        columns=[
            "FindingType",
            "FindingName",
            "StringValue",
            "NumericValue",
            "Unit",
            "Finding",
        ]
    )

    # rename numeric values and pivot table
    df_numeric = df_numeric.replace(
        {
            "Finding": {
                "*Not Applicable RV TAPSE (TV annulus)": "TAPSE_num",
                "*Not Applicable Echo EF Estimated": "EF_est_num",
                "*Not Applicable EF (Mod BP)": "EF_mbp_num",
                "*Not Applicable PASP": "PASP_num",
                "Pulmonary Hypertension estimated PA systolic pressure": "est_PASP_num",
            }
        }
    )

    df_numeric = df_numeric.drop(
        columns=["FindingType", "FindingName", "StringValue", "Unit"]
    )

    df_numeric_pivot = df_numeric.pivot_table(
        index=[
            "PatientDurableKey",
            "SurgicalCaseKey",
            "ImagingKey",
            "EchoStartDate",
            "EchoFinalisedDate",
            "PlannedOperationStartInstant",
        ],
        values="NumericValue",
        columns="Finding",
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
            "Finding": {
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

    df_cat = df_cat.drop(columns=["FindingType", "FindingName", "NumericValue", "Unit"])

    df_cat_pivot = df_cat.pivot_table(
        index=[
            "PatientDurableKey",
            "SurgicalCaseKey",
            "ImagingKey",
            "EchoStartDate",
            "EchoFinalisedDate",
            "PlannedOperationStartInstant",
        ],
        values="StringValue",
        columns="Finding",
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
            "PatientDurableKey",
            "SurgicalCaseKey",
            "ImagingKey",
            "EchoStartDate",
            "EchoFinalisedDate",
            "PlannedOperationStartInstant",
        ]
    ].drop_duplicates()

    df_results = df_cases.merge(
        df_cat_pivot,
        on=[
            "PatientDurableKey",
            "SurgicalCaseKey",
            "ImagingKey",
            "EchoStartDate",
            "EchoFinalisedDate",
            "PlannedOperationStartInstant",
        ],
        how="left",
    )

    df_results = df_results.merge(
        df_numeric_pivot,
        on=[
            "PatientDurableKey",
            "SurgicalCaseKey",
            "ImagingKey",
            "EchoStartDate",
            "EchoFinalisedDate",
            "PlannedOperationStartInstant",
        ],
        how="left",
    )

    string_cols_to_join = [
        "LV_string_value",
        "LV_string_value_2",
        "PH_string_value",
        "pulm_HTN_string_bin",
        "pulm_HTN_string_moderate",
        "pulm_HTN_string_severe",
    ]

    for col in string_cols_to_join:
        cols = [
            "PatientDurableKey",
            "SurgicalCaseKey",
            "ImagingKey",
            "EchoStartDate",
            "EchoFinalisedDate",
            "PlannedOperationStartInstant",
        ] + [col]

        to_join = df_string[cols]

        to_join = to_join.drop_duplicates()
        to_join = to_join[~to_join[col].isna()]

        df_results = df_results.merge(
            to_join,
            on=[
                "PatientDurableKey",
                "SurgicalCaseKey",
                "ImagingKey",
                "EchoStartDate",
                "EchoFinalisedDate",
                "PlannedOperationStartInstant",
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
    df_results["LV_function_abnormal"] = np.where(
        (df_results["EF_est_num"] <= 30)
        | (df_results["EF_mbp_num"] <= 30)
        | (df_results["LV_string_value"] <= 30)
        | (df_results["LV_string_value_2"] <= 30)
        | (df_results["LVEF_cat"] == "decreased")
        | (df_results["LV_diast_fill_cat"] == "abnormal")
        | (df_results["LV_imp_cat"] == "1")
        | (df_results["LV_size_cat"] == "severe"),
        1,
        0,
    )

    df_results["RV_function_abnormal"] = np.where(
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
    df_results["EchoPerformed"] = 1
    df_results["EchoAbnormal"] = np.where(
        (df_results["valve_abnormal"] == 1)
        | (df_results["LV_function_abnormal"] == 1)
        | (df_results["RV_function_abnormal"] == 1)
        | (df_results["pulm_htn"] == 1),
        1,
        0,
    )

    # select only engineered features
    df_results = df_results[
        [
            "PatientDurableKey",
            "SurgicalCaseKey",
            "ImagingKey",
            "EchoStartDate",
            "EchoFinalisedDate",
            "PlannedOperationStartInstant",
            "valve_abnormal",
            "LV_function_abnormal",
            "RV_function_abnormal",
            "pulm_htn",
            "EchoPerformed",
            "EchoAbnormal",
        ]
    ]

    # select only most recent echo per surgical case and return this

    df_last_echo = (
        df_results.sort_values("EchoFinalisedDate")
        .groupby(
            [
                "PatientDurableKey",
                "SurgicalCaseKey",
                "PlannedOperationStartInstant",
            ]
        )
        .tail(1)
    )

    df_last_echo = df_last_echo[
        [
            "SurgicalCaseKey",
            "PlannedOperationStartInstant",
            "valve_abnormal",
            "LV_function_abnormal",
            "RV_function_abnormal",
            "pulm_htn",
            "EchoPerformed",
            "EchoAbnormal",
        ]
    ]

    return df_last_echo


def j_wrangle_obs(caboodle_obs):

    caboodle_obs.loc[:, "month_pre_theatre"] = caboodle_obs.loc[
        :, "PlannedOperationStartInstant"
    ] - pd.to_timedelta(16, unit="W")

    caboodle_obs = caboodle_obs[
        (
            caboodle_obs.loc[:, "TakenInstant"]
            < caboodle_obs.loc[:, "PlannedOperationStartInstant"]
        )
        & (
            caboodle_obs.loc[:, "FirstDocumentedInstant"]
            < caboodle_obs.loc[:, "PlannedOperationStartInstant"]
        )
        & (
            caboodle_obs.loc[:, "TakenInstant"]
            > caboodle_obs.loc[:, "month_pre_theatre"]
        )
        & (
            caboodle_obs.loc[:, "FirstDocumentedInstant"]
            > caboodle_obs.loc[:, "month_pre_theatre"]
        )
    ]

    numerical_obs_list = ["Resp", "Temp", "SpO2", "Pulse", "BMI (Calculated)"]

    text_obs_list = ["BP", "Room Air or Oxygen"]

    # Split to numerical and text obs for processing
    numerical_obs = caboodle_obs[
        caboodle_obs.loc[:, "DisplayName"].isin(numerical_obs_list)
    ]
    numerical_obs = numerical_obs[~numerical_obs["NumericValue"].isna()]

    text_obs = caboodle_obs[caboodle_obs.loc[:, "DisplayName"].isin(text_obs_list)]
    text_obs = text_obs[text_obs["Value"] != ""]

    # Process text obs
    text_obs[["SYS_BP", "DIAS_BP"]] = text_obs[text_obs.loc[:, "DisplayName"] == "BP"][
        "Value"
    ].str.split("/", 1, expand=True)

    text_obs.loc[:, "SYS_BP"].fillna(value=np.nan, inplace=True)
    text_obs.loc[:, "DIAS_BP"].fillna(value=np.nan, inplace=True)

    text_obs.loc[:, "SYS_BP"] = text_obs.loc[:, "SYS_BP"].apply(lambda x: float(x))
    text_obs.loc[:, "DIAS_BP"] = text_obs.loc[:, "DIAS_BP"].apply(lambda x: float(x))

    oxygen_conditions = [
        (text_obs.loc[:, "DisplayName"] == "Room Air or Oxygen")
        & (text_obs.loc[:, "Value"] == "Supplemental Oxygen"),
        (text_obs.loc[:, "DisplayName"] == "Room Air or Oxygen")
        & (text_obs.loc[:, "Value"] == "Room air"),
        (text_obs.loc[:, "DisplayName"] != "Room Air or Oxygen"),
    ]

    oxygen_codes = (1, 0, np.nan)

    text_obs.loc[:, "ON_OXYGEN_BIN"] = np.select(oxygen_conditions, oxygen_codes)

    text_obs = text_obs.drop(
        columns=["Value", "NumericValue", "DisplayName", "month_pre_theatre"]
    )

    bp_obs = text_obs[
        [
            "SurgicalCaseKey",
            "FirstDocumentedInstant",
            "TakenInstant",
            "PlannedOperationStartInstant",
            "SYS_BP",
            "DIAS_BP",
        ]
    ]

    bp_obs = bp_obs[~bp_obs["SYS_BP"].isna()]
    bp_obs = bp_obs.drop_duplicates()

    o2_obs = text_obs[
        [
            "SurgicalCaseKey",
            "FirstDocumentedInstant",
            "TakenInstant",
            "PlannedOperationStartInstant",
            "ON_OXYGEN_BIN",
        ]
    ]

    o2_obs = o2_obs[~o2_obs["ON_OXYGEN_BIN"].isna()]
    o2_obs = o2_obs.drop_duplicates()

    text_obs = bp_obs.merge(
        o2_obs,
        on=[
            "SurgicalCaseKey",
            "FirstDocumentedInstant",
            "TakenInstant",
            "PlannedOperationStartInstant",
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
        (numerical_obs["DisplayName"] == "SpO2"),
        (numerical_obs["DisplayName"] == "Pulse"),
        (numerical_obs["DisplayName"] == "Resp"),
        (numerical_obs["DisplayName"] == "Temp"),
        (numerical_obs["DisplayName"] == "BMI (Calculated)"),
    ]

    values_obs_codes = ("SPO2", "PULSE", "RR", "TEMP", "BMI")

    numerical_obs.loc[:, "obs_code"] = np.select(
        obs_long_names_conditions, values_obs_codes
    )

    numerical_obs = numerical_obs.drop(
        columns=["Value", "DisplayName", "month_pre_theatre"]
    )

    numerical_obs = numerical_obs.pivot_table(
        index=[
            "SurgicalCaseKey",
            "PlannedOperationStartInstant",
            "FirstDocumentedInstant",
            "TakenInstant",
        ],
        values="NumericValue",
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
            "SurgicalCaseKey",
            "FirstDocumentedInstant",
            "TakenInstant",
            "PlannedOperationStartInstant",
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
        all_obs[ob + "_abnormal_count"] = all_obs.groupby(["SurgicalCaseKey"])[
            ob + "_abnormal_flag"
        ].transform(sum)

    for ob in preadm_obs_list:
        all_obs[ob + "_measured_count"] = all_obs.groupby(["SurgicalCaseKey"])[
            ob
        ].transform("count")

    for ob in preadm_obs_list:
        all_obs[ob + "_last_value"] = (
            all_obs.sort_values("TakenInstant")
            .groupby(["SurgicalCaseKey"])[ob]
            .transform("last")
        )

    for ob in preadm_obs_list:
        all_obs[ob + "_mean_value"] = all_obs.groupby(["SurgicalCaseKey"])[
            ob
        ].transform("mean")

    for ob in preadm_obs_list:
        all_obs[ob + "_min_value"] = all_obs.groupby(["SurgicalCaseKey"])[ob].transform(
            min
        )

    for ob in preadm_obs_list:
        all_obs[ob + "_max_value"] = all_obs.groupby(["SurgicalCaseKey"])[ob].transform(
            max
        )

    all_obs["BMI_max_value"] = all_obs.groupby(["SurgicalCaseKey"])["BMI"].transform(
        max
    )

    # Drop cols not using as predictors
    cols_to_drop_obs = (
        preadm_obs_list
        + [ob + "_abnormal_flag" for ob in preadm_obs_list]
        + ["FirstDocumentedInstant", "TakenInstant", "BMI"]
    )

    obs = all_obs.drop(columns=cols_to_drop_obs).drop_duplicates()

    return obs


def j_wrangle_hx(df):
    pass


def prepare_draft(
    electives: List[Dict],
    preassess: List[Dict],
    labs: List[Dict],
    echo: List[Dict],
    obs: List[Dict],
) -> pd.DataFrame:

    electives_df = parse_to_data_frame(electives, SurgData)
    preassess_df = parse_to_data_frame(preassess, PreassessData)
    labs_df = parse_to_data_frame(labs, LabData)
    echo_df = parse_to_data_frame(echo, EchoData)
    # obs_df = parse_to_data_frame(obs, ObsData)

    df = (
        merge_surg_preassess(surg_data=electives_df, preassess_data=preassess_df)
        .merge(wrangle_labs(labs_df), how="left", on="PatientDurableKey")
        .merge(j_wrangle_echo(echo_df), how="left", on="SurgicalCaseKey")
        # .merge(j_wrangle_obs(obs_df), how="left", on="SurgicalCaseKey")
    )
    # df = electives_df
    # create pacu label
    df["pacu"] = False
    df["pacu"] = np.where(
        df["booked_destination"].astype(str).str.contains("PACU"), True, df["pacu"]
    )

    # drop cancellations
    df = df[~(df["Canceled"] == 1)]

    df = simple_sum(df)

    return df
