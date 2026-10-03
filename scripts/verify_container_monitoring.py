"""Verify real Compose metrics/alerts and rollback; persist only observed results."""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.rollback_model import rollback
from simulate_traffic import simulate
from src.utils.configuration import resolve_project_path


def get(url: str) -> dict:
    """Read a JSON endpoint with a timeout; propagate failures instead of inventing output."""
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def main():
    """Run both traffic scenarios against actual Compose services and verify reload."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--prometheus-url", default="http://127.0.0.1:9090")
    args = parser.parse_args()
    health = get(args.api_url + "/health")
    normal = simulate(args.api_url, "normal", 50, 0.8)
    targets = get(args.prometheus_url + "/api/v1/targets")["data"]["activeTargets"]
    assert any(t["health"] == "up" for t in targets), "No UP target"
    normal_alerts = get(args.prometheus_url + "/api/v1/alerts")["data"]["alerts"]
    assert not any(
        a["labels"].get("alertname") == "HighAveragePaymentDelay" for a in normal_alerts
    ), "NORMAL unexpectedly alerted"
    print("NORMAL: target UP, no payment delay alert", flush=True)
    drift = simulate(args.api_url, "drift", 50, 0.8)
    firing = None
    for _ in range(10):
        alerts = get(args.prometheus_url + "/api/v1/alerts")["data"]["alerts"]
        candidates = [
            a
            for a in alerts
            if a["labels"].get("alertname") == "HighAveragePaymentDelay"
            and a["state"] == "firing"
        ]
        if candidates:
            firing = candidates[0]
            break
        time.sleep(1)
    assert firing is not None, "No FIRING alert observed"
    backup = resolve_project_path("models/churn_pipeline_v1.joblib")
    active = resolve_project_path("models/churn_pipeline.joblib")
    restored = rollback(backup, active)
    subprocess.run(["docker", "compose", "restart", "api"], check=True)
    final_health = None
    for _ in range(60):
        try:
            candidate = get(args.api_url + "/health")
            if candidate.get("model_sha256") == restored["restored_sha256"]:
                final_health = candidate
                break
        except OSError:
            pass
        time.sleep(1)
    assert final_health is not None, "API did not reload stable model"
    report = {
        "runtime": "Actual Docker Compose containers",
        "initial_health": health,
        "normal": normal,
        "drift": drift,
        "normal_alerts": normal_alerts,
        "observed_alert": firing,
        "target_up": True,
        "rollback": restored,
        "health_after_container_restart": final_health,
        "backup_same_as_initial": health["model_sha256"]
        == final_health["model_sha256"],
        "cloud_deployed": False,
        "performance_degradation_proven": False,
    }
    output = resolve_project_path("reports/metrics/container_verification.json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        "DRIFT: FIRING observed; container restart healthy with stable model hash",
        flush=True,
    )


if __name__ == "__main__":
    main()
