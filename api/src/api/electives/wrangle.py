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
)


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


def prepare_draft(
    electives: List[Dict],
    preassess: List[Dict],
    labs: List[Dict],
) -> pd.DataFrame:
    electives_df = parse_to_data_frame(electives, SurgData)
    preassess_df = parse_to_data_frame(preassess, PreassessData)
    labs_df = parse_to_data_frame(labs, LabData)

    df = merge_surg_preassess(
        surg_data=electives_df, preassess_data=preassess_df
    ).merge(wrangle_labs(labs_df), how="left", on="PatientDurableKey")
    # df = electives_df
    # create pacu label
    df["pacu"] = False
    df["pacu"] = np.where(
        df["booked_destination"].astype(str).str.contains("PACU"), True, df["pacu"]
    )

    # drop cancellations
    df = df[~(df["Canceled"] == 1)]

    return df
