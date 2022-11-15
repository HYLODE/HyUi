# Ignore xgboost import, it's required for pickled file
import xgboost  # noqa: F401
import pickle
import pandas as pd
from pathlib import Path
import os
import re
import sched
import time
from sqlalchemy import create_engine
from functions import run_pipeline  # type: ignore
from web.config import get_settings


def get_emapdb_engine():
    get_settings().star_dsn
    return create_engine(get_settings().star_dsn)


def get_predictions(dataset):
    # Load the model and shap model
    with open("final_model.pkl", "rb") as f:
        model = pickle.load(f)

    # Remove columns with 'ward' in them (these may cause model drift)
    ward_columns = [i for i in dataset.columns if re.match(".*_ward$", i)]
    ward_columns.extend(["icu_admission"])
    cols_for_use = [i for i in dataset.columns if i not in ward_columns]

    # Make our predictions
    predictions = model.predict_proba(dataset.loc[:, cols_for_use])[:, 1]

    return dict(zip(dataset.index.map(str), predictions))


def write_predictions(predictions_map):
    generated_data_folder_path = Path(f"{Path(__file__).parent}/generated_data")

    if not generated_data_folder_path.is_dir():
        os.makedirs(generated_data_folder_path)

    with open(
        f"{generated_data_folder_path}/id_to_admission_prediction.pkl", "wb"
    ) as f:
        print("Pickling predictions map")
        pickle.dump(predictions_map, f)


def run_prediction_pipeline(db_engine, scheduler, interval):
    # most return variables unused for our use case
    dataset, _, _, _, _ = run_pipeline(
        list([pd.to_datetime("now").date()]), db_engine, now=True
    )

    predictions_map = get_predictions(dataset)
    write_predictions(predictions_map)

    scheduler.enter(
        interval, 1, run_prediction_pipeline, (db_engine, scheduler, interval)
    )


if __name__ == "__main__":
    # functions.py relies on specific, relative paths
    dir_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(dir_path)

    scheduler = sched.scheduler(time.time, time.sleep)

    emapdb_engine = get_emapdb_engine()

    run_prediction_pipeline(emapdb_engine, scheduler, interval=1800)

    scheduler.run()
