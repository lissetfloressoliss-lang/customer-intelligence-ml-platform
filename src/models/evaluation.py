"""Binary classification evaluation utilities."""

from __future__ import annotations

from typing import Any

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_binary_classifier(
    y_true: Any,
    y_pred: Any,
    y_proba: Any,
) -> dict[str, float]:
    """Return accuracy, precision, recall, F1 and ROC AUC for binary outputs.

    Args:
        y_true: Observed binary labels.
        y_pred: Predicted binary labels.
        y_proba: Positive-class probabilities.

    Returns:
        Dictionary of five binary classification metrics as floats.
    """
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
    }
