"""Compare business costs on the exact reserved split, never on training rows."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from sklearn.metrics import confusion_matrix, precision_score, recall_score
from sklearn.model_selection import train_test_split

from src.data import load_customer_data
from src.features.preprocessing import split_features_target
from src.models import load_model
from src.utils.configuration import load_parameters, resolve_project_path


def main() -> None:
    """Verify train-only scaling and persist a comparison for 0.50 and 0.45."""
    params = load_parameters()
    dataframe = load_customer_data(params["paths"]["raw_data"])
    features, target = split_features_target(dataframe)
    X_train, X_test, _, y_test = train_test_split(
        features,
        target,
        test_size=params["training"]["test_size"],
        random_state=params["training"]["random_state"],
        stratify=target,
    )
    model = load_model(resolve_project_path(params["paths"]["model"]))
    numeric = model.named_steps["preprocessor"].named_transformers_["numeric"]
    imputed = numeric.named_steps["imputer"].transform(
        X_train.loc[:, numeric.feature_names_in_]
    )
    np.testing.assert_allclose(
        numeric.named_steps["scaler"].mean_, imputed.mean(axis=0)
    )
    assert numeric.named_steps["scaler"].n_samples_seen_ == len(X_train)
    assert not set(X_train.index) & set(X_test.index)
    probabilities = model.predict_proba(X_test)[:, 1]
    rows = []
    for threshold in (0.50, 0.45):
        predictions = (probabilities >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, predictions, labels=[0, 1]).ravel()
        rows.append(
            {
                "threshold": threshold,
                "recall": float(recall_score(y_test, predictions, zero_division=0)),
                "precision": float(
                    precision_score(y_test, predictions, zero_division=0)
                ),
                "TP": int(tp),
                "TN": int(tn),
                "FP": int(fp),
                "FN": int(fn),
                "cost": int(50 * fp + 500 * fn),
            }
        )
    result = {
        "train_rows": len(X_train),
        "evaluation_rows": len(X_test),
        "random_state": params["training"]["random_state"],
        "evaluation_customer_ids": dataframe.loc[X_test.index, "customer_id"].tolist(),
        "preprocessing_train_only_verified": True,
        "comparison": rows,
        "limitation": "Single synthetic reserved split; threshold comparison is not independent final validation.",
    }
    output = resolve_project_path("reports/metrics/threshold_comparison.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "evaluation_customer_ids"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
