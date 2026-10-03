# Módulo II: materiales, compatibilidad y estado local

Fecha: 3 de octubre de 2026. Búsqueda en toda la carpeta del curso, conservando los originales. La guía completa del segundo trabajo aún no fue suministrada; esta implementación inicial sigue las presentaciones disponibles y deberá contrastarse con esa guía.

## Archivos originales encontrados

Raíz de búsqueda: `D:\6. 2026\Cursos\202609 DMC_ML Engineering & MLOp`.

| Material | Ruta desde esa raíz |
| --- | --- |
| FastAPI, sesión 6 | `s6\01. Descubre\S6_De-un-modelo-ML-a-una-API-REST-con-FastAPI.pptx` |
| Docker y Prometheus, sesión 7 | `s7\01. Descubre\S7_Contenerizacion-de-una-API-ML-con-Docker.pptx` |
| AWS, sesión 8 | `s8\Material sesión 08-20261003\01. Descubre\Curso 2 S8 – Despliegue y mantenimiento automatizado de modelos.pptx` |
| Monitoreo y mantenimiento, sesión 9 | `s9\Material sesión 09-20261003\01. Descubre\C2_S9 - Monitoring.pptx` |
| ZIP base del Módulo I | `s1\02. Explora\entregable_D3_16_repositorio_final_curso_1.zip` |
| Guía del Módulo I | `modulo I\Guía Práctica de Laboratorio.docx` |
| Referencia al repositorio | `modulo I\link del repositorio de github.docx` |

Las carpetas s6–s9 también contienen grabaciones y transcripciones. No se encontraron ZIP, notebooks, scripts Python, Dockerfiles ni modelos joblib independientes del Módulo II en la carpeta del curso. El ZIP disponible corresponde al Módulo I y la copia extraída contiene sus seis notebooks, módulos, dataset y el joblib generado localmente. No se modificaron originales ni se copiaron resultados de las diapositivas como evidencia propia.

## Base y contrato real

Se extendió el repositorio NovaTel existente en la rama local `feature/fastapi-serving`, desde `main` del Módulo I (`3273fc5`). El entrenamiento, parámetros, dataset, notebooks y código de inferencia del Módulo I se conservan. No se publicó ni integró esta nueva rama.

Artefacto: `artifacts/models/churn_pipeline.joblib`, Pipeline con preprocesador y regresión logística, clases [0, 1]. SHA256: `63eb7a8fae5719eb69ae3a109ec3eaafe1b21679f3e8f176a84362ecb5883f6d`.

Variables numéricas requeridas:

`age`, `tenure_months`, `monthly_fee`, `total_spent`, `support_calls`, `complaints`, `last_payment_delay`, `digital_usage_score`, `marketing_score`, `preferred_contact_hour`.

Variables categóricas requeridas:

`gender`, `region`, `customer_segment`, `contract_type`, `internet_service`, `tv_service`, `streaming_service`, `payment_method`.

`customer_id` se conserva como identificador de respuesta. `churn` e `internal_campaign_code` no entran al modelo. Los campos deben estar presentes; faltantes explícitos en campos permitidos se imputan con el preprocesador persistido. El contrato JSON parcial de la diapositiva no basta para este modelo. La API rechaza categorías fuera del diccionario aunque OneHotEncoder admita desconocidas: una decisión de validación del contrato, no una propiedad distinta del modelo.

## Dependencias y diferencias

NumPy 2.5.3 y SciPy 1.18.1 declaran Python >=3.12; por tanto el serving fijado requiere Python >=3.12, aunque el Módulo I declare >=3.11. Se añade `.devcontainer/serving/devcontainer.json` para Python 3.12 sin cambiar el perfil original 3.11. Seleccionar este perfil para Módulo II; no instalar estas versiones API en el perfil 3.11.

El artefacto local carga sin advertencias de versión con Python 3.12.13, scikit-learn 1.9.1, numpy 2.5.3, pandas 2.3.3, joblib 1.6.0 y scipy 1.18.1. `requirements-api.txt` fija estas versiones reales y las dependencias API. Se conservan las listas originales del Módulo I; se añade `requirements-api-dev.txt` para pruebas HTTP y se adapta el workflow para instalarlas.

