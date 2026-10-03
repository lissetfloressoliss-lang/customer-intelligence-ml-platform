"""FastAPI serving using the unchanged Curso 1 persisted pipeline."""

import io
import logging
import time
import warnings
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import ValidationError
from sklearn.exceptions import InconsistentVersionWarning
from starlette.responses import Response

from api.schemas import CustomerInput, PredictionOutput
from src.features.preprocessing import get_feature_schema
from src.models import load_model, predict_customers
from src.utils.configuration import load_parameters, resolve_project_path

MAX_BATCH_ROWS = 50_000
MAX_BATCH_BYTES = 20 * 1024 * 1024
logger = logging.getLogger(__name__)


def create_app(model_path: str | Path | None = None) -> FastAPI:
    """Return an app with isolated metrics; load a trusted local model at startup.

    Args:
        model_path: Optional trusted local joblib path, resolved from project root.
    Returns:
        FastAPI instance with health, prediction, CSV batch and metrics endpoints.
    """
    registry = CollectorRegistry()
    count = Counter(
        "churn_predictions_total",
        "Successful predictions",
        ["class"],
        registry=registry,
    )
    latency = Histogram(
        "churn_prediction_latency_seconds", "Inference call latency", registry=registry
    )
    errors = Counter(
        "churn_prediction_errors_total", "Inference failures", registry=registry
    )
    delay = Histogram(
        "churn_input_last_payment_delay",
        "Observed payment delay days",
        buckets=(0, 5, 10, 15, 30, 60, 120),
        registry=registry,
    )
    scores = Histogram(
        "churn_probability",
        "Predicted score distribution",
        buckets=(0, 0.1, 0.25, 0.45, 0.5, 0.75, 0.9, 1),
        registry=registry,
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        """Load model before accepting requests; fail on incompatible sklearn versions."""
        params = load_parameters()
        threshold = float(params["prediction"]["threshold"])
        if not 0 < threshold < 1:
            raise ValueError("Invalid configured threshold")
        with warnings.catch_warnings():
            warnings.simplefilter("error", InconsistentVersionWarning)
            model = load_model(
                resolve_project_path(model_path or params["paths"]["model"])
            )
        if list(model.feature_names_in_) != list(get_feature_schema().model_features):
            raise ValueError("Model feature contract differs from schema")
        if list(model.classes_) != [0, 1]:
            raise ValueError("Expected classes [0,1]")
        application.state.model = model
        application.state.threshold = threshold
        yield
        application.state.model = None

    application = FastAPI(title="NovaTel Churn API", version="2.0.0", lifespan=lifespan)

    def infer(customers: list[CustomerInput]) -> list[dict]:
        """Infer validated rows and record observations without retaining customer IDs."""
        dataframe = pd.DataFrame([row.model_dump() for row in customers])
        dataframe = dataframe.where(pd.notna(dataframe), np.nan)
        start = time.perf_counter()
        try:
            result = predict_customers(
                application.state.model,
                dataframe,
                threshold=application.state.threshold,
            )
        except Exception as exc:
            errors.inc()
            logger.exception("Inference failed")
            raise HTTPException(500, "Inference failed") from exc
        finally:
            latency.observe(time.perf_counter() - start)
        for row in result.itertuples():
            count.labels(**{"class": str(row.churn_prediction)}).inc()
            scores.observe(row.churn_probability)
        for value in dataframe.last_payment_delay:
            delay.observe(float(value))
        return result.to_dict(orient="records")

    @application.get("/health")
    def health() -> dict:
        """Return readiness only after the model loaded successfully."""
        if getattr(application.state, "model", None) is None:
            raise HTTPException(503, "Model unavailable")
        return {"status": "healthy", "threshold": application.state.threshold}

    @application.post("/predict", response_model=PredictionOutput)
    def predict(customer: CustomerInput) -> dict:
        """Return one prediction using persisted preprocessing and classifier."""
        return infer([customer])[0]

    @application.post("/predict/batch", response_model=list[PredictionOutput])
    def predict_batch(file: UploadFile) -> list[dict]:
        """Predict a validated UTF-8 CSV, capped at 50000 rows and 20 MiB."""
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(400, "Upload a CSV file")
        content = file.file.read(MAX_BATCH_BYTES + 1)
        if len(content) > MAX_BATCH_BYTES:
            raise HTTPException(413, "CSV exceeds 20 MiB")
        try:
            frame = pd.read_csv(
                io.BytesIO(content),
                nrows=MAX_BATCH_ROWS + 1,
                dtype={"customer_id": str},
                encoding="utf-8-sig",
            )
        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError,
        ) as exc:
            raise HTTPException(400, "Empty or invalid UTF-8 CSV") from exc
        if frame.empty:
            raise HTTPException(400, "CSV has no rows")
        if len(frame) > MAX_BATCH_ROWS:
            raise HTTPException(413, "CSV exceeds 50000 rows")
        columns = ["customer_id", *get_feature_schema().model_features]
        missing = set(columns) - set(frame.columns)
        if missing:
            raise HTTPException(422, {"missing_columns": sorted(missing)})
        if frame.customer_id.duplicated().any():
            raise HTTPException(422, "Duplicate customer_id values")
        selected = frame.loc[:, columns].astype(object)
        records = selected.where(pd.notna(selected), None).to_dict(orient="records")
        try:
            customers = [CustomerInput.model_validate(row) for row in records]
        except ValidationError as exc:
            raise HTTPException(422, "CSV contains invalid feature values") from exc
        return infer(customers)

    @application.get("/metrics")
    def metrics() -> Response:
        """Expose process-local counters and histograms in Prometheus format."""
        return Response(
            generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST}
        )

    return application


app = create_app()
