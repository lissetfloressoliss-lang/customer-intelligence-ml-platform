FROM python:3.12-slim
WORKDIR /app
COPY requirements-api-lock.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements-api-lock.txt
COPY api ./api
COPY src ./src
COPY pyproject.toml params.yaml ./
COPY models/churn_pipeline.joblib models/churn_pipeline_v1.joblib ./models/
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
