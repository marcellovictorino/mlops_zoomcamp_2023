"""
Example retrieving model from PRODUCTION and using it to make predictions
"""
from dataclasses import dataclass


@dataclass
class MLFlowStages:
    PRODUCTION: str = "PRODUCTION"
    STAGING: str = "STAGING"
    ARCHIVE: str = "ARCHIVE"
    NULL = None


MODEL_NAME = ""
MODEL_STAGE: str = MLFlowStages.PRODUCTION

import mlflow

# From mlflow code example
model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/{MODEL_STAGE}")
y_pred = model.predict(X_test)

# Retrieving artifact and deserializing
from mlflow.tracking import MlflowClient

MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

client.download_artifacts(run_id=run_id, path="preprocessor", dst_path=".")

import pickle

# TODO: does it mean we need to know the exact name the artifact was stored?
with open("preprocessor/preprocessor.b", "rb") as f_in:
    dv = pickle.load(f_in)
