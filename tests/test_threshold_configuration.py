"""Verify YAML inference defaults and explicit CLI threshold precedence."""

import subprocess
import sys

import pandas as pd
import yaml

from src.models import save_training_artifacts, train_model
from src.utils.configuration import load_parameters
from src.utils.paths import PROJECT_ROOT


def test_prediction_yaml_and_cli_override(customer_dataframe, tmp_path):
    result = train_model(customer_dataframe)
    model = tmp_path / "model.joblib"
    save_training_artifacts(result, model, tmp_path / "metrics.json")
    params = load_parameters()
    params["prediction"]["threshold"] = 0.45
    params["paths"]["predictions"] = str(tmp_path / "yaml.csv")
    config = tmp_path / "params.yaml"
    config.write_text(yaml.safe_dump(params), encoding="utf-8")
    command = [
        sys.executable,
        str(PROJECT_ROOT / "main.py"),
        "predict",
        "--data",
        "data/raw/customer_churn.csv",
        "--model",
        str(model),
        "--params",
        str(config),
    ]
    subprocess.run(command, cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        command + ["--threshold", "0.50", "--output", str(tmp_path / "cli.csv")],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    for path, threshold in (("yaml.csv", 0.45), ("cli.csv", 0.50)):
        predictions = pd.read_csv(tmp_path / path)
        expected = (predictions.churn_probability >= threshold).astype(int)
        pd.testing.assert_series_equal(
            predictions.churn_prediction,
            expected,
            check_names=False,
        )
