"""Training pipeline for churn classification."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.features.preprocessing import (
    build_preprocessing_pipeline,
    split_features_target,
)
from src.models.evaluation import evaluate_binary_classifier


@dataclass(frozen=True)
class TrainingResult:
    pipeline: Pipeline
    metrics: dict[str, float]
    train_rows: int
    test_rows: int


def build_training_pipeline(
    *,
    random_state: int = 42,
    algorithm: str = "logistic_regression",
    max_iter: int = 1000,
    class_weight: str | None = "balanced",
) -> Pipeline:
    """Build an unfitted pipeline; preprocessing is fitted during training only.

    Args:
        random_state: Seed for splitting or the classifier.
        algorithm: Supported algorithm: logistic_regression.
        max_iter: Maximum logistic regression optimization iterations.
        class_weight: Classifier class weights; balanced or None.

    Returns:
        Unfitted Pipeline combining preprocessing and logistic regression.
    """
    if algorithm != "logistic_regression":
        raise ValueError(f"Unsupported model algorithm: {algorithm}")
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessing_pipeline()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=max_iter,
                    class_weight=class_weight,
                    random_state=random_state,
                ),
            ),
        ]
    )


def train_model(
    dataframe: pd.DataFrame,
    *,
    test_size: float = 0.20,
    random_state: int = 42,
    algorithm: str = "logistic_regression",
    max_iter: int = 1000,
    class_weight: str | None = "balanced",
) -> TrainingResult:
    """Split before fitting and evaluate on a stratified reserved test set.

    Args:
        dataframe: Customer rows with the required feature columns.
        test_size: Fraction reserved for evaluation before any fitting.
        random_state: Seed for splitting or the classifier.
        algorithm: Supported algorithm: logistic_regression.
        max_iter: Maximum logistic regression optimization iterations.
        class_weight: Classifier class weights; balanced or None.

    Returns:
        TrainingResult containing fitted pipeline, reserved-set metrics and split sizes.
    """
    features, target = split_features_target(dataframe)

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=random_state,
        stratify=target,
    )

    pipeline = build_training_pipeline(
        random_state=random_state,
        algorithm=algorithm,
        max_iter=max_iter,
        class_weight=class_weight,
    )
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    probabilities = pipeline.predict_proba(X_test)[:, 1]

    metrics = evaluate_binary_classifier(
        y_test,
        predictions,
        probabilities,
    )

    return TrainingResult(
        pipeline=pipeline,
        metrics=metrics,
        train_rows=len(X_train),
        test_rows=len(X_test),
    )


def save_training_artifacts(
    result: TrainingResult,
    model_path: str | Path,
    metrics_path: str | Path,
) -> None:
    """Persist the complete fitted pipeline and evaluation metrics; return None.

    Args:
        result: Training result containing the fitted pipeline and metrics.
        model_path: Path to the trusted persisted pipeline.
        metrics_path: Output JSON path; parent folders are created.

    Returns:
        None; writes the fitted pipeline and JSON metrics to disk.
    """
    model_path = Path(model_path)
    metrics_path = Path(metrics_path)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(result.pipeline, model_path)

    metrics_path.write_text(
        json.dumps(
            {
                "metrics": result.metrics,
                "train_rows": result.train_rows,
                "test_rows": result.test_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
