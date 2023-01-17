import numpy as np
import pandas as pd
from pydantic import BaseModel

import pickle
from pathlib import Path

# from imblearn.pipeline import Pipeline
# from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
# from sklearn.linear_model import BayesianRidge
# from sklearn.ensemble import RandomForestClassifier
# from category_encoders import TargetEncoder
from api.convert import to_data_frame

from models.electives import (
    CaboodleCaseBooking,
    ClarityPostopDestination,
    CaboodlePreassessment,
    SurgData,
    PreassessData,
    LabData,
    # EchoData,
    EchoWithAbnormalData,
    ObsData,
    AxaCodes,
)
from api.electives.hypo_help import (
    merge_surg_preassess,
    wrangle_labs,
    # simple_sum,
    #  j_wrangle_echo,
    j_wrangle_obs,
    wrangle_echo,
    fill_na,
    # camel_to_snake,
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
    patient_durable_key(unique patient identifier), rather than a surgical case
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
    electives: list[type[BaseModel]],
    pod: list[type[BaseModel]],
    preassess: list[type[BaseModel]],
) -> pd.DataFrame:
    """
    Prepare elective case list

    :param      electives:  list of dicts with surgical cases
    :param      pod:    list of dicts with postop destination
    :param      preassess:    list of dicts with preassessment info

    :returns:   merged dataframe
    """
    electives_df = to_data_frame(electives, CaboodleCaseBooking)
    # electives_df = parse_to_data_frame(electives, SurgData)
    preassess_df = to_data_frame(preassess, CaboodlePreassessment)
    pod_df = to_data_frame(pod, ClarityPostopDestination)

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


def prepare_draft(
    electives: list[type[BaseModel]],
    preassess: list[type[BaseModel]],
    labs: list[type[BaseModel]],
    echo: list[type[BaseModel]],
    obs: list[type[BaseModel]],
    axa: list[type[BaseModel]],
) -> pd.DataFrame:

    electives_df = to_data_frame(electives, SurgData)
    preassess_df = to_data_frame(preassess, PreassessData)
    labs_df = to_data_frame(labs, LabData)
    echo_df = to_data_frame(echo, EchoWithAbnormalData)
    obs_df = to_data_frame(obs, ObsData)
    axa_codes = to_data_frame(axa, AxaCodes)
    # axa_codes = camel_to_snake(
    #    pd.read_csv(
    #        "axa_codes.csv",
    #        encoding="cp1252",
    #        usecols=["SurgicalService", "Name", "axa_severity", "protocolised_adm"],
    #    )
    # )

    # print(axa_codes.columns)

    df = (
        merge_surg_preassess(surg_data=electives_df, preassess_data=preassess_df)
        .merge(wrangle_labs(labs_df), how="left", on="patient_durable_key")
        .merge(wrangle_echo(echo_df), how="left", on="patient_durable_key")
        .merge(
            j_wrangle_obs(obs_df),
            how="left",
            on=["surgical_case_key", "planned_operation_start_instant"],
        )
        .sort_values("surgery_date", ascending=True)
        .drop_duplicates(subset="patient_durable_key", keep="first")
        .sort_index()
        .pipe(fill_na)
        .merge(
            axa_codes[["surgical_service", "name", "axa_severity", "protocolised_adm"]],
            on=["surgical_service", "name"],
            how="left",
        )
    )
    # print(df.columns)
    # create pacu label
    df["pacu"] = False
    df["pacu"] = np.where(
        df["booked_destination"].astype(str).str.contains("PACU"), True, df["pacu"]
    )
    df["pacu"] = np.where(
        df["pacdest"].astype(str).str.contains("PACU"), True, df["pacu"]
    )

    deployed = pickle.load(
        open((Path(__file__).parent / "deploy/RFR_jan1601.sav"), "rb")
    )
    model = deployed.best_estimator_
    cols = model[1].feature_names_in_
    preds = model.predict_proba(df[cols])[:, 1]
    df["icu_prob"] = preds

    return df
