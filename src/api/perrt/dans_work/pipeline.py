### D Stein ICU Prediction Processing Pipeline


from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
from pprint import pprint
import urllib

import arrow
import matplotlib.pyplot as plt
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

from xgboost import XGBClassifier

# Import my fuctions
from functions import (
    argmax_time,
    test_function,
    sql_query_from_file,
    FlexibleSqlQuery,
    linear_slope,
    run_pipeline,
    pull_extra_data,
)

test_function()

# Prepare sql connection
try:
    uds_user, uds_passwd = Path(os.getcwd() + "/secret").read_text().strip().split("\n")
    uds_host = "UCLVLDDDTAEPS02"
    uds_name = "uds"
    uds_port = "5432"
except FileNotFoundError:
    print("You need a credential file named secret")

try:
    emapdb_engine = create_engine(
        f"postgresql://{uds_user}:{uds_passwd}@{uds_host}:{uds_port}/{uds_name}"
    )
    print("Sucessfully connected to EMAP")
except ConnectionRefusedError:
    print("Unable to connect to EMAP")


# Read the last time this was run - if unable to find the file make a file with an old time of running
try:
    f = open("saved_data/last_run.txt", "r")
    last_run = pd.to_datetime(f.read())
except:
    f = open("saved_data/last_run.txt", "w+")
    old_time = "2022-04-26 13:20:53.250748"
    f.write(old_time)
    f.close()
    last_run = pd.to_datetime(old_time)

# If the lastrun file is corrupted then:
try:
    rerun = pd.to_datetime("now") - last_run > pd.to_timedelta("0 days 00:15:00")
except:
    rerun = True

# Only run if last run was >15 minutes ago
if rerun:

    try:
        print(
            f"Last run was greater than than 15 minutes ago, at {str(last_run)}: rerunning now"
        )

    except:
        print(f"Last run file unavailable or corrupted, rerunning pipeline now")

    # Run the pipeline
    practice_dataset, obs_df, others_df, results_df, labs_only_df = run_pipeline(
        list([pd.to_datetime("now").date()]), emapdb_engine, now=True
    )
    extra_data = pull_extra_data(practice_dataset.index, emapdb_engine)

    # Save these files
    practice_dataset.to_csv("saved_data/practice_dataset.csv")
    obs_df.to_csv("saved_data/obs_df.csv")
    others_df.to_csv("saved_data/others_df.csv")
    results_df.to_csv("saved_data/results_df.csv")
    labs_only_df.to_csv("saved_data/labs_only_df.csv")
    extra_data.to_csv("saved_data/extra_data.csv")

    # Save the time that was run
    f = open("saved_data/last_run.txt", "w+")
    f.write(str(pd.to_datetime("now")))
    f.close()

    print(f'Rerun now finished at {str(pd.to_datetime("now"))}, closing')

else:
    # Read in practice dataset so we can run the extra data pull
    print(
        f"Last run was less than 15 minutes ago, at {str(last_run)}: rerunning only extra data"
    )

    practice_dataset = pd.read_csv("saved_data/practice_dataset.csv")
    extra_data = pull_extra_data(practice_dataset.index, emapdb_engine)
    extra_data.to_csv("saved_data/extra_data.csv")

    print(f'Extra data now saved at {str(pd.to_datetime("now"))}, closing')
