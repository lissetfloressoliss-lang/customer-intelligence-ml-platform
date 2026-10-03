"""Prepare validated serving and stable backup copies from the Curso 1 artifact."""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.dependencies import load_serving_model
from src.utils.configuration import resolve_project_path


def main():
    """Create missing serving copies; preserve an existing stable backup."""
    source = resolve_project_path("artifacts/models/churn_pipeline.joblib")
    _, digest = load_serving_model(source)
    directory = resolve_project_path("models")
    directory.mkdir(exist_ok=True)
    for name in ["churn_pipeline.joblib", "churn_pipeline_v1.joblib"]:
        target = directory / name
        if not target.exists():
            shutil.copy2(source, target)
        _, target_hash = load_serving_model(target)
        if target_hash != digest:
            raise ValueError(f"Existing {name} differs; choose versions explicitly")
    (directory / "manifest.json").write_text(
        json.dumps(
            {
                "baseline_sha256": digest,
                "backup": "churn_pipeline_v1.joblib",
                "active": "churn_pipeline.joblib",
                "backup_origin": "Copy of validated Curso 1 artifact; same model, not an independent retrained version.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Validated active and backup model copies; existing files preserved.")


if __name__ == "__main__":
    main()
