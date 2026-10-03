"""Send complete synthetic NovaTel records and report measured scenario results."""

import argparse
import json
import time
import urllib.request

import numpy as np
import pandas as pd

from api.schemas import CustomerInput
from src.features.preprocessing import get_feature_schema
from src.utils.configuration import resolve_project_path


def simulate(url: str, scenario: str, rows: int = 50, interval: float = 0.8) -> dict:
    """Send deterministic baseline or modified inputs; never infer concept drift.

    Args:
        url: API base URL supplied by the operator.
        scenario: normal or drift, both using the same sampled baseline records.
        rows: Number of requests per scenario.
        interval: Seconds between requests for Prometheus sampling.
    Returns:
        Observed input/output means and successful response counts.
    """
    frame = pd.read_csv(resolve_project_path("data/raw/customer_churn.csv"))
    frame = frame.sample(n=rows, random_state=2026).copy()
    if scenario == "drift":
        frame["monthly_fee"] *= 1.7
        frame["support_calls"] += 5
        frame["last_payment_delay"] += 25
        frame["digital_usage_score"] *= 0.4
    elif scenario != "normal":
        raise ValueError("scenario must be normal or drift")
    cols = ["customer_id", *get_feature_schema().model_features]
    records = (
        frame[cols]
        .astype(object)
        .where(pd.notna(frame[cols]), None)
        .to_dict(orient="records")
    )
    probabilities = []
    for row in records:
        customer = CustomerInput.model_validate(row)
        request = urllib.request.Request(
            url.rstrip("/") + "/predict",
            data=json.dumps(customer.model_dump(), allow_nan=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
        probabilities.append(result["churn_probability"])
        time.sleep(interval)
    result = {
        "scenario": scenario,
        "successful_requests": len(probabilities),
        "seed": 2026,
        "input_means": {
            c: float(frame[c].mean())
            for c in [
                "monthly_fee",
                "support_calls",
                "last_payment_delay",
                "digital_usage_score",
            ]
        },
        "mean_churn_probability": float(np.mean(probabilities)),
        "limitation": "Synthetic perturbation; no independent ground truth or concept-drift conclusion.",
    }
    path = resolve_project_path(f"reports/metrics/traffic_{scenario}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    """Parse simulation options and print only measured scenario results."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--scenario", choices=["normal", "drift", "both"], default="both"
    )
    parser.add_argument("--rows", type=int, default=50)
    parser.add_argument("--interval", type=float, default=0.8)
    args = parser.parse_args()
    if args.rows < 1 or args.rows > 1000 or args.interval < 0:
        parser.error("Invalid rows or interval")
    scenarios = ["normal", "drift"] if args.scenario == "both" else [args.scenario]
    for scenario in scenarios:
        print(
            json.dumps(simulate(args.url, scenario, args.rows, args.interval), indent=2)
        )


if __name__ == "__main__":
    main()
