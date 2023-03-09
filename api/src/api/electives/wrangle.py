import numpy as np
import pandas as pd

# import sympy as sym

from pydantic import BaseModel

# from imblearn.pipeline import Pipeline
# from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
# from sklearn.linear_model import BayesianRidge
# from sklearn.ensemble import RandomForestClassifier
# from category_encoders import TargetEncoder
from api.convert import to_data_frame
import pickle
import requests
from api.config import get_settings

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

        model_name = "hrishee-electives-xgb-pipeline"
        model_version = "2"

        mlflow_var = get_settings().mlflow_url
        model_uri = f"{mlflow_var}/api/2.0/mlflow/registered-models/get"
        response = requests.get(
            model_uri, params={"name": model_name, "version": model_version}
        )
        source = response.json()["registered_model"]["latest_versions"][0]["source"]
        ml_exp, run_id = source.split("/")[4:6]
        mlflowmodel_url = (
            f"{mlflow_var}/get-artifact?path=pipeline/model.pkl&run_uuid={run_id}"
        )
        mlflowmodel = pickle.loads(requests.get(mlflowmodel_url).content)
        model = mlflowmodel.best_estimator_
        cols = model[1].feature_names_in_
        preds = model.predict_proba(df[cols])[:, 1]

        df["icu_prob"] = preds

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


def aggregation(
    individual_level_predictions: pd.DataFrame,
    date_column: str,
    pred_column: str,
) -> pd.DataFrame:

    agg_series = individual_level_predictions.groupby(date_column)[pred_column].apply(
        list
    )
    # this code is from HyMind - Jen had got from Zella I think
    # TODO get my head around this
    # to instead write something that doesn't need sympy etc
    # I think it should be possible fairly easily with eg. scipy.comb

    # s = sym.Symbol("s")
    # r = sym.Symbol("r")
    # syms = sym.symbols("r0:175")
    # core_expression = (1 - r) + r * s

    # def ex(ri: sym.Symbol) -> sym.Expr:
    #     return core_expression.subs({r: ri})

    # def build_expression(n: int) -> sym.Expr:
    #     expression = 1
    #     for i in range(n):
    #         expression = expression * ex(syms[i])
    #     return expression

    # def expression_subs(
    #     expression: sym.Expr, n: int, predictions: list[float]
    # ) -> sym.Expr:
    #     substitution = dict(zip(syms[0:n], predictions[0:n]))
    #     return expression.subs(substitution)

    # def return_coeff(expression: sym.Expr, i: int) -> sym.Expr:
    #     return sym.expand(expression).coeff(s, i)

    # def pred_proba_to_pred_demand(predictions_proba: list[float]) -> list[float]:
    #     n = len(predictions_proba)
    #     expression = build_expression(n)
    #     expression = expression_subs(expression, n, predictions_proba)
    #     pred_demand = [return_coeff(expression, i) for i in range(n + 1)]
    #     return pred_demand

    # agg_demand = agg_series.apply(pred_proba_to_pred_demand)

    # agg_demand_df = pd.DataFrame(
    #     {"date": agg_demand.index, "probabilities": agg_demand.array}
    # )

    def poisson_binomial(probs: list[float]) -> list[float]:
        # we want a poisson binomial distribution for electives.
        # I have adapted the maths from
        # https://github.com/tsakim/poibin/blob/master/poibin.py

        # this uses a discrete fourier transform of the PB dist
        # timeit() 895us vs 1.71s.
        # the output is the same as above

        success_probs = np.array(probs)
        number_trials = len(probs)
        omega = 2 * np.pi / (number_trials + 1)
        chi = np.empty(number_trials + 1, dtype=complex)
        chi[0] = 1
        half_number_trials = int(number_trials / 2 + number_trials % 2)

        exp_value = np.exp(omega * np.arange(1, half_number_trials + 1) * 1j)

        xy = 1 - success_probs + success_probs * exp_value[:, np.newaxis]

        argz_sum = np.arctan2(xy.imag, xy.real).sum(axis=1)

        exparg = np.log(np.abs(xy)).sum(axis=1)
        d_value = np.exp(exparg)
        chi[1 : half_number_trials + 1] = d_value * np.exp(argz_sum * 1j)

        # set second half of chis:
        chi[half_number_trials + 1 : number_trials + 1] = np.conjugate(
            chi[1 : number_trials - half_number_trials + 1][::-1]
        )

        chi /= number_trials + 1
        xi = np.fft.fft(chi)
        xi += np.finfo(type(xi[0])).eps
        return xi.real.tolist()  # type: ignore

    agg_demand_2 = agg_series.apply(poisson_binomial)
    agg_demand_df_2 = pd.DataFrame(
        {"date": agg_demand_2.index, "probabilities": agg_demand_2.array}
    )
    return agg_demand_df_2
