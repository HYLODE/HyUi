# type: ignore
### D Stein ICU Prediction Processing Pipeline - functions
# TODO: This file needs to be cleaned up and linting reinstated.

# Ignore linting for the moment
# flake8: noqa

from datetime import datetime, timedelta
import os
from pathlib import Path
from pprint import pprint
import urllib

# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import sqlalchemy

from scipy import stats
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
import re

import sklearn
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.model_selection import ParameterGrid, train_test_split
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    mean_squared_error,
    mean_absolute_error,
    auc,
    confusion_matrix,
    roc_curve,
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
    log_loss,
    ConfusionMatrixDisplay,
)


def test_function():
    print(os.getcwd())
    print(datetime.now())


# Helper function for reading sql query
def sql_query_from_file(query_file, sql_dir=None, verbose=True):
    """Read SQL from a text file"""
    if not sql_dir:
        sql_dir = Path(__file__).parent.resolve() / "sql"
    f = sql_dir / query_file
    query = f.read_text()
    if verbose:
        print(query)
    return query


### Build the flexible query class


# This produces a sql query given some parameters as input
# It is significantly simplified from the first iteration
class FlexibleSqlQuery:
    def __init__(self, time_interval: str):
        # Here we are just setting up the class - all will need some sort of time horizon
        if time_interval:
            self.time_interval = time_interval  # How far is the lookback?
        else:
            raise Exception("All queries need a time_interval")

        self.type = None

    def generate_query(self):
        # This formats the queries appropriately (it will be called in the appropriate method)
        # Separating it out allows individual attributes to be changed and then the query regenerated

        if self.type == "observations":
            # Observations query
            self.query = self.unformatted_query.format(
                horizon=self.time_interval,  # The period over which we pull observations
                location=self.location,  # The wards that we pull data from
                end_time=self.end_time,  # Time that the prediction is made from (end of obs collection)
                icu_location=self.icu_location,  # Which ICU wards are we predicting on?
                min_age=self.min_age,  # The minimum age that we are interested in
            )

        elif self.type == "others":
            # Labs query
            self.query = self.unformatted_query.format(
                horizon=self.time_interval,  # The period over which we pull results
                end_time=self.end_time,  # Time that the prediction is made from (end of obs collection)
                hv_ids=self.hv_ids,  # Using the hospital visit ids from the previous query
            )

        else:
            raise Exception(
                "I don't recognise the type of flexible query you are trying to use"
            )

    def observations(
        self,
        end_time: str,
        icu_location: str = "loc.location_string LIKE 'T03%%' OR loc.location_string LIKE '%%T06PACU%%' OR loc.location_string LIKE '%%GWB L01W%%'",
        min_age: int = 13,
        location: str = "SELECT location_string FROM ward_location",
    ):
        """
        Location is a string, this is the location where the patients are pulled from (usually (SELECT loc FROM ward_location))
        End_time is the time that we are looking for patients on the wards
        icu_location is a string that defaults to PACU, T03 and GWB critical care - but could easily add places here
        """
        # This method uses the census query

        # Make sure that we can't change the purpose of different queries
        if self.type:
            if self.type != "observations":
                raise Exception(
                    "This query is already a obs query. You can't reuse it. Please instantiate a new query"
                )
        else:
            self.type = "observations"

        # Again we are hard coding that census query has to be from this file
        self.unformatted_query = sql_query_from_file(
            "Observations_V3.sql", verbose=False
        )

        # First do the location bits
        self.location = location
        self.icu_location = icu_location

        # Now do some timing bits
        self.end_time = end_time  # This needs to be manually formatted - could potentially be fixed but slightly reduces flexibility

        # These are defaults but can be changed
        self.min_age = (
            str(min_age) + " YEARS"
        )  # The minimum age of patients we are looking for

        # Now just generate the query
        self.generate_query()

    def others(self, subtype: str, end_time: str, hv_ids: np.array):
        # Make sure that we can't change the purpose of different queries
        if self.type:
            if self.type != "others":
                raise Exception(
                    "This query is already a others query. You can't reuse it. Please instantiate a new query"
                )
        else:
            self.type = "others"

        if subtype == "labs":
            # Again we are hard coding that labs query has to be from this file
            self.unformatted_query = sql_query_from_file("Labs_V3.sql", verbose=False)

        elif subtype == "consults":
            self.unformatted_query = sql_query_from_file(
                "Consults_V3.sql", verbose=False
            )

        elif subtype == "others":
            self.unformatted_query = sql_query_from_file("Others_V3.sql", verbose=False)
            # Note that for others the time window is how far to look back for recent theatres and ICU

        # Set the time to make predictions from
        self.end_time = end_time

        # Make the list of hv_ids
        # Process IDs into useable string
        hv_ids = np.unique(hv_ids)
        formatted_hv_ids = "'" + str(hv_ids[0]) + "'"
        for i in hv_ids[1:]:
            formatted_hv_ids = formatted_hv_ids + ", " + "'" + str(i) + "'"
        self.hv_ids = formatted_hv_ids

        # Now just generate the query
        self.generate_query()

    def __str__(self):
        return self.query

    def __call__(self):
        return self.query


