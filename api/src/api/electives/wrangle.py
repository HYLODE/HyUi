import numpy as np
import pandas as pd
import sympy as sym

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
    # print(hx_df)

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
            axa_codes[["surgical_service", "name", "axa_severity", "protocolised_adm"]],
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

    # print(df.columns)
    # create pacu label
    df["pacu"] = np.where(
        df["booked_destination"].astype(str).str.contains("PACU")
        | df["pacdest"].astype(str).str.contains("PACU")
        | df["pod_orc"].astype(str).str.contains("PACU"),
        True,
        False,
    )

    if to_predict:
        deployed = pickle.load(
            open((Path(__file__).parent / "deploy/RFR_jan1601.sav"), "rb")
        )
        model = deployed.best_estimator_
        cols = model[1].feature_names_in_
        df_to_predict = fill_na(df)
        preds = model.predict_proba(df_to_predict[cols])[:, 1]
        df["icu_prob"] = preds
    else:
        df["icu_prob"] = 0
    return df


def aggregation(
    individual_level_predictions: pd.DataFrame,
    date_column: str,
    pred_column: str,
) -> pd.Series:

    # this code is from HyMind - Jen had got from Zella I think
    # TODO get my head around this
    # to instead write something that doesn't need sympy etc
    # I think it should be possible fairly easily with eg. scipy.comb

    agg_series = individual_level_predictions.groupby(date_column)[pred_column].apply(
        list
    )

    s = sym.Symbol("s")
    r = sym.Symbol("r")
    syms = sym.symbols("r0:175")
    core_expression = (1 - r) + r * s

    def ex(ri: sym.Symbol) -> sym.Expr:
        return core_expression.subs({r: ri})

    def build_expression(n: int) -> sym.Expr:
        expression = 1
        for i in range(n):
            expression = expression * ex(syms[i])
        return expression

    def expression_subs(
        expression: sym.Expr, n: int, predictions: list[float]
    ) -> sym.Expr:
        substitution = dict(zip(syms[0:n], predictions[0:n]))
        return expression.subs(substitution)

    def return_coeff(expression: sym.Expr, i: int) -> sym.Expr:
        return sym.expand(expression).coeff(s, i)

    def pred_proba_to_pred_demand(predictions_proba: list[float]) -> dict[int, float]:
        n = len(predictions_proba)
        expression = build_expression(n)
        expression = expression_subs(expression, n, predictions_proba)
        pred_demand_dict = {i: return_coeff(expression, i) for i in range(n + 1)}
        return pred_demand_dict

    agg_series = agg_series.apply(lambda x: pred_proba_to_pred_demand(x))

    return agg_series
