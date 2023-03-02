import numpy as np
import pandas as pd
from pydantic import BaseModel

# from imblearn.pipeline import Pipeline
# from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
# from sklearn.linear_model import BayesianRidge
# from sklearn.ensemble import RandomForestClassifier
# from category_encoders import TargetEncoder
from api.convert import to_data_frame
import pickle
from pathlib import Path

from models.electives import (
    PreassessSummaryData,
    ClarityPostopDestination,
    SurgData,
    PreassessData,
    LabData,
    EchoWithAbnormalData,
    ObsData,
    AxaCodes,
    MedicalHx,
)
from api.electives.hypo_help import (
    merge_surg_preassess,
    wrangle_labs,
    j_wrangle_obs,
    wrangle_echo,
    fill_na,
    wrangle_pas,
    wrangle_hx,
)


def prepare_draft(
    electives: list[type[BaseModel]],
    preassess: list[type[BaseModel]],
    labs: list[type[BaseModel]],
    echo: list[type[BaseModel]],
    obs: list[type[BaseModel]],
    axa: list[type[BaseModel]],
    pod: list[type[BaseModel]],
    pa_summary: list[type[BaseModel]],
    medical_hx: list[type[BaseModel]],
    to_predict: bool = False,
) -> pd.DataFrame:

    """
    Prepares the dataframe for the dashboard by merging data from different
    sources. It loads tables for
        surgical cases ('electives')
        pre-assessment
        labs
        echos
        obs
        the final preassessment summary
        post-operative destination (from clarity)
        the list of axa codes and protocolised admissions
        it merges these tables and cleans them
        then calculates some additional features

    If to_predict is set to True, it also loads a
    pre-trained random forest model to predict ICU admission.
    """

    electives_df = to_data_frame(electives, SurgData)
    preassess_df = to_data_frame(preassess, PreassessData)
    pa_summary_df = to_data_frame(pa_summary, PreassessSummaryData)
    labs_df = to_data_frame(labs, LabData)
    echo_df = to_data_frame(echo, EchoWithAbnormalData)
    obs_df = to_data_frame(obs, ObsData)
    axa_codes = to_data_frame(axa, AxaCodes)
    pod_df = to_data_frame(pod, ClarityPostopDestination)
    hx_df = to_data_frame(medical_hx, MedicalHx)

    # axa_codes = camel_to_snake(
    #    pd.read_csv(
    #        "axa_codes.csv",
    #        encoding="cp1252",
    #        usecols=["SurgicalService", "Name", "axa_severity", "protocolised_adm"],
    #    )
    # )

    if to_predict:
        df = (
            merge_surg_preassess(surg_data=electives_df, preassess_data=preassess_df)
            .merge(pod_df, left_on="surgical_case_epic_id", right_on="or_case_id")
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
                axa_codes[
                    ["surgical_service", "name", "axa_severity", "protocolised_adm"]
                ],
                on=["surgical_service", "name"],
                how="left",
            )
            .merge(wrangle_pas(pa_summary_df), how="left", on="patient_durable_key")
            .merge(
                wrangle_hx(hx_df),
                how="left",
                on="patient_durable_key",
            )
            .merge(
                hx_df.groupby("patient_durable_key").agg({"display_string": ". ".join}),
                # .rename({"display_string": "hx_string"}),
                how="left",
                on="patient_durable_key",
            )
        )

        model_loc = "deploy/feb-3-xgb.pkl"
        with open((Path(__file__).parent / model_loc), "rb") as pickle_file:
            pipeline = pickle.load(pickle_file)

        model = pipeline.best_estimator_
        cols = model[1].feature_names_in_
        preds = model.predict_proba(df[cols])[:, 1]

        # model_name='hrishee-feb-3-xgb'
        # model_version = 4
        # mlflow_var = get_settings().mlflow_url
        # mlflow.set_tracking_uri(mlflow_var)
        # mlflowmodel = mlflow.pyfunc.load_model(
        #     model_uri=f"models:/{model_name}/{model_version}/pipeline"
        # )
        # input_col_dict = mlflowmodel.metadata.signature.inputs.to_dict()
        # inputs = [i["name"] for i in input_col_dict]
        # dtypes = {
        #     input_dict["name"]: "<U0" if input_dict["type"] == "string" else "float32"
        #     for input_dict in input_col_dict
        # }
        # future_X = model[inputs].copy().astype(dtypes)
        # preds = model.predict(future_X)

        df["icu_prob"] = preds

        # create pacu label
        df["pacu"] = np.where(
            # df["booked_destination"].astype(str).str.contains("PACU")
            # | df["pacdest"].astype(str).str.contains("PACU")
            # |
            df["pod_orc"].astype(str).str.contains("PACU"),
            True,
            False,
        )

    else:
        df = (
            merge_surg_preassess(surg_data=electives_df, preassess_data=preassess_df)
            .merge(pod_df, left_on="surgical_case_epic_id", right_on="or_case_id")
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
            # .pipe(fill_na)
            .merge(
                axa_codes[
                    ["surgical_service", "name", "axa_severity", "protocolised_adm"]
                ],
                on=["surgical_service", "name"],
                how="left",
            )
            .merge(wrangle_pas(pa_summary_df), how="left", on="patient_durable_key")
            .merge(
                hx_df.groupby("patient_durable_key").agg({"display_string": ". ".join}),
                # .rename({"display_string": "hx_string"}),
                how="left",
                on="patient_durable_key",
            )
        )
        # create pacu label
        df["pacu"] = np.where(
            df["booked_destination"].astype(str).str.contains("PACU")
            | df["pacdest"].astype(str).str.contains("PACU")
            | df["pod_orc"].astype(str).str.contains("PACU"),
            True,
            False,
        )
        df["icu_prob"] = 0

    return df
