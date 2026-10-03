# Auditoría final Curso 2 — 3 de octubre de 2026

Fuente obligatoria: guía completa recibida en Texto pegado.txt. Auditoría documental del código y evidencias existentes: no se repitieron tests ni despliegues. Cumple significa resultado funcional acreditado; parcial identifica una diferencia literal o una comprobación incompleta.

| Requisito | Evidencia | Estado | Limitación |
| --- | --- | --- | --- |
| Caso NovaTel y conservación Curso 1 | README.md; src/; artifacts/models/; models/manifest.json | cumple | Datos sintéticos; no calidad real de producción. |
| Rama feature/fastapi-serving, commit docente y PR hacia main | [PR #2](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/pull/2); commit a5c59c2 | cumple | PR integrado; documentación posterior consolidada en main. |
| Repositorio público y estructura api/, models/, tests/ | api/; models/; tests/test_api.py; GitHub público | cumple | Raíz del repositorio existente, no carpeta novatel-churn nueva. |
| Dependencias fijas exactas del ejemplo | requirements-api.txt; requirements-api-lock.txt; models/manifest.json | parcial | Versiones distintas por compatibilidad del artefacto: sklearn 1.9.1 y joblib 1.6.0; lock Linux/Python 3.12 con hashes. No se afirma reproducción de versiones docentes. |
| Pydantic, tipos e intervalos | api/schemas.py; tests/test_api.py | cumple | Contrato real de 18 features y customer_id; el ejemplo de 4 campos no basta para este modelo. |
| Carga centralizada MODEL_PATH | api/dependencies.py; api/main.py | cumple | Se carga una vez en lifespan; rechaza incompatibilidad sklearn. |
| /health, /predict, /predict/batch | api/main.py; reports/metrics/aws_lab_retry/https_verification.json | cumple | AWS: HTTP 200; API temporal retirada tras validación. Batch JSON, CSV adicional separado. |
| pytest y ejecución Uvicorn | [Actions Docker](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/actions/runs/37144265520); tests/test_api.py | cumple | 33 tests, una advertencia TestClient/httpx; Docker Windows no operativo, runner Ubuntu sí. |
| Dockerfile Python 3.12, puerto 8000, .dockerignore | Dockerfile; .dockerignore; requirements-api-lock.txt | cumple | Base python:3.12-slim sin digest; transiciones de base no bloqueadas. |
| Build Linux amd64 y Compose API+Prometheus 8000/9090 | docker-compose.yml; [build imagen](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/actions/runs/37155186041); reports/metrics/container_verification.json | cumple | Compose/Prometheus verificados en Actions; puertos limitados a loopback. |
| ECR privado novatel-churn-api e imagen aws-v1 | reports/metrics/aws_lab/image.json; reports/metrics/aws_lab_retry/create_service.json; Docker Compose | parcial | Imagen publicada con tag lab-e57f06d y digest 7ce2b015…, no aws-v1 en ECR. ECR eliminado por cleanup; imagen sí fue desplegada. |
| ECS Fargate Express y HTTPS/ALB | reports/metrics/aws_lab_retry/ecs_completed.json; service_completed.json; https_verification.json | cumple | Una tarea 0.25 vCPU/1GB, COMPLETED. Endpoint Express HTTPS; curl --resolve por DNS local, TLS validado. |
| Seguridad IAM y exclusión secretos | .gitignore; reports/metrics/course2_publication_review.json; política complementaria saneada | parcial | Sin root ni secretos en código; no consta MFA, rotación o carácter temporal de credenciales CLI. Escaneo no es auditoría formal. |
| /metrics Counter, Histogram, Gauge y 4 inputs | api/main.py; reports/metrics/container_verification.json; aws_lab_retry/https_verification.json | cumple | AWS probó exposición /metrics; scrape y alerta se demostraron en Docker, no en AWS. |
| Scrape/evaluation 5s y alerts.yml | prometheus.yml; alerts.yml; tests/prometheus_rules.yml | cumple | Regla adaptada a _sum/_count de Histogram; ejemplo avg_over_time sobre nombre base no es válido para este histograma. |
| Simulación 50 NORMAL y 50 DRIFT | simulate_traffic.py; reports/metrics/traffic_normal_container.json; traffic_drift_container.json | cumple | Resultados propios distintos de la tabla del profesor; simulación sintética. |
| Alerta HighAveragePaymentDelay FIRING | reports/metrics/container_verification.json; monitoring_lab.json | cumple | FIRING real en Docker y Prometheus portátil; no se atribuye a AWS. |
| Analizar input/prediction/concept drift | docs/course_2/guide_alignment.md; reports/metrics/container_verification.json | cumple | Probabilidad 0.413552→0.433207; no ground truth posterior ni pérdida de accuracy demostrada. |
| Rollback respaldo, restart API y health | scripts/rollback_model.py; reports/metrics/container_verification.json; rollback_lab.json | cumple | Respaldo idéntico al inicial; valida procedimiento, no mejora de versión distinta. Docker verificado; no rollback AWS. |
| No reentrenar automáticamente ante alerta | api/main.py; simulate_traffic.py; scripts/rollback_model.py | cumple | Alerta inicia investigación; no reentrenamiento automático. |
| Cleanup de recursos de despliegue | reports/metrics/aws_lab_retry/closure_check.json; manual_admin_closure.json | parcial | API: servicio/clúster INACTIVE, cero tareas, ECR/SG ausentes. Manual administrador: sin ALB/TG y logs NovaTel eliminados. Auto Scaling y revisiones pendientes. |
| URL pública enviada a DMC en plazo | No hay evidencia de envío | pendiente | Guía fija 24 septiembre–1 octubre y prohíbe fuera de plazo; fecha actual 3 octubre. Requiere regularización docente, no se afirma entrega. |

## Endpoint y enlace de entrega

La guía ordena desmontar después de validar, por lo que no exige endpoint permanentemente activo. El estado de servicio se acredita con respuestas guardadas y se reproduce localmente si el evaluador lo requiere. En DMC se entrega exactamente https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform . PR y Actions son enlaces complementarios, no sustituyen la URL del repositorio.

## Cierre pendiente

Auto Scaling: confirmar ausencia de service/novatel-lab/novatel-churn-api, namespace ecs, dimensión ecs:service:DesiredCount y sus políticas/acciones. No hay consulta API autorizada. Revisión :2 seguía ACTIVE en cierre; :1 no tiene confirmación final de desregistro. El administrador debe desregistrar solo las revisiones del laboratorio; no borrar roles vinculados compartidos. Logs /aws-glue/crawlers conservados. No se declara limpieza total.

## Requisitos pendientes y diferencias

Obligatorio sin evidencia: envío oficial DMC en plazo. Cleanup aún incompleto en comprobación. Diferencias literales a aceptar: versiones/modelo real, schema de 18 features, tag ECR distinto y PromQL corregido. No justifica otro despliegue para renombrar un tag ya retirado. Codespaces pertenece a la solicitud previa del Curso 1; no figura como requisito del Curso 2 en esta guía. Prometheus cloud, rollback cloud, MFA y rotación no cuentan con evidencias propias; no se inventan.
