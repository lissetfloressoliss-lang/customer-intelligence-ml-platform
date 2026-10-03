"""Load a trusted serving artifact once, honoring MODEL_PATH and project paths."""

import hashlib
import os
import warnings
from pathlib import Path

from sklearn.exceptions import InconsistentVersionWarning

from src.models import load_model
from src.utils.configuration import resolve_project_path


def load_serving_model(path: str | Path | None = None):
    """Return (pipeline, SHA256) from a trusted local path; reject sklearn mismatch.

    Args:
        path: Override of MODEL_PATH; default models/churn_pipeline.joblib.
    Returns:
        Loaded pipeline and file SHA256 for operational version verification.
    """
    source = resolve_project_path(
        path or os.environ.get("MODEL_PATH", "models/churn_pipeline.joblib")
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        model = load_model(source)
    return model, hashlib.sha256(source.read_bytes()).hexdigest()