# Make a function that can be used for the aggregates
# Potentially should have some rules about returning nas (2 values for the slope, 3 values for the r value)
def linear_slope(x_input: np.array, returns: str) -> int:
    """Function that takes an series and returns the slope of a linear fit or r value
    Takes a numpy array as its input, requires to specify whether it should return r value or slope
    """

    # Name the various inputs for R value
    R = ("r", "R", "r value", "r-value", "r_value", "R value", "R-value", "R_value")

    # Coerce np dtype to float
    x_array = x_input.astype("float")

    # Find the values that aren't na
    not_na = np.isnan(x_array) == False

    # Make them into np arrays
    x = np.array(x_input[not_na], dtype="float")
    y = np.array(range(x.shape[0]))

    # Some rules about returning nas
    if x.shape[0] < 2:
        return 0

    # Make sure we return no value for fit quality if only 2 points
    elif (x.shape[0] < 3) and (returns in R):
        return 0

    else:
        if returns == "slope":
            return stats.linregress(y, x)[0]

        elif returns in R:
            return stats.linregress(y, x)[2]

        else:
            raise Exception("This needs to be either slope or R value")


# Custom function to compare across times where some are none
def argmax_time(time_array: np.array) -> int:
    """Function that takes an array and returns the maximum value
    Just uses np.argmax but ignores non-time values"""

    # This falls down if the referrals are run when the times are changed (e.g. GMT -> BST)
    try:
        new_array = time_array.astype(np.datetime64)

        # only argmax over ones that aren't NaN (note that np.argmax can handle NaN but not NaT)
        not_na = np.where(np.isnan(new_array) == False)
        max_time = np.argmax(new_array[not_na[0]])

        return not_na[0][max_time]

    # So here we manually run it through np.datetime and if it falls down allocate NaT
    # This isn't the most efficient way of doing things but will only have to be used on days
    # when the times change
    except:
        new_array = np.array([], dtype=np.datetime64)

        # Work through the array and try to convert to dt
        for position, date in enumerate(time_array):
            try:
                new_date = np.datetime64(date)
            except:
                new_date = np.datetime64("NaT")

            # Add to the array
            new_array = np.append(new_array, new_date)

        # only argmax over ones that aren't NaN (note that np.argmax can handle NaN but not NaT)
        not_na = np.where(np.isnan(new_array) == False)
        max_time = np.argmax(new_array[not_na])

        return not_na[0][max_time]


