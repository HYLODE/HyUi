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

    pod_data = preassess_data[preassess_data["name"] == name]

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
    electives_df: pd.DataFrame,
    post_op_destinations_df: pd.DataFrame,
    preassess_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare elective case list

    :param      electives_df:  dataframe with surgical cases
    :param      post_op_destinations_df:    dataframe with postop destination
    :param      preassess_df:    dataframe with preassessment info

    :returns:   merged dataframe
    """

    # Prepare copies of each data frame
    # --------------------------
    # dfc = electives_df.copy()
    # dfp = post_op_destinations_df.copy()
    # # dfp.drop(['id'], axis=1, inplace=True)
    # dfa = preassess_df.copy()
    # dfa.drop(['id'], axis=1, inplace=True)

    # PREASSESSMENT JOIN TO CASES
    # ---------------------------
    # import ipdb; ipdb.set_trace()
    # drop duplicate columns to avoid suffix after merge
    # dfc.drop(
    #     [
    #         "most_recent_pod_dt",
    #         "pod_preassessment",
    #         "most_recent_METs",
    #         "most_recent_ASA",
    #     ],
    #     axis=1,
    #     inplace=True,
    # )
    dfca = process_join_preassess_data(electives_df, preassess_df)

    # Post-op destination from case booking (clarity) join
    # ----------------------------------------------------
    # drop duplicate columns to avoid suffix after merge
    # dfca.drop(["pod_orc", "SurgeryDateClarity"], axis=1, inplace=True)
    # dfp.drop(['id'], axis=1, inplace=True)
    df = dfca.merge(
        post_op_destinations_df,
        left_on="surgical_case_epic_id",
        right_on="or_case_id",
        how="left",
    )

    # Can't drop b/c it breaks the pydantic model
    # df.drop(columns=[
    #     "PatientKey",
    #     "SurgicalCaseEpicId",
    #     "PatientDurableKey",
    #     "PlacedOnWaitingListDate",
    #     "PatientDurableKey",
    #     "LastUpdatedInstant",
    #     "SurgicalCaseUclhKey",
    #     "SurgicalCaseKey",
    #     "CaseCancelReasonCode",
    #     "CaseCancelReason",
    #     "Name",
    #     "id",
    #     "ElectiveAdmissionType",
    #     "IntendedManagement",
    #     "RemovalReason",
    #     "Subgroup",
    #     "PlannedOperationEndInstant",
    # ], inplace=True)

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
