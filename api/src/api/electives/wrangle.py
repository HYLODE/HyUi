from typing import Dict, List

import numpy as np
import pandas as pd
from api.convert import parse_to_data_frame

from models.electives import (
    ElectiveRow,
    ElectivePostOpDestinationRow,
    ElectivePreassessRow,
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
    electives_df = parse_to_data_frame(electives, ElectiveRow)
    preassess_df = parse_to_data_frame(preassess, ElectivePreassessRow)
    pod_df = parse_to_data_frame(pod, ElectivePostOpDestinationRow)

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
