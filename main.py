"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.data import load_csv
from src.data.validation import validate_customer_data
from src.models import (
    load_model,
    predict_customers,
    save_training_artifacts,
    train_model,
)
from src.utils.configuration import load_parameters, resolve_project_path


def build_parser() -> argparse.ArgumentParser:
    """Create CLI arguments whose defaults come from the canonical YAML file."""
    parser = argparse.ArgumentParser(description="Customer churn MLE pipeline")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    train_parser = subparsers.add_parser("train")
    train_parser.add_argument("--params", type=Path, default=Path("params.yaml"))
    train_parser.add_argument(
        "--data",
        type=Path,
        required=True,
    )
    train_parser.add_argument(
        "--model-output",
        type=Path,
        default=None,
    )
    train_parser.add_argument(
        "--metrics-output",
        type=Path,
        default=None,
    )
    train_parser.add_argument(
        "--test-size",
        type=float,
        default=None,
    )
    train_parser.add_argument(
        "--seed",
        type=int,
        default=None,
    )

    predict_parser = subparsers.add_parser("predict")
    predict_parser.add_argument("--params", type=Path, default=Path("params.yaml"))
    predict_parser.add_argument(
        "--data",
        type=Path,
        required=True,
    )
    predict_parser.add_argument(
        "--model",
        type=Path,
        required=True,
    )
    predict_parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    predict_parser.add_argument(
        "--threshold",
        type=float,
        default=None,
    )

    return parser


def main() -> None:
    """Validate inputs and execute training or inference with YAML defaults."""
    args = build_parser().parse_args()
    params = load_parameters(args.params)
    dataframe = load_csv(resolve_project_path(args.data))
    validate_customer_data(dataframe, require_target=args.command == "train")

    if args.command == "train":
        result = train_model(
            dataframe,
            test_size=args.test_size
            if args.test_size is not None
            else params["training"]["test_size"],
            random_state=args.seed
            if args.seed is not None
            else params["training"]["random_state"],
            algorithm=params["model"]["algorithm"],
            max_iter=params["model"]["max_iter"],
            class_weight=params["model"]["class_weight"],
        )
        save_training_artifacts(
            result,
            resolve_project_path(args.model_output or params["paths"]["model"]),
            resolve_project_path(args.metrics_output or params["paths"]["metrics"]),
        )
        print(result.metrics)
        return

    model = load_model(resolve_project_path(args.model))
    predictions = predict_customers(
        model,
        dataframe,
        threshold=args.threshold
        if args.threshold is not None
        else params["prediction"]["threshold"],
    )

    args.output = resolve_project_path(args.output or params["paths"]["predictions"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(args.output, index=False)
    print(args.output)


if __name__ == "__main__":
    main()
