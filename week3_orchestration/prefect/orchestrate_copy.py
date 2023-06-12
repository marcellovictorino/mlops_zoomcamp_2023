import pickle
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import mlflow
import numpy as np
import pandas as pd
import scipy
from prefect import flow, task
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

# MLflow settings
EXPERIMENT_NAME = "linear_regression"
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(EXPERIMENT_NAME)


@task(retries=3, retry_delay_seconds=2)
def process_data(
    parquet_filename: str, vectorizer=None
) -> Tuple[scipy.sparse._csr.csr_matrix, np.ndarray, Optional[DictVectorizer]]:
    df = pd.read_parquet(parquet_filename)
    df["duration"] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    df.duration = df.duration.apply(lambda td: td.total_seconds() / 60)

    df_clean = df[(df.duration >= 1) & (df.duration <= 60)]
    categorical = ["PULocationID", "DOLocationID"]
    df_clean[categorical] = df_clean[categorical].astype(str)
    df_train = df_clean[categorical]
    train_dicts = df_train.to_dict(orient="records")

    if not vectorizer:
        # dictionary vectorizer not provided, treat as training job
        vectorizer = DictVectorizer()
        X_train = vectorizer.fit_transform(train_dicts)
    else:
        # dictionary vectorizer provided, treat as validation job
        X_train = vectorizer.transform(train_dicts)

    target = "duration"
    y_train = df_clean[target].values

    return X_train, y_train, vectorizer


@task(log_prints=True)
def train_model(
    X_train: scipy.sparse._csr.csr_matrix,
    X_test: scipy.sparse._csr.csr_matrix,
    y_train: np.ndarray,
    y_test: np.ndarray,
    dv: DictVectorizer,
) -> None:
    """train a model and write everything out"""

    with mlflow.start_run():
        # Enable auto logging
        mlflow.sklearn.autolog()

        lr = LinearRegression()
        lr.fit(X_train, y_train)

        y_pred = lr.predict(X_test)

        rmse = mean_squared_error(y_test, y_pred, squared=False)
        print(f"Model RMSE: {rmse:.3f}")
        mlflow.log_metric("rmse", rmse)

        # No params to explicitly log
        # mlflow.log_params(best_params)

        # Already captured by autolog
        # mlflow.sklearn.log_model(lr, artifact_path="models")

        # Avoid storing files locally
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "preprocessor.b"
            with open(file_path, "wb") as fh:
                pickle.dump(dv, fh)
                mlflow.log_artifact(file_path.as_posix(), artifact_path="artifacts")


@flow(name="taxi_ride_train", log_prints=True)
def main_flow(
    train_path: str,
    test_path: str,
) -> None:
    """The main training pipeline"""

    # Load
    X_train, y_train, dv_train = process_data(parquet_filename=train_path)
    X_test, y_test, _ = process_data(parquet_filename=test_path, vectorizer=dv_train)

    # Train
    train_model(
        X_train=X_train, X_test=X_test, y_train=y_train, y_test=y_test, dv=dv_train
    )


if __name__ == "__main__":
    Path().as_posix()
    data_source_folder = Path(__file__).parents[2] / Path("source_data")
    train_path = data_source_folder / Path("yellow_tripdata_2022-01.parquet")
    test_path = data_source_folder / Path("yellow_tripdata_2022-02.parquet")

    print(train_path)

    main_flow(train_path=train_path.as_posix(), test_path=test_path.as_posix())
