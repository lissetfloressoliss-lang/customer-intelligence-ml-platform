"""Serving regression tests with freshly trained local pipeline artifacts."""

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from src.features.preprocessing import get_feature_schema
from src.models import predict_customers, save_training_artifacts, train_model


@pytest.fixture(scope="module")
def serving_artifact(tmp_path_factory):
    folder = tmp_path_factory.mktemp("serving")
    from src.data import load_customer_data

    result = train_model(load_customer_data())
    path = folder / "pipeline.joblib"
    save_training_artifacts(result, path, folder / "metrics.json")
    return path, result.pipeline


@pytest.fixture
def client(serving_artifact):
    with TestClient(create_app(serving_artifact[0])) as instance:
        yield instance


def input_record(dataframe):
    columns = ["customer_id", *get_feature_schema().model_features]
    row = dataframe.loc[:, columns].iloc[0].astype(object)
    return row.where(pd.notna(row), None).to_dict()


def test_health_and_prediction_match_pipeline(
    client, serving_artifact, customer_dataframe
):
    assert client.get("/health").json()["status"] == "healthy"
    assert client.get("/health").json()["threshold"] == 0.45
    response = client.post("/predict", json=input_record(customer_dataframe))
    assert response.status_code == 200
    expected = predict_customers(
        serving_artifact[1], customer_dataframe.head(1), threshold=0.45
    ).iloc[0]
    assert response.json()["churn_probability"] == pytest.approx(
        expected.churn_probability
    )
    assert response.json()["churn_prediction"] == int(expected.churn_prediction)
    assert client.get("/openapi.json").status_code == 200


def test_explicit_nulls_are_imputed(client, serving_artifact, customer_dataframe):
    row = input_record(customer_dataframe)
    row["age"] = None
    row["region"] = None
    response = client.post("/predict", json=row)
    expected = predict_customers(
        serving_artifact[1],
        pd.DataFrame([row]).where(pd.notna(pd.DataFrame([row])), np.nan),
        threshold=0.45,
    )
    assert response.status_code == 200
    assert response.json()["churn_probability"] == pytest.approx(
        expected.iloc[0].churn_probability
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("age", -1),
        ("contract_type", "Unknown"),
        ("monthly_fee", -1),
        ("digital_usage_score", 101),
    ],
)
def test_invalid_input(client, customer_dataframe, field, value):
    row = input_record(customer_dataframe)
    row[field] = value
    assert client.post("/predict", json=row).status_code == 422


def test_missing_feature_rejected(client, customer_dataframe):
    row = input_record(customer_dataframe)
    del row["marketing_score"]
    assert client.post("/predict", json=row).status_code == 422


def test_batch_matches_pipeline(client, serving_artifact, customer_dataframe):
    frame = customer_dataframe.head(10)
    response = client.post(
        "/predict/batch/csv",
        files={
            "file": (
                "customers.csv",
                frame.to_csv(index=False).encode("utf-8"),
                "text/csv",
            )
        },
    )
    assert response.status_code == 200
    expected = predict_customers(serving_artifact[1], frame, threshold=0.45)
    np.testing.assert_allclose(
        [r["churn_probability"] for r in response.json()], expected.churn_probability
    )


@pytest.mark.parametrize(
    "filename,content,status",
    [
        ("bad.txt", b"x", 400),
        ("empty.csv", b"", 400),
        ("headers.csv", b"customer_id,age\n", 400),
        ("missing.csv", b"customer_id,age\nNT-1,20\n", 422),
    ],
)
def test_bad_csv(client, filename, content, status):
    assert (
        client.post(
            "/predict/batch/csv", files={"file": (filename, content)}
        ).status_code
        == status
    )


def test_batch_row_limit(client, customer_dataframe, monkeypatch):
    monkeypatch.setattr("api.main.MAX_BATCH_ROWS", 2)
    csv = customer_dataframe.head(3).to_csv(index=False).encode("utf-8")
    assert (
        client.post(
            "/predict/batch/csv", files={"file": ("customers.csv", csv)}
        ).status_code
        == 413
    )


def test_metrics_record_actual_predictions(client, customer_dataframe):
    assert (
        client.post("/predict", json=input_record(customer_dataframe)).status_code
        == 200
    )
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "churn_predictions_total" in metrics.text
    assert "churn_prediction_latency_seconds_count 1.0" in metrics.text
    assert "churn_input_payment_delay_count 1.0" in metrics.text
    assert "NT-000001" not in metrics.text


def test_missing_artifact_fails_startup(tmp_path):
    with (
        pytest.raises(FileNotFoundError),
        TestClient(create_app(tmp_path / "missing.joblib")),
    ):
        pass


def test_incompatible_sklearn_fails_startup(serving_artifact, monkeypatch):
    import warnings

    from sklearn.exceptions import InconsistentVersionWarning

    def incompatible_load(path):
        warnings.warn(
            InconsistentVersionWarning(
                estimator_name="Pipeline",
                current_sklearn_version="1.9.1",
                original_sklearn_version="1.9.0",
            )
        )

    monkeypatch.setattr("api.dependencies.load_model", incompatible_load)
    with (
        pytest.raises(InconsistentVersionWarning),
        TestClient(create_app(serving_artifact[0])),
    ):
        pass


def test_duplicate_batch_ids_rejected(client, customer_dataframe):
    frame = customer_dataframe.head(2).copy()
    frame["customer_id"] = "NT-duplicate"
    response = client.post(
        "/predict/batch/csv",
        files={"file": ("customers.csv", frame.to_csv(index=False).encode("utf-8"))},
    )
    assert response.status_code == 422


def test_json_batch_and_aliases(client, customer_dataframe):
    row = input_record(customer_dataframe)
    row["payment_delay"] = row.pop("last_payment_delay")
    row["digital_usage"] = row.pop("digital_usage_score")
    response = client.post("/predict/batch", json=[row])
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert client.post("/predict/batch", json=[]).status_code == 422


def test_guide_four_fields_do_not_fabricate_features(client):
    response = client.post(
        "/predict",
        json={
            "monthly_fee": 100,
            "support_calls": 2,
            "payment_delay": 5,
            "digital_usage": 50,
        },
    )
    assert response.status_code == 422


def test_guide_metrics_have_correct_types(client, customer_dataframe):
    from prometheus_client.parser import text_string_to_metric_families

    assert (
        client.post("/predict", json=input_record(customer_dataframe)).status_code
        == 200
    )
    families = {
        m.name: m for m in text_string_to_metric_families(client.get("/metrics").text)
    }
    assert families["churn_probability"].type == "gauge"
    for name in ["monthly_fee", "support_calls", "payment_delay", "digital_usage"]:
        assert families["churn_input_" + name].type == "histogram"


def test_atomic_rollback_preserves_backup_and_archives_active(
    serving_artifact, tmp_path
):
    import hashlib
    import shutil

    from scripts.rollback_model import rollback

    backup = tmp_path / "v1.joblib"
    active = tmp_path / "active.joblib"
    shutil.copy2(serving_artifact[0], backup)
    active.write_bytes(b"broken-v2")
    expected = hashlib.sha256(backup.read_bytes()).hexdigest()
    result = rollback(backup, active)
    assert result["restored_sha256"] == expected
    assert hashlib.sha256(active.read_bytes()).hexdigest() == expected
    assert hashlib.sha256(backup.read_bytes()).hexdigest() == expected
    assert active.with_name(result["archive"]).read_bytes() == b"broken-v2"
