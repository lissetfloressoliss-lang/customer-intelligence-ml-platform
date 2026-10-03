"""Regression tests for YAML wiring, path resolution and train-only preprocessing."""

import json
import subprocess
import sys

import joblib
import numpy as np
import yaml
from sklearn.model_selection import train_test_split

from src.features.preprocessing import split_features_target
from src.models import train_model
from src.utils.configuration import load_parameters
from src.utils.paths import PROJECT_ROOT


def test_cli_uses_yaml_from_another_directory(tmp_path):
    params = load_parameters()
    params["training"] = {"test_size": 0.30, "random_state": 17}
    params["model"]["max_iter"] = 321
    params["model"]["class_weight"] = None
    params["paths"]["model"] = str(tmp_path / "model.joblib")
    params["paths"]["metrics"] = str(tmp_path / "metrics.json")
    config = tmp_path / "params.yaml"
    config.write_text(yaml.safe_dump(params), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "main.py"),
            "train",
            "--data",
            "data/raw/customer_churn.csv",
            "--params",
            str(config),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    metrics = json.loads((tmp_path / "metrics.json").read_text())
    assert (metrics["train_rows"], metrics["test_rows"]) == (700, 300)
    model = joblib.load(tmp_path / "model.joblib")
    classifier = model.named_steps["classifier"]
    assert classifier.max_iter == 321
    assert classifier.random_state == 17
    assert classifier.class_weight is None


def test_preprocessing_fits_training_rows_only(customer_dataframe, tmp_path):
    features, target = split_features_target(customer_dataframe)
    train, test, _, _ = train_test_split(
        features,
        target,
        test_size=0.20,
        random_state=42,
        stratify=target,
    )
    result = train_model(customer_dataframe)
    path = tmp_path / "pipeline.joblib"
    joblib.dump(result.pipeline, path)
    restored = joblib.load(path)
    numeric = restored.named_steps["preprocessor"].named_transformers_["numeric"]
    values = numeric.named_steps["imputer"].transform(train[numeric.feature_names_in_])
    np.testing.assert_allclose(numeric.named_steps["scaler"].mean_, values.mean(axis=0))
    assert numeric.named_steps["scaler"].n_samples_seen_ == len(train)
    np.testing.assert_allclose(
        restored.predict_proba(test), result.pipeline.predict_proba(test)
    )
