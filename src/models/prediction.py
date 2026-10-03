"""Prediction utilities."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from src.features.preprocessing import select_inference_features


def load_model(
    model_path: str | Path,
) -> Pipeline:
    """Load a trusted local joblib classifier; reject missing or incompatible artifacts.

    Args:
        model_path: Path to the trusted persisted pipeline.

    Returns:
        Restored classifier pipeline with a predict_proba method.
    """
    path = Path(model_path)

    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}")

    model = joblib.load(path)

    if not hasattr(model, "predict_proba"):
        raise TypeError("Loaded artifact is not a compatible classifier.")

    return model


def predict_customers(
    model: Pipeline,
    dataframe: pd.DataFrame,
    *,
    threshold: float = 0.50,
) -> pd.DataFrame:
    """Return customer IDs, probabilities and binary predictions at the threshold.

    Args:
        model: Fitted pipeline exposing predict_proba.
        dataframe: Customer rows with the required feature columns.
        threshold: Positive-class decision threshold strictly between zero and one.

    Returns:
        DataFrame of probabilities, thresholded labels and optional customer IDs.
    """
    if not 0.0 < threshold < 1.0:
        raise ValueError("threshold must be between 0 and 1.")

    features = select_inference_features(dataframe)
    probabilities = model.predict_proba(features)[:, 1]
    predictions = (probabilities >= threshold).astype(int)

    output = pd.DataFrame(
        {
            "churn_probability": probabilities,
            "churn_prediction": predictions,
        },
        index=dataframe.index,
    )

    if "customer_id" in dataframe.columns:
        output.insert(
            0,
            "customer_id",
            dataframe["customer_id"].values,
        )

    return output
