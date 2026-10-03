> Estado histórico de implementación. Para el estado final, despliegue AWS y cierre, consultar [auditoría final](final_audit.md). Las afirmaciones anteriores sobre roles ausentes o AWS pendiente quedaron superadas por las evidencias posteriores.

# Módulo II: contraste con la guía y resultados propios

Guía recibida como texto adjunto el 3 de octubre de 2026. La base es el repositorio NovaTel existente y su pipeline persistido del Módulo I. Se conserva el modelo original en artifacts/models/; serving usa copias confiables en models/.

## Adaptaciones necesarias

| Guía | Implementación comprobada |
| --- | --- |
| Cuatro features en una lista posicional | Nuestro modelo exige 18 variables con nombres. Se usa el DataFrame completo; no se inventan las 14 faltantes. Los aliases payment_delay y digital_usage se traducen a last_payment_delay y digital_usage_score. Cuatro campos solos dan HTTP 422. |
| scikit-learn 1.9.0, joblib 1.3.2 y otras versiones docentes | El artefacto real usa sklearn 1.9.1, joblib 1.6.0, numpy 2.5.3 y scipy 1.18.1, que requieren Python >=3.12. Se fijan las versiones reales y transitivas en requirements-api-lock.txt (Linux/Python 3.12) con hashes. La imagen base permanece como etiqueta 3.12-slim, aún sin digest ni build validado. |
| Cargar el modelo en cada llamada | api/dependencies.py centraliza MODEL_PATH y la carga en lifespan; se carga una sola vez, rechazando versiones incompatibles y contratos distintos. |
| /predict/batch recibe JSON | Implementado como lista JSON; el CSV previo se conserva en /predict/batch/csv. |
| Gauge churn_probability | Implementado como gauge de última probabilidad; se añade churn_probability_distribution para la distribución. Los cuatro histogramas de inputs usan los nombres docentes. |
| avg_over_time(churn_input_payment_delay[15s]) | Un histograma clásico expone _sum, _count y _bucket, no esa serie escalar. Se corrige a sum(rate(churn_input_payment_delay_sum[15s])) / sum(rate(churn_input_payment_delay_count[15s])) > 15, con for:15s. Scrape y evaluación cada 5s. |
| models/churn_pipeline_v1.joblib | Copia validada del mismo modelo inicial. Se incluyen los dos artefactos sintéticos y su manifiesto de hashes/versiones; no se presenta el respaldo como un modelo reentrenado distinto. |
| Rollback con cp y restart | scripts/rollback_model.py valida el respaldo, archiva la copia activa y restaura atómicamente. Se probó restauración + reinicio Uvicorn y hash en /health. No se afirma rollback de contenedor ni AWS. Compose monta models/ para que un reinicio recargue la copia restaurada. |
| Express Mode requiere ecsTaskExecutionRole | También requiere infrastructure role. Ninguno de los dos roles estándar existe en la cuenta actual. ECR DescribeRepositories devolvió AccessDeniedException. |
| Envío antes del 1 de octubre | Hoy es 3 de octubre de 2026. No se afirma envío a DMC ni cumplimiento del plazo; confirmar una excepción con el profesor. |

Fuentes: [histogramas Prometheus](https://prometheus.io/docs/practices/histograms/), [Express Mode AWS CLI](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-getting-started.html).

## Pruebas y evidencia

33 tests pytest aprobados, conservando las 12 pruebas del Módulo I; una advertencia de TestClient/httpx. Ruff aprobado. Compose válido. promtool check rules y test rules aprobaron casos NORMAL y alerta FIRING.

Experimento propio con Prometheus 3.5.0 portátil en Windows y Uvicorn local, 50 peticiones por escenario, mismos clientes sintéticos muestreados con semilla 2026:

| Medida | NORMAL | DRIFT |
| --- | ---: | ---: |
| monthly_fee | 110.8236 | 188.40012 |
| support_calls | 1.76 | 6.76 |
| last_payment_delay | 6.52 | 31.52 |
| digital_usage_score | 70.097826 | 28.039130 |
| Probabilidad media | 0.413552 | 0.433207 |

Se verificó target UP, ninguna alerta de atraso durante NORMAL y HighAveragePaymentDelay FIRING durante DRIFT. Los procesos portátiles se detuvieron al finalizar. Evidencia propia: reports/metrics/monitoring_lab.json, traffic_normal.json, traffic_drift.json y rollback_lab.json. No se copiaron cifras del profesor ni se concluye concept drift o pérdida de accuracy sin ground truth posterior.

## Ejecución local

```bash
pip install -r requirements.txt -r requirements-api.txt -r requirements-api-dev.txt
pytest -v
python scripts/prepare_serving_models.py
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

La instalación y el modelo requieren Python >=3.12; usar el perfil .devcontainer/serving. Abrir /docs para enviar todos los campos reales. La salud incluye status, service, threshold y model_sha256. La API no entrena ni ajusta transformaciones al inferir.

Con Docker Desktop Linux realmente funcionando:

```bash
docker compose config --quiet
docker build -t novatel-churn-api:aws-v1 .
docker compose up -d
python simulate_traffic.py --scenario normal
python simulate_traffic.py --scenario drift
curl http://localhost:9090/api/v1/alerts
python scripts/rollback_model.py
docker compose restart api
curl http://localhost:8000/health
docker compose down
```

Docker Desktop fue iniciado, pero el motor no respondió al probe con timeout. Las pruebas portátiles no sustituyen el build o ejecución de contenedores. Para repetir promtool: promtool check rules alerts.yml y promtool test rules tests/prometheus_rules.yml. No se reentrena automáticamente al dispararse una alerta.

## AWS: plan preparado, no ejecutado

Región configurada y de la guía: us-east-1. STS confirma identidad IAM, sin publicar credenciales. Faltan ecsTaskExecutionRole y ecsInfrastructureRoleForExpressServices; la consulta ECR está denegada. El despliegue exige confirmar cuenta destino, corregir permisos y autorizar creación/costos (se mantiene la instrucción de no crear recursos todavía).

Plan: build Linux amd64 de novatel-churn-api:aws-v1, repositorio ECR privado novatel-churn-api, push por password-stdin, ECS Express Mode con ambos roles y health-check-path /health, validación de HTTPS y cleanup verificando los recursos realmente creados. La guía menciona el DNS del ALB; se debe usar el endpoint HTTPS que Express Mode entregue y comprobar el certificado, no asumir que cualquier DNS ALB tiene TLS válido.

Los roles corresponden a AmazonECSTaskExecutionRolePolicy y AmazonECSInfrastructureRoleforExpressGatewayServices, con relaciones de confianza y permisos PassRole correctos. No se crearon roles, políticas, ECR, ECS, ALB ni otros recursos. No existe URL cloud ni evidencia de CloudWatch/HTTPS. No se ejecutaron los comandos destructivos de cleanup de la guía sobre recursos ajenos o nombres supuestos.

## Verificación Docker posterior y publicación

PR #2 integrado tras checks aprobados. https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/actions/runs/37144265520 verificó 33 tests, build y ejecución real Docker Compose, promtool, 50 NORMAL sin alerta y 50 DRIFT con alerta FIRING, target UP y salud tras rollback. Evidencia: reports/metrics/container_verification.json. El modelo restaurado coincide con el inicial; no prueba una mejora de calidad. El bloqueo del motor Windows permanece local; la validación de contenedores se completó en Ubuntu de GitHub Actions. AWS permanece sin desplegar.
