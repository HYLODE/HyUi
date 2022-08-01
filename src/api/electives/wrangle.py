# src/api/electives/wrangle.py
from typing import List

import pandas as pd


def _get_most_recent_value(name, preassess_data):
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


def process_join_preassess_data(preassess_data, future_cases):
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
    asa_data.head()

    mets_data = mets_data[["PatientDurableKey", "StringValue"]]
    mets_data = mets_data.rename(columns={"StringValue": "most_recent_METs"})

    future_cases = future_cases.merge(pod_data, on="PatientDurableKey", how="left")
    future_cases = future_cases.merge(asa_data, on="PatientDurableKey", how="left")
    future_cases = future_cases.merge(mets_data, on="PatientDurableKey", how="left")

    return future_cases


def prepare_electives(dfcases: pd.DataFrame, dfpod: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare elective case list

    :param      dfcases:  dataframe with surgical cases
    :param      dfpod:    dataframe with postop destination

    :returns:   merged dataframe
    """

    # CASES JOIN TO POST OP DEST
    # --------------------------
    df = dfcases.merge(dfpod, on="SurgicalCaseKey", how="left")

    # PREASSESSMENT JOIN TO CASES
    # ---------------------------
    # future_table = process_join_preassess_data(future_preassess_data, future_data)
    # future_table = future_table.drop(
    #     columns=[
    #         "PlacedOnWaitingListDate",
    #         "DecidedToAdmitDate",
    #         "ElectiveAdmissionType",
    #         "IntendedManagement",
    #         "RemovalReason",
    #         "Status",
    #         "Subgroup",
    #         "SurgicalService",
    #         "Type",
    #         "_LastUpdatedInstant",
    #         "PatientKey",
    #         "PatientDurableKey",
    #         "PrimaryService",
    #         "Classification",
    #         "SurgeryPatientClass",
    #         "AdmissionPatientClass",
    #         "PrimaryAnesthesiaType",
    #         "ReasonNotPerformed",
    #         "Canceled",
    #         "SurgicalCaseUclhKey",
    #         "SurgicalCaseKey",
    #         "CaseScheduleStatus",
    #         "CaseCancelReason",
    #         "CaseCancelReasonCode",
    #         "CancelDate",
    #         "PlannedOperationStartInstantUTC",
    #         "PlannedOperationEndInstantUTC",
    #     ]
    # )

    return df
