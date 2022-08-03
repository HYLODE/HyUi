# src/api/electives/wrangle.py
from typing import List

import pandas as pd
import numpy as np


def _get_most_recent_value(name: str, preassess_data: pd.DataFrame) -> pd.DataFrame:
    """
    Gets the most recent value.

    :param      name:            The name
    :type       name:            { type_description }
    :param      preassess_data:  The preassess data
    :type       preassess_data:  { type_description }
    """

    pod_data = preassess_data[preassess_data["Name"] == name]

    idx = (
        pod_data.groupby("PatientDurableKey")["CreationInstant"].transform(max)
        == pod_data["CreationInstant"]
    )

    data = pod_data[idx]

    return data


def process_join_preassess_data(
    preassess_data: pd.DataFrame, future_cases: pd.DataFrame
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

    pod_data = _get_most_recent_value("POST-OP DESTINATION", preassess_data)
    asa_data = _get_most_recent_value(
        "WORKFLOW - ANAESTHESIA - ASA STATUS", preassess_data
    )
    mets_data = _get_most_recent_value(
        "SYMPTOMS - CARDIOVASCULAR - EXERCISE TOLERANCE", preassess_data
    )

    pod_data = pod_data[["PatientDurableKey", "CreationInstant", "StringValue"]]
    pod_data = pod_data.rename(
        columns={
            "CreationInstant": "most_recent_pod_dt",
            "StringValue": "pod_preassessment",
        }
    )

    asa_data = asa_data[["PatientDurableKey", "StringValue"]]
    asa_data = asa_data.rename(columns={"StringValue": "most_recent_ASA"})

    mets_data = mets_data[["PatientDurableKey", "StringValue"]]
    mets_data = mets_data.rename(columns={"StringValue": "most_recent_METs"})

    future_cases = future_cases.merge(pod_data, on="PatientDurableKey", how="left")
    future_cases = future_cases.merge(asa_data, on="PatientDurableKey", how="left")
    future_cases = future_cases.merge(mets_data, on="PatientDurableKey", how="left")

    return future_cases


def prepare_electives(
    dfcases: pd.DataFrame, dfpod: pd.DataFrame, dfpreassess: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepare elective case list

    :param      dfcases:  dataframe with surgical cases
    :param      dfpod:    dataframe with postop destination
    :param      dfpreassess:    dataframe with preassessment info

    :returns:   merged dataframe
    """

    # Prepare copies of each data frame
    # --------------------------
    dfc = dfcases.copy()
    dfp = dfpod.copy()
    # dfp.drop(['id'], axis=1, inplace=True)
    dfa = dfpreassess.copy()
    # dfa.drop(['id'], axis=1, inplace=True)

    # PREASSESSMENT JOIN TO CASES
    # ---------------------------
    # import ipdb; ipdb.set_trace()
    # drop duplicate columns to avoid suffix after merge
    dfc.drop(["most_recent_pod_dt", "pod_preassessment", "most_recent_METs", "most_recent_ASA"], axis=1, inplace=True)
    dfca = process_join_preassess_data(dfa, dfc)

    # Post-op destination from case booking (clarity) join
    # ----------------------------------------------------
    # drop duplicate columns to avoid suffix after merge
    dfca.drop(["pod_orc", "SurgeryDateClarity"], axis=1, inplace=True)
    # dfp.drop(['id'], axis=1, inplace=True)
    df = dfca.merge(dfp, left_on="SurgicalCaseEpicId", right_on="or_case_id", how="left")


    df.drop(columns=[
        "PatientKey",
        "SurgicalCaseEpicId",
        "PatientDurableKey",
        "PlacedOnWaitingListDate",
        "PatientDurableKey",
        "LastUpdatedInstant",
        "SurgicalCaseUclhKey",
        "SurgicalCaseKey",
        "CaseCancelReasonCode",
        "CaseCancelReason",
        "Name",
        "id",
        "ElectiveAdmissionType",
        "IntendedManagement",
        "RemovalReason",
        "Subgroup",
    ])

    df['pacu'] = False
    df['pacu'] = np.where(df['pod_orc'].str.contains('PACU'), True, df['pacu'])
    df['pacu'] = np.where(df['pod_preassessment'].str.contains('PACU'), True, df['pacu'])


    return df