La presentación Docker usa scikit-learn 1.9.0, numpy 2.5.1 y joblib 1.5.3. Esas versiones difieren de nuestro artefacto y no se copiaron. Cargar modelos scikit-learn entre versiones diferentes no es una compatibilidad garantizada; la API convierte InconsistentVersionWarning en error de arranque. No carga artefactos aportados por usuarios.

Las dependencias directas de serving están fijadas; sus transitivas y la etiqueta base Docker no quedan fijadas por digest. Para producción falta un lock multiplataforma y una imagen validada. El TestClient instalado emite una advertencia de migración futura de httpx a httpx2; las pruebas actuales funcionan y esta advertencia no representa fallo del modelo.

Fuentes técnicas: [persistencia scikit-learn](https://scikit-learn.org/stable/model_persistence.html), [lifespan FastAPI](https://fastapi.tiangolo.com/advanced/events/), [archivos FastAPI](https://fastapi.tiangolo.com/tutorial/request-files/), [histogramas Prometheus](https://prometheus.github.io/client_python/instrumenting/histogram/).

## Implementación y ejecución local

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-api.txt -r requirements-api-dev.txt
$env:PYTEST_ADDOPTS='--basetemp=.tools/pytest-course2-user'
pytest -v
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Abrir `http://127.0.0.1:8000/docs`. GET /health indica el modelo cargado y umbral 0.45. POST /predict valida todos los campos. POST /predict/batch acepta CSV UTF-8 de hasta 50000 filas y 20 MiB, valida columnas e IDs duplicados, e ignora churn/campaign para inferencia. GET /metrics expone contadores por clase, latencia, distribución de scores y atrasos; no incluye IDs ni clientes en labels.

El modelo se carga una sola vez durante lifespan. No se ajusta ningún preprocesador ni se entrena en la API. El Dockerfile copia solo serving, módulos y modelo, ejecuta como usuario sin privilegios y usa un worker: las métricas son por proceso. El artefacto está excluido de Git y debe generarse antes del build con las versiones compatibles. Desde un clon limpio, instalar requisitos API antes de entrenar el artefacto que se incluirá en Docker.

Con Docker Desktop y su motor Linux iniciados:

```bash
python main.py train --data data/raw/customer_churn.csv
docker compose config --quiet
docker compose up --build -d
```

Prometheus se configura para consultar `api:8000/metrics` cada 15 segundos. La regla HighAveragePaymentDelay compara el promedio observado en 5 minutos con 15 días durante 15 segundos. Tener el archivo de regla no demuestra que la alerta haya disparado. No hay Alertmanager, ground truth posterior, automatización de reentrenamiento ni rollback ejecutado.

## Infraestructura y bloqueos reales

- Docker CLI 29.5.2 disponible. El motor Docker Desktop Linux no estaba accesible (named pipe inexistente). Compose validó su sintaxis sin iniciar servicios. No se construyó imagen ni se ejecutó Prometheus.
- AWS CLI 2.35.5 disponible. Perfil `default` configurado y consulta STS de solo lectura exitosa. No se imprimieron credenciales; no se crearon recursos. Esto confirma autenticación, no permisos IAM para ECR/ECS/Fargate/ALB ni región o cuenta de destino aprobada.
- La guía completa del segundo trabajo sigue pendiente. La arquitectura AWS de las diapositivas es ECR + ECS/Fargate + ALB/HTTPS + CloudWatch, pero no se inventaron comandos de aprovisionamiento ni despliegues.
- Los resultados de 13 tests, tamaños de imagen, latencias y alerta FIRING de las diapositivas pertenecen al ejemplo docente; no son resultados de este trabajo.
- La ejecución HTTP local y TestClient verifican API y métricas observadas. No equivalen a scrape Prometheus, alerta FIRING ni endpoint HTTPS desplegado.

## Resultados propios verificados

29 pruebas aprobadas (12 del Módulo I y 17 de serving); una advertencia de TestClient/httpx, sin fallos. Ruff aprobado (E4/E7/E9/F/I), dependencias compatibles según `uv pip check`, Compose válido según `docker compose config --quiet`. API Uvicorn real en loopback: /health HTTP 200, /predict HTTP 200, umbral 0.45 y métricas de una inferencia comprobadas. El servidor se detuvo al terminar. Evidencia en `reports/metrics/course2_http_verification.json` y `course2_readiness.json`.