# Now run the whole pipeline
def run_pipeline(date_list: list, engine, now: bool = False) -> pd.DataFrame:
    """Function to run the whole data preparation pipeline
    We need to pass a list of dates and the number of hours to take obs from
    """

    # We have to set up the column names that we are going to use:
    # Choose the columns we're going to iterate over
    cols_for_agg = list(
        [
            "ALB",
            "ALP",
            "ALT",
            "BCST",
            "BILI",
            "CA",
            "CCA",
            "COHb",
            "CREA",
            "CRP",
            "FiO2",
            "GCS_Total",
            "GFR",
            "Glu",
            "Hb",
            "HCTU",
            "HTRT",
            "INR",
            "K",
            "LDH",
            "LY",
            "Lac",
            "MCVU",
            "MG",
            "NA",
            "NE",
            "NEWS_Score",
            "Oxygen_therapy_flow_rate",
            "PHOS",
            "PLT",
            "PT",
            "Pain_score,_verbal_at_rest",
            "Pain_score,_verbal_on_movement",
            "Pulse",
            "RCC",
            "Resp",
            "SpO2",
            "Temp",
            "UREA",
            "WCC",
            "pCO2",
            "pH",
            "Sys_BP",
            "Dia_BP",
            "MAP",
            "Oxygen_delivery_device_enc",
            "AVPU_enc",
            "Oxygen_enc",
            "pressure_areas_observed",
        ]
    )

    # Now columns just to take count from
    cols_for_count = list(
        [
            "Inpatient_consult_to_Intensivist",
            "Inpatient_consult_to_PERRT",
            "Inpatient_consult_to_Social_Work",
            "Recent_palliative_ref",
        ]
    )

    # This are the columns that we only want the most recent value from
    cols_for_last = list(
        [
            "sex_enc",
            "building_enc",
            "bed_type_enc",
            "age_at_obs",
            "NEWS2_scale",
            "asian_ethnicity",
            "black_ethnicity",
            "chinese_ethnicity",
            "other_ethnicity",
            "white_ethnicity",
            "missing_ethnicity",
            "10201000174_ward",
            "1020100163_ward",
            "1020100172_ward",
            "1020100175_ward",
            "1021800004_ward",
            "1021800025_ward",
            "1021800026_ward",
            "1021800027_ward",
            "1021800028_ward",
            "1021800030_ward",
            "1021800031_ward",
            "ACU_ward",
            "BBNU_ward",
            "BCN_ward",
            "COB_ward",
            "F3NU_ward",
            "HS15_ward",
            "HSDC_ward",
            "LW_ward",
            "MFAW_ward",
            "T01_ward",
            "T01ECU_ward",
            "T06H_ward",
            "T07_ward",
            "T08N_ward",
            "T08S_ward",
            "T09C_ward",
            "T09N_ward",
            "T09S_ward",
            "T10O_ward",
            "T10S_ward",
            "T12N_ward",
            "T12S_ward",
            "T13N_ward",
            "T13S_ward",
            "T14N_ward",
            "T14S_ward",
            "T16N_ward",
            "T16S_ward",
            "dnacpr",
            "recent_surgery",
            "ever_surgery",
            "recent_icu",
            "med_ref",
            "og_ref",
            "ortho_ref",
            "surg_ref",
            "No_initial_ref",
            "onc_ref",
            "elective_surgery",
            "emergency_surgery",
            "emergency_admission",
            "icu_admission",
        ]
    )

    # Make the colnames
    final_inputs_colnames = list()
    for i in cols_for_agg:
        final_inputs_colnames.extend(
            [f"Mean_{i}", f"Slope_{i}", f"R_{i}", f"Count_{i}", f"Last_{i}"]
        )

    # Add in the columns that we are just taking the last value from
    final_inputs_colnames.extend(cols_for_last)
    for i in cols_for_count:
        final_inputs_colnames.extend([f"Count_{i}"])

    # Copy this list so we can include the ward strain variables and missing markers
    practice_dataset_colnames = final_inputs_colnames.copy()
    practice_dataset_colnames.extend(["average_ward_NEWS", "ward_NEWS_over_5"])
    practice_dataset_colnames.extend([f"Missing_{i}" for i in cols_for_agg])

    final_inputs_colnames.extend(["ward_raw"])

    # Set up some storage for outcomes
    practice_dataset = pd.DataFrame(columns=practice_dataset_colnames)

    # Store the median values
    medians = {
        "Mean_ALB": 35.0,
        "Last_ALB": 35.0,
        "Mean_ALP": 96.75,
        "Last_ALP": 96.0,
        "Mean_ALT": 24.0,
        "Last_ALT": 24.0,
        "Mean_BILI": 7.0,
        "Last_BILI": 7.0,
        "Mean_CA": 2.21,
        "Last_CA": 2.21,
        "Mean_CCA": 2.42,
        "Last_CCA": 2.42,
        "Mean_COHb": 1.2,
        "Last_COHb": 1.2,
        "Mean_CREA": 67.0,
        "Last_CREA": 67.0,
        "Mean_CRP": 31.0,
        "Last_CRP": 29.1,
        "Mean_FiO2": 21,  # Note I've manually changed this to be normal as it isn't usually recorded when abnormal
        "Last_FiO2": 21.0,
        "Mean_GCS_Total": 15.0,
        "Last_GCS_Total": 15.0,
        "Mean_GFR": 90.0,
        "Last_GFR": 90.0,
        "Mean_Glu": 6.0,
        "Last_Glu": 6.0,
        "Mean_HCTU": 0.328,
        "Last_HCTU": 0.328,
        "Mean_HTRT": 21.0,
        "Last_HTRT": 20,
        "Mean_INR": 1.03,
        "Last_INR": 1.03,
        "Mean_K": 4.1,
        "Last_K": 4.1,
        "Mean_LDH": 280.0,
        "Last_LDH": 278.0,
        "Mean_LY": 1.2,
        "Last_LY": 1.2,
        "Mean_Lac": 1.3,
        "Last_Lac": 1.2,
        "Mean_MCVU": 90.1,
        "Last_MCVU": 90.1,
        "Mean_MG": 0.8,
        "Last_MG": 0.8,
        "Mean_NA": 137.5,
        "Last_NA": 137.0,
        "Mean_NE": 5.68,
        "Last_NE": 5.5,
        "Mean_NEWS_Score": 0.8333333333333334,
        "Last_NEWS_Score": 1.0,
        "Mean_Oxygen_therapy_flow_rate": 0.0,
        "Last_Oxygen_therapy_flow_rate": 0.0,
        "Mean_PHOS": 1.06,
        "Last_PHOS": 1.06,
        "Mean_PLT": 237.0,
        "Last_PLT": 237.0,
        "Mean_PT": 11.3,
        "Last_PT": 11.3,
        "Mean_Pain_score,_verbal_at_rest": 1.0,
        "Last_Pain_score,_verbal_at_rest": 1.0,
        "Mean_Pain_score,_verbal_on_movement": 0.3333333333333333,
        "Last_Pain_score,_verbal_on_movement": 0.0,
        "Mean_Pulse": 81.0,
        "Last_Pulse": 81.0,
        "Mean_RCC": 3.65,
        "Last_RCC": 3.65,
        "Mean_Resp": 17.6,
        "Last_Resp": 18.0,
        "Mean_SpO2": 97.16666666666667,
        "Last_SpO2": 97.0,
        "Mean_Temp": 98.1,
        "Last_Temp": 98.2,
        "Mean_UREA": 5.2,
        "Last_UREA": 5.2,
        "Mean_WCC": 8.06,
        "Last_WCC": 7.88,
        "Mean_pCO2": 5.67,
        "Last_pCO2": 5.62,
        "Mean_pH": 7.412,
        "Last_pH": 7.413,
        "Mean_Hb": 122.0,
        "Last_Hb": 121.0,
        "Mean_Sys_BP": 123.0,
        "Last_Sys_BP": 123.0,
        "Mean_Dia_BP": 69.14285714285714,
        "Last_Dia_BP": 69.0,
        "Mean_MAP": 87.33333333333333,
        "Last_MAP": 87.66666666666666,
        "Mean_Oxygen_delivery_device_enc": 0.0,
        "Last_Oxygen_delivery_device_enc": 0.0,
        "Mean_AVPU_enc": 0.0,
        "Last_AVPU_enc": 0.0,
        "Mean_Oxygen_enc": 0.0,
        "Last_Oxygen_enc": 0.0,
        "Mean_pressure_areas_observed": 0.6666666666666666,
        "Last_pressure_areas_observed": 1.0,
    }

    # Work through all of the dates to get ICU admission after 24h from ward patients
    for number, date in enumerate(date_list):
        if not now:
            # Using 09:30 as this is when sitrep is - change the start time on both of the sql queries, formatted for postgres, alternating day and night
            end_time = "DATE '" + str(date) + " 09:30:00'"

        # Allow the query to be generated for now
        else:
            end_time = "NOW()"

        ### Do the data pulls
        print(f"do data pulls for {date}, starting at " + str(datetime.now()))

        # Do the observations pull
        obs_query = FlexibleSqlQuery("24 HOURS")
        obs_query.observations(end_time)
        obs_df = pd.read_sql(obs_query(), engine)

        # The labs pull
        labs_query = FlexibleSqlQuery("72 HOURS")
        labs_query.others("labs", end_time, obs_df["hospital_visit_id"])
        labs_df = pd.read_sql(labs_query(), engine)

        # Consults pull
        consults_query = FlexibleSqlQuery("48 HOURS")
        consults_query.others("consults", end_time, obs_df["hospital_visit_id"])
        consults_df = pd.read_sql(consults_query(), engine)

        # Other data pull
        other_query = FlexibleSqlQuery("7 DAYS")
        other_query.others("others", end_time, obs_df["hospital_visit_id"])
        others_df = pd.read_sql(other_query(), engine)

        print("data pulls done")

        ### Some data processing for obs

        # Combine columns where can be text or numeric
        combined_column = obs_df["value_as_text"].combine_first(obs_df["value_as_real"])
        obs_df["value"] = combined_column

        # Make a table of only the things we want to keep
        obs_only_df = obs_df.loc[
            :, ["hospital_visit_id", "observation_datetime", "value", "vital"]
        ]

        ### Data processing for labs

        # Combine values to make a single result column
        labs_df["value"] = labs_df["value_as_real"].combine_first(
            labs_df["value_as_text"]
        )

        # Rename test_lab_code to vital
        labs_df["vital"] = labs_df["test_lab_code"]

        # Make a datetime column: for cultures we care about request time, for others valid_from
        labs_df["observation_datetime"] = labs_df["valid_from"]

        # Make a table of only the columns we want to keep
        labs_only_df = labs_df.loc[
            :, ["hospital_visit_id", "observation_datetime", "vital", "value"]
        ]

        # Now bin any rows outside of the time window (because blood cultures might have been ordered some time ago)

        ### This is the first possible point of failure

        print("trying timedelta thing")
        begin_date = (date - timedelta(days=3)).isoformat()

        ###

        try:
            labs_only_df = labs_only_df.loc[
                labs_only_df["observation_datetime"] > begin_date, :
            ]
        except:
            locations_before_end = np.array(
                labs_only_df["observation_datetime"], dtype=np.datetime64
            )
            labs_only_df = labs_only_df.loc[
                locations_before_end > np.datetime64(begin_date), :
            ]

        ### Now consults
        # Make an extra column as there is no 'value' associated with an order
        consults_df["value"] = 1

        # Rename and keep only the columns we want
        consults_df["observation_datetime"] = consults_df["valid_from"]
        consults_df["vital"] = consults_df["name"]
        consults_only_df = consults_df.loc[
            :, ["hospital_visit_id", "observation_datetime", "vital", "value"]
        ]

        # Combine all the palliative ones
        consults_only_df.loc[
            consults_df.vital
            == "Inpatient Consult to Symptom Control and Palliative Care",
            ["vital"],
        ] = "Recent_palliative_ref"
        consults_only_df.loc[
            consults_df.vital
            == "Inpatient Consult to Transforming end of life care team",
            ["vital"],
        ] = "Recent_palliative_ref"

        ### Now stick them all together

        results_df = pd.concat([obs_only_df, labs_only_df, consults_only_df])

        # Now reset the index
        results_df = results_df.reset_index()
        results_df = results_df.loc[
            :, ["hospital_visit_id", "observation_datetime", "value", "vital"]
        ]

        # Now drop any annoying duplicates
        Unique_results_index = (
            results_df.loc[:, ["hospital_visit_id", "observation_datetime", "vital"]]
            .drop_duplicates(keep="last")
            .index
        )
        results_df = results_df.loc[Unique_results_index, :]

        ### Now processing them into a pivot table

        # Now make a pivot table
        Pivot_results = results_df.pivot(
            index=["hospital_visit_id", "observation_datetime"],
            columns="vital",
            values=["value"],
        )

        # Annoying way to allow us to subsequently merge because pivotting on 2 columns gives multi index
        Pivot_results.columns = [i[1] for i in Pivot_results.columns.to_flat_index()]
        Pivot_results = Pivot_results.reset_index()

        ##Now split BP in the Pivotted results
        # Find all non-na BPs and split them
        BP_isnt_na = Pivot_results["BP"].isna() == False
        Split_BP = Pivot_results.loc[BP_isnt_na, "BP"].str.split(pat="/")

        # Make new columns and get BPs including MAP
        Pivot_results["Sys_BP"] = Pivot_results["Dia_BP"] = Pivot_results[
            "MAP"
        ] = np.nan
        Sys_BP = np.array([i[0] for i in Split_BP], dtype="int")
        Dia_BP = np.array([i[1] for i in Split_BP], dtype="int")

        # Calculate MAP and then assign the values into the column
        MAP = Dia_BP + (Sys_BP - Dia_BP) * (1 / 3)
        Pivot_results.loc[BP_isnt_na, "Sys_BP"] = Sys_BP
        Pivot_results.loc[BP_isnt_na, "Dia_BP"] = Dia_BP
        Pivot_results.loc[BP_isnt_na, "MAP"] = MAP

        # Now merge back on the missing values
        non_pivotted_columns = [
            "location_string",
            "age_at_obs",
            "mrn",
            "hospital_visit_id",
            "ethnicity",
            "sex",
            "bed",
            "ward_raw",
            "building",
            "bed_type",
            "icu_admission",
            "hospital_discharge_dt",
        ]
        Pivot_all = pd.merge(
            Pivot_results, obs_df.loc[:, non_pivotted_columns], on=["hospital_visit_id"]
        )

        # First drop duplicate rows
        Pivot_all.drop_duplicates(inplace=True)

        ### Now the processing so we can infer what type of initial referral (specialty) the patients had

        # Duplicate others_df so we can rerun a few times
        other_df = others_df.copy()

        # These are the two columns we are interested in
        other_df["ref_type"] = None
        other_df["onc_ref"] = False

        # Record whether each patient has a given type of referral
        med_refs = np.array(other_df["med_ref"].isna(), dtype=int)
        surg_refs = np.array(other_df["surg_ref"].isna(), dtype=int)
        og_refs = np.array(other_df["og_ref"].isna(), dtype=int)
        ortho_refs = np.array(other_df["ortho_ref"].isna(), dtype=int)
        haem_onc_refs = np.array(other_df["haem_onc_ref"].isna(), dtype=int)
        refs_array = np.array([surg_refs, med_refs, og_refs, haem_onc_refs, ortho_refs])

        # Now determine the total number of referrals each patient has
        number_refs = 5 - np.sum(
            [med_refs, surg_refs, og_refs, ortho_refs, haem_onc_refs], axis=0
        )
        num_not_onc = 4 - np.sum([med_refs, surg_refs, og_refs, ortho_refs], axis=0)

        # Where only one referral make this the referral type
        colnames = np.array(other_df.columns[2:7])
        single_refs = colnames[np.argmin(refs_array[:, num_not_onc == 1], axis=0)]
        other_df.loc[num_not_onc == 1, ["ref_type"]] = single_refs

        print("trying to to_datetime")
        # Convert all referral times to datetime where not already true
        # This is annoying but necessary
        try:
            other_df.surg_ref = pd.to_datetime(other_df.surg_ref)
        except:
            print("surg ref doesnt need to be converted to datetime")

        try:
            other_df.og_ref = pd.to_datetime(other_df.og_ref)
        except:
            print("og ref doesnt need to be converted to datetime")

        try:
            other_df.ortho_ref = pd.to_datetime(other_df.ortho_ref)
        except:
            print("ortho ref doesnt need to be converted to datetime")

        try:
            other_df.haem_onc_ref = pd.to_datetime(other_df.haem_onc_ref)
        except:
            print("haemonc ref doesnt need to be converted to datetime")

        try:
            other_df.med_ref = pd.to_datetime(other_df.med_ref)
        except:
            print("med ref doesnt need to be converted to datetime")

        print("finished to datetime")

        # Now where multiple take last one (excluding haemonc)
        non_onc_refs = np.array(["surg_ref", "med_ref", "og_ref", "ortho_ref"])

        print("trying argmax_time")

        last_ref = other_df.loc[num_not_onc > 1, non_onc_refs].apply(
            argmax_time, axis=1
        )

        if np.where(num_not_onc > 1)[0].shape[0] > 0:
            other_df.loc[num_not_onc > 1, ["ref_type"]] = non_onc_refs[last_ref]
        print("finished argmax_time")

        # Now if there are any places where there is a haem ref but no other ref (unlikely due to sql query)
        #  set reftype to medref
        haemonc_only = np.intersect1d(
            np.where(other_df["ref_type"].isna() == True),
            np.where(other_df.haem_onc_ref.isna() == False),
        )
        if haemonc_only.shape[0] > 0:
            other_df.loc[haemonc_only, ["ref_type"]] = "med_ref"

        # Now where there is a haemonc ref set haemonc to true
        other_df.loc[other_df.haem_onc_ref.isna() == False, ["onc_ref"]] = True

        ### Now process theatre locations so we can see if someone has been to theatre before

        other_df["elective_surgery"] = 0
        other_df["emergency_surgery"] = 0

        # Set where a patient has been to either elective or emergency theatres
        other_df.loc[other_df["ever_surgery"] == "T02THR", "emergency_surgery"] = 1
        other_df.loc[other_df["ever_surgery"] == "THP3", "elective_surgery"] = 1
        other_df.loc[
            other_df["ever_surgery"] == "1021800001", "elective_surgery"
        ] = 1  # GWB theatres

        # Now mark if patient has had recent or ever surgery
        other_df["recent_surgery"] = other_df["recent_surgery"].isna() == False
        other_df["ever_surgery"] = other_df["ever_surgery"].isna() == False

        # Now do the same for ICU
        other_df["recent_icu"] = other_df["recent_icu"].isna() == False

        # And for DNACPR
        other_df["dnacpr"] = other_df["dnacpr"] == "DNACPR"

        # And for emergency admission
        other_df["emergency_admission"] = other_df["first_ward"].isna() == False

        # One hot encode ref_type
        ref_cat = np.array(other_df["ref_type"]).reshape(
            -1, 1
        )  # Annoying reshape for sk.OHE
        OH_enc = OneHotEncoder()
        OH_ref = OH_enc.fit_transform(ref_cat).toarray()

        # Make DF of them
        OH_categories = OH_enc.categories_[0]
        OH_categories[OH_categories == None] = "No_initial_ref"
        ref_df = pd.DataFrame(OH_ref, columns=OH_categories)

        # Now make other_df only the colums we want
        other_df = other_df.loc[
            :,
            [
                "hospital_visit_id",
                "admission_datetime",
                "dnacpr",
                "recent_surgery",
                "ever_surgery",
                "recent_icu",
                "onc_ref",
                "elective_surgery",
                "emergency_surgery",
                "emergency_admission",
            ],
        ]

        # Now merge back on
        other_df = pd.concat([other_df, ref_df], axis=1)

        # Now add back this extra data
        Pivot_all = pd.merge(Pivot_all, other_df, on=["hospital_visit_id"])

        ### Some very simple data validation here
        # Make some rules for imputation
        No_flow_rate = np.where(Pivot_all["Oxygen therapy flow rate"].isna())

        # Where there is no flow rate and on room air or no supplemental oxygen
        Room_air = np.where(Pivot_all["Oxygen"] == "Room air")
        No_resp_support = np.where(
            Pivot_all["Oxygen delivery device"] == "No respiratory support provided"
        )

        # Where FiO2 is 21 or 22 or empty
        FiO2_sealevel = np.where([23 < Pivot_all["FiO2"]] == False)
        Room_air_no_support = np.union1d(
            FiO2_sealevel, np.union1d(Room_air, No_resp_support)
        )

        # Now set to zero
        Pivot_all.loc[
            Pivot_all.index[np.intersect1d(Room_air_no_support, No_flow_rate)],
            "Oxygen therapy flow rate",
        ] = 0

        # Where GCS is 15 we can assume AVPU is A
        GCS_15 = np.array(Pivot_all["GCS Total"] == 15, dtype="int")
        AVPU_na = np.array(Pivot_all["AVPU"].isna(), dtype="int")

        # Should probably use GCS_V but not currently pulling through as no one has it
        Pivot_all.loc[(GCS_15 + AVPU_na) > 1, "AVPU"] = "A"

        ### Now finally for the proper data transformation steps

        # First encode the oxygen delivery devices
        O2_delivery_mapping = {
            "No respiratory support provided": 0,
            "Nasal cannula": 1,
            "Simple mask": 1,
            "Humidified oxygen mask": 1,
            "Non-rebreather mask": 1,
            "Capno mask": 1,
            "CPAP/Bi-PAP mask": 2,
        }

        Pivot_all["Oxygen_delivery_device_enc"] = pd.to_numeric(
            Pivot_all["Oxygen delivery device"].map(O2_delivery_mapping),
            errors="coerce",
        )

        # Now encode AVPU
        AVPU_mapping = {"A": 0, "C": 1, "V": 2, "P": 3, "U": 4}
        Pivot_all["AVPU_enc"] = pd.to_numeric(
            Pivot_all["AVPU"].map(AVPU_mapping), errors="coerce"
        )

        # Now encode oxygen
        Oxygen_mapping = {"Room air": 0, "Supplemental Oxygen": 1}
        Pivot_all["Oxygen_enc"] = pd.to_numeric(
            Pivot_all["Oxygen"].map(Oxygen_mapping), errors="coerce"
        )

        # Combine where more than one source is available
        if "Na+" in Pivot_all.columns:
            Pivot_all["NA"] = Pivot_all["NA"].combine_first(Pivot_all["Na+"])
        if "K+" in Pivot_all.columns:
            Pivot_all["K"] = Pivot_all["K"].combine_first(Pivot_all["K+"])
        if "Crea" in Pivot_all.columns:
            Pivot_all["CREA"] = Pivot_all["CREA"].combine_first(Pivot_all["Crea"])
        if "NEWS2 Score" in Pivot_all.columns:
            Pivot_all["NEWS Score"] = Pivot_all["NEWS Score"].combine_first(
                Pivot_all["NEWS2 Score"]
            )
        if "tHb" in Pivot_all.columns:
            Pivot_all["Hb"] = Pivot_all["HBGL"].combine_first(Pivot_all["tHb"])
        if "UREA" in Pivot_all.columns:
            if "Urea" in Pivot_all.columns:
                Pivot_all["UREA"] = Pivot_all["UREA"].combine_first(Pivot_all["Urea"])

        ### Some one-hot encoding of ethnicity and then other variables
        # Here I effectively decided that refused to give/unavailable should be NA
        ethnicity_mapping = {
            "White British": "white",
            "White Irish": "white",
            "Other White Background": "white",
            "Black Caribbean": "black",
            "Black African": "black",
            "Other Black Background": "black",
            "BLACK BRITIS": "black",
            "Asian Bangladeshi": "asian",
            "Asian Indian": "asian",
            "Asian Pakistani": "asian",
            "Other Asian Background": "asian",
            "Chinese": "chinese",
            #'Not Yet Asked': 'other',
            "Other Ethnic Group": "other",
            # None: 'other',
            #'Not Stated/ Unknown': 'other',
            "Other Mixed Background": "other",
            "Mixed White and Asian": "other",
            "Mixed White and Black Caribbean": "other",
            #'Refused to Give': 'other',
            "Mixed White and Black African": "other",
        }

        # Make an intermediate variable with larger categories
        Pivot_all["ethnic_cat"] = Pivot_all["ethnicity"].map(ethnicity_mapping)

        # Now do the one hot encoding
        ethnic_cat = np.array(Pivot_all["ethnic_cat"]).reshape(
            -1, 1
        )  # Annoying reshape for sk.OHE
        OH_enc = OneHotEncoder()
        OH_ethnicity = OH_enc.fit_transform(ethnic_cat).toarray()

        # Now make something we can merge back onto the main table
        ethnic_categories = [str(i) + "_ethnicity" for i in OH_enc.categories_[0]]

        # Don't want one named 'nan_ethnicity'
        nan_ethnicity = [
            i for i, j in enumerate(ethnic_categories) if j == "nan_ethnicity"
        ]
        ethnic_categories[nan_ethnicity[0]] = "missing_ethnicity"
        ethnicity_df = pd.DataFrame(OH_ethnicity, columns=ethnic_categories)

        # Now merge back on
        Pivot_all = pd.concat([Pivot_all, ethnicity_df], axis=1)

        ### Now for the wards - these are just the wards that were available that day but I plan to strip it down so only certain wards are available

        ward_list = np.array(
            [
                "10201000174",
                "1020100163",
                "1020100172",
                "1020100175",
                "1021800004",
                "1021800025",
                "1021800026",
                "1021800027",
                "1021800028",
                "1021800030",
                "1021800031",
                "ACU",
                "BBNU",
                "BCN",
                "COB",
                "F3NU",
                "HS15",
                "HSDC",
                "LW",
                "MFAW",
                "T01",
                "T01ECU",
                "T06H",
                "T07",
                "T08N",
                "T08S",
                "T09C",
                "T09N",
                "T09S",
                "T10O",
                "T10S",
                "T12N",
                "T12S",
                "T13N",
                "T13S",
                "T14N",
                "T14S",
                "T16N",
                "T16S",
            ]
        )

        # Now do the one hot encoding
        ward_array = ward_list.reshape(-1, 1)  # Annoying reshape for sk.OHE
        OH_enc = OneHotEncoder(handle_unknown="ignore")
        OH_enc.fit(ward_array)  # Fit the encoder
        OH_ward = OH_enc.transform(
            np.array(Pivot_all["ward_raw"]).reshape(-1, 1)
        ).toarray()

        # Rename them so it says ward
        ward_list = [i + "_ward" for i in ward_list]
        ward_df = pd.DataFrame(OH_ward, columns=ward_list)

        # Now merge back on
        Pivot_all = pd.concat([Pivot_all, ward_df], axis=1)

        # Do something with the all pressure areas thing:
        Pressure_mapping = {"No (Comment)": 0, "Yes": 1}
        # Sorry this is a slightly nasty looking line
        Pivot_all["pressure_areas_observed"] = pd.to_numeric(
            Pivot_all["All pressure areas observed?"].map(Pressure_mapping),
            errors="coerce",
        )

        # Sex
        Sex_mapping = {"F": 0, "M": 1}
        Pivot_all["sex_enc"] = pd.to_numeric(
            Pivot_all["sex"].map(Sex_mapping), errors="coerce"
        )

        # Building
        Building_mapping = {"tower": 0, "EGA": 1, "GWB": 2}
        Pivot_all["building_enc"] = pd.to_numeric(
            Pivot_all["building"].map(Building_mapping), errors="coerce"
        )

        # Bed type
        Bed_mapping = {"bay": 0, "sideroom": 1}
        Pivot_all["bed_type_enc"] = pd.to_numeric(
            Pivot_all["bed_type"].map(Bed_mapping), errors="coerce"
        )

        # Mark if a patient is on the NEWS2 Scale
        if "NEWS2_Score" in Pivot_all.columns:
            Pivot_all["NEWS2_scale"] = Pivot_all.NEWS2_Score.isna() == False
        else:
            Pivot_all["NEWS2_scale"] = False

        # Remove spaces from colnames
        Pivot_all.columns = [re.sub(" ", "_", i) for i in Pivot_all.columns]

        ### Now finally for the data aggregation steps

        # If columns not avalaible make them but empty:
        columns_for_transformed = cols_for_agg + cols_for_last + cols_for_count
        available_columns = np.intersect1d(columns_for_transformed, Pivot_all.columns)
        unavailable_columns = [
            i for i in columns_for_transformed if not i in available_columns
        ]
        Pivot_all.reset_index(inplace=True)
        try:
            Pivot_all.loc[:, unavailable_columns] = np.nan
        except:
            for i in unavailable_columns:
                Pivot_all.loc[:, [i]] = np.nan

        # Force all interesting columns to numeric
        Transformed_dataframe = Pivot_all.loc[
            :, cols_for_agg + cols_for_last + cols_for_count
        ]
        non_numeric_columns = Transformed_dataframe.dtypes.index[
            Transformed_dataframe.dtypes == "object"
        ]
        Transformed_dataframe[non_numeric_columns] = Transformed_dataframe[
            non_numeric_columns
        ].apply(pd.to_numeric, errors="coerce")

        # Add back CSN and datetime
        Transformed_dataframe[
            ["hospital_visit_id", "observation_datetime", "ward_raw"]
        ] = Pivot_all[["hospital_visit_id", "observation_datetime", "ward_raw"]]

        # Set up our new storage
        final_inputs_index = Transformed_dataframe["hospital_visit_id"].unique()
        final_inputs = pd.DataFrame(
            np.nan, columns=final_inputs_colnames, index=final_inputs_index
        )

        for colname in cols_for_agg:
            all_colnames = [
                f"Mean_{colname}",
                f"Slope_{colname}",
                f"R_{colname}",
                f"Count_{colname}",
                f"Last_{colname}",
            ]

            # We're looping through all of the columns calling these aggregate functions
            final_inputs.loc[:, all_colnames] = Transformed_dataframe.groupby(
                "hospital_visit_id"
            ).agg(
                **{
                    f"Mean_{colname}": pd.NamedAgg(colname, aggfunc=np.mean),
                    # These two return the slope and r value for a least squares fit line
                    f"Slope_{colname}": pd.NamedAgg(
                        colname, aggfunc=lambda x: linear_slope(x, returns="slope")
                    ),
                    f"R_{colname}": pd.NamedAgg(
                        colname, aggfunc=lambda x: linear_slope(x, returns="r value")
                    ),
                    # These named functions exclude nans helpfully
                    f"Count_{colname}": pd.NamedAgg(colname, aggfunc="count"),
                    f"Last_{colname}": pd.NamedAgg(colname, aggfunc="last"),
                }
            )

        for colname in cols_for_last:
            # We're looping through all of the columns calling these aggregate functions
            final_inputs.loc[:, colname] = Transformed_dataframe.groupby(
                "hospital_visit_id"
            ).agg(**{colname: pd.NamedAgg(colname, aggfunc="last")})

        for colname in cols_for_count:
            # We're looping through all of the columns calling these aggregate functions
            final_inputs.loc[:, colname] = Transformed_dataframe.groupby(
                "hospital_visit_id"
            ).agg(**{colname: pd.NamedAgg(colname, aggfunc="count")})

        final_inputs.loc[:, "ward_raw"] = Transformed_dataframe.groupby(
            "hospital_visit_id"
        ).agg(**{"ward_raw": pd.NamedAgg("ward_raw", aggfunc="last")})

        ### Now for the ward acuity steps
        final_inputs["ward_NEWS_over_5"] = np.nan
        final_inputs["average_ward_NEWS"] = np.nan

        # Work through all the wards, getting the number of patients with a NEWS > 5
        for i in final_inputs["ward_raw"].unique():
            ward_locs = final_inputs["ward_raw"] == i

            # Patients with a NEWS >5
            ward_NEWS_over_5 = len(
                np.intersect1d(
                    np.where(pd.to_numeric(final_inputs["Last_NEWS_Score"]) >= 5),
                    np.where(ward_locs),
                )
            )

            # Mean news
            mean_NEWS = np.nanmean(final_inputs.Last_NEWS_Score[ward_locs])

            # Now re_allocate
            final_inputs.loc[ward_locs, ["average_ward_NEWS"]] = mean_NEWS
            final_inputs.loc[ward_locs, ["ward_NEWS_over_5"]] = ward_NEWS_over_5

        ### Now we are going to impute the missing values
        # Keep track of missingness
        for i in cols_for_agg:
            final_inputs[f"Missing_{i}"] = final_inputs[f"Last_{i}"].isna()

        # Now work through and do the median imputation
        for i in medians:
            final_inputs.loc[final_inputs[i].isna(), i] = medians[i]

        # Make all others 0 where they are nan
        for i in cols_for_count:
            final_inputs.loc[final_inputs[i].isna(), i] = 0

        # Finally paste onto our practice dataset
        practice_dataset = practice_dataset.append(
            final_inputs.loc[:, practice_dataset_colnames]
        )

    # Now return the practice dataset
    return practice_dataset, obs_df, others_df, results_df, labs_only_df


def pull_extra_data(csns, engine):
    # Now pull some additional data to join to this
    data_pull = sql_query_from_file("Extra_data_for_model.sql", verbose=False)

    # Process IDs into useable string
    formatted_csns = "'" + str(csns[0]) + "'"
    for i in csns[1:]:
        formatted_csns = formatted_csns + ", " + "'" + str(i) + "'"

    formatted_data_pull = data_pull.format(csns=formatted_csns)
    return pd.read_sql(formatted_data_pull, engine)
