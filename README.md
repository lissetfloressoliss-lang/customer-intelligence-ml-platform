# Customer Intelligence ML Platform — NovaTel Perú

Entrega académica de Lisset Flores: **Módulo I — desarrollo del pipeline de ML** y **Módulo II — despliegue y mantenimiento automatizado de modelos**. Caso educativo de churn con datos completamente sintéticos; el Módulo II conserva el pipeline del Módulo I.

**Enlace de entrega:** [repositorio público en main](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform). La [auditoría final del Módulo II](docs/course_2/final_audit.md) compara cada requisito de la guía con sus evidencias y limitaciones. La API AWS fue validada por HTTPS y retirada al finalizar; la guía exige desmontar tras la validación, no mantener un endpoint activo.

## Módulo I: pipeline de entrenamiento e inferencia

Componentes: seis notebooks (281 celdas), módulos de datos/preprocesamiento/modelado en `src/`, CLI `main.py`, parámetros en `params.yaml`, pruebas, pipeline DVC y GitHub Actions. El modelo persistido incluye imputación, escalado y OneHotEncoder; las transformaciones se ajustan únicamente con las 800 filas de entrenamiento. Se reservan 200 filas para evaluación estratificada, con semilla 42.

Resultados existentes: dataset de 1000 filas y 21 columnas, 256 valores faltantes, cero IDs duplicados y churn de 24%; carga, validación, entrenamiento e inferencia ejecutados. Se generaron el `.joblib`, métricas y 1000 predicciones. Las 12 pruebas del Módulo I y Ruff aprobaron; la versión funcional inicial usaba threshold 0.50 y la rama `feature/threshold-configuration` incorporó 0.45.

Mismo modelo persistido y mismas 200 filas reservadas, con 48 casos de churn:

| Threshold | Recall | Precision | FP | FN | Costo: 50*FP + 500*FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.50 | 0.750000 | 0.378947 | 59 | 12 | 8950 |
| 0.45 | 0.833333 | 0.373832 | 67 | 8 | 7350 |

0.45 reduce el costo observado en **1600 (17.88%)**, evita 4 FN y agrega 8 FP. La precisión baja ligeramente. La evaluación por defecto del clasificador a 0.50 dio accuracy 0.645, F1 0.503497 y ROC AUC 0.728344.
Las predicciones batch sobre las 1000 filas sirven para demostrar inferencia, no para justificar el cambio de umbral.

Evidencias y publicación:

- [Comparación sobre evaluación reservada](reports/metrics/threshold_comparison.json) y [métricas de entrenamiento](reports/metrics/training_metrics.json).
- [PR #1 integrado](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/pull/1) y [Actions: 12 pruebas aprobadas](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/actions/runs/37139590833).
- [Diferencias con la guía](docs/course_notes/laboratory_alignment.md). Los artefactos en `artifacts/models/` y predicciones en `reports/predictions/` se generan localmente y están excluidos de Git.

## Módulo II: API, contenedores y mantenimiento

Componentes: FastAPI en `api/`, validación Pydantic de las 18 variables reales del modelo y `customer_id`, carga centralizada mediante `MODEL_PATH`, endpoints `/health`, `/predict`, `/predict/batch` y `/metrics`; inferencia CSV adicional. `models/` contiene las dos copias sintéticas de serving y su [manifiesto](models/manifest.json). Dockerfile, Compose, Prometheus, `alerts.yml`, simulación NORMAL/DRIFT y script de rollback completan el laboratorio. El serving fijado requiere Python >=3.12 y dependencias compatibles con el artefacto.

Resultados locales y Docker existentes: **33 tests aprobados en total** (12 del Módulo I y 21 de API), build y salud de contenedores, validación promtool, 50 solicitudes NORMAL y 50 DRIFT, target UP, alerta `HighAveragePaymentDelay` en FIRING y reinicio saludable tras rollback. Docker se verificó en el runner Ubuntu de Actions; el daemon local de Windows no respondió. También hay evidencia local con Prometheus portátil. El backup tiene el mismo hash que el modelo inicial: acredita la restauración, sin demostrar mejora de una versión distinta. No se reentrena automáticamente ante una alerta.

Evidencias y publicación:

- [PR #2 integrado](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/pull/2) y [Actions: tests, Docker, alerta y rollback](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/actions/runs/37144265520).
- [Verificación de contenedores](reports/metrics/container_verification.json), [tráfico NORMAL](reports/metrics/traffic_normal_container.json) y [tráfico DRIFT](reports/metrics/traffic_drift_container.json).
- [Adaptaciones y resultados propios](docs/course_2/guide_alignment.md), [inventario inicial histórico](docs/course_2/materials_and_readiness.md) y [auditoría final](docs/course_2/final_audit.md).

### Despliegue AWS exitoso

El único reintento controlado autorizado del **3 de octubre de 2026** llegó a **COMPLETED** en ECS Express Mode, cuenta `345485442361`, región `us-east-1`: clúster `novatel-lab`, servicio `novatel-churn-api`, una tarea Fargate de **0.25 vCPU / 1 GB**, mínimo y máximo de tareas en 1. La imagen Linux amd64 se publicó en ECR privado con tag `lab-e57f06d`.

`/health`, `/predict`, `/predict/batch`, `/metrics` y `/openapi.json` respondieron **HTTP 200 por HTTPS** con certificado validado. Salud confirmó el hash original del modelo y threshold **0.45**; las predicciones individual y batch respetaron el umbral. Se usó `curl --resolve` con DNS público por caché negativa del resolvedor local, conservando hostname, SNI y validación TLS. La exposición de métricas se verificó en AWS; el scrape Prometheus, la alerta FIRING y el rollback se demostraron en Docker/local, no en AWS.

Evidencias: [build de la imagen](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/actions/runs/37155186041), [ECS COMPLETED](reports/metrics/aws_lab_retry/ecs_completed.json), [estado del servicio](reports/metrics/aws_lab_retry/service_completed.json), [verificación HTTPS](reports/metrics/aws_lab_retry/https_verification.json) y [resultado del laboratorio](reports/metrics/aws_lab_retry/outcome.json). El endpoint es histórico y fue retirado; no se presenta como servicio activo. El costo del laboratorio breve se estimó inferior a USD 0.10: no es un importe facturado ni un límite automático; el presupuesto orientativo autorizado fue USD 1.

### Estado de cierre más reciente

No se afirma limpieza total. Se conservan la red, roles y recursos preexistentes o compartidos.

| Recurso | Estado más reciente | Fuente de comprobación |
| --- | --- | --- |
| Servicio y clúster del laboratorio | INACTIVE; cero tareas en ejecución | [Cierre por API](reports/metrics/aws_lab_retry/closure_check.json) y [resultado](reports/metrics/aws_lab_retry/outcome.json) |
| ECR `novatel-churn-api` | Eliminado | Resultado y cierre por API |
| SG `sg-02b021826cefe3ada` y `sg-00cd6568e9995797e` | Ausentes; SG default conservado | Cierre por API |
| `RollbackAlarm` | No aparece en la comprobación de cierre | Cierre por API |
| ALB y target groups | Administrador confirmó que no hay en us-east-1 | [Confirmación manual, no API](reports/metrics/aws_lab_retry/manual_admin_closure.json) |
| Logs NovaTel `…-a899` y `…-3cf2` | Ambos eliminados; `/aws-glue/crawlers` conservado | Confirmación manual del administrador, no API |
| Application Auto Scaling | Pendiente confirmar ausencia del target `service/novatel-lab/novatel-churn-api` y sus políticas/acciones | Lectura API denegada; requiere administrador |
| Definiciones `novatel-lab-novatel-churn-api:1` y `:2` | `:2` ACTIVE en la última evidencia API; `:1` sin confirmación final de desregistro | Desregistro y confirmación pendientes del administrador |

## Limitaciones y requisitos pendientes

- La selección de threshold se hizo sobre un único split sintético; falta evaluación final independiente o validación cruzada. Los costos de 50 y 500 son supuestos académicos, no resultados financieros reales. Las predicciones sobre las 1000 filas no justifican el cambio.
- El schema de 18 variables, las versiones compatibles, el tag ECR `lab-e57f06d` en lugar de `aws-v1` y la regla PromQL corregida difieren literalmente del ejemplo docente; están documentados en la auditoría. La base Docker `python:3.12-slim` no está fijada por digest.
- La simulación demuestra cambios en entradas y probabilidades; no hay ground truth posterior ni pérdida de accuracy o concept drift probados. No hay evidencia de Prometheus alojado en AWS ni rollback AWS.
- El cierre de Auto Scaling y el desregistro de revisiones de tareas siguen pendientes. MFA, rotación y carácter temporal de las credenciales CLI no están acreditados. El escaneo de secretos no reemplaza una auditoría formal.
- Codespaces del Módulo I permanece pendiente; las instrucciones siguientes no son evidencia de ejecución. Codespaces no figura como requisito del Módulo II en su guía.
- No existe evidencia de envío oficial a DMC. La guía del Módulo II fija 24 de septiembre–1 de octubre y prohíbe la entrega fuera de plazo; al 3 de octubre requiere regularización docente. El enlace a entregar es el repositorio público, con PR y Actions como evidencias complementarias.

Los datos son sintéticos: no contienen nombres, correos, teléfonos ni direcciones personales reales. La revisión de archivos candidatos, incluidos notebooks, no detectó claves ni tokens; `correo@example.com` es un ejemplo de la guía Git. Entornos virtuales, cachés, herramientas y temporales están excluidos de Git. Los manifiestos originales del ZIP reflejan la validación histórica de nueve pruebas, no los resultados posteriores.

## Ejecución y reproducción

Los comandos siguientes son instrucciones para el evaluador; esta mejora documental no repite pruebas ni despliegues.

### Módulo I: entorno aislado

Requiere Python >=3.11. Desde la raíz que contiene `main.py`:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
```

En Linux/Codespaces, activar con `source .venv/bin/activate`.
La verificación local usó una instalación existente de Python 3.12.13, creando `.venv` con `uv venv --python 3.12 .venv` e instalando ambas listas con `uv pip`. Las versiones resueltas se registran en `requirements-resolved.txt` como evidencia del entorno; las listas declaradas continúan definiendo los rangos permitidos.
Jupyter no está declarado: para abrir notebooks hace falta un kernel/entorno Jupyter adicional. Codespaces se configura en `.devcontainer/devcontainer.json`.

### Configuración del pipeline

La fuente real es **`params.yaml` en la raíz**, no `config/params.yaml`.
Ver [diferencias con la guía](docs/course_notes/laboratory_alignment.md).
El YAML configura la división, semilla, algoritmo, iteraciones, pesos, umbral y rutas de salida. `--params` permite otra configuración. `--test-size`, `--seed`, `--threshold` y rutas de salida explícitas tienen prioridad sobre el YAML. El umbral vigente es **0.45**. La versión funcional inicial de `main` (`9403276`) se registró con **0.50** antes de crear `feature/threshold-configuration`.

### Comandos y salidas del Módulo I

```bash
pytest -v
python -c "from src.data import load_customer_data, validate_customer_data; print(validate_customer_data(load_customer_data()).to_dict())"
python main.py train --data data/raw/customer_churn.csv
python main.py predict --data data/raw/customer_churn.csv --model artifacts/models/churn_pipeline.joblib
python scripts/evaluate_thresholds.py
```

En esta máquina los temporales por defecto de pytest presentan un problema de permisos. Se resolvió con `$env:PYTEST_ADDOPTS='--basetemp=.tools/pytest-local'` antes de `pytest -v`; `.tools/` está excluida de Git.

Resultado local: **12 pruebas aprobadas** (9 originales y 3 nuevas). Ruff sin errores para las reglas E4/E7/E9/F/I; todos los métodos y funciones de `src/` tienen docstrings de argumentos y retornos. Entrenamiento e inferencia ejecutados con Python 3.12.13.

Salidas verificadas:

- `artifacts/models/churn_pipeline.joblib`: preprocesamiento y clasificador.
- `reports/metrics/training_metrics.json`: métricas y tamaños del split.
- `reports/predictions/customer_predictions.csv`: 1000 predicciones batch.
- `reports/metrics/threshold_comparison.json`: evaluación reservada y sus IDs sintéticos.

El dataset tiene 1000 filas, 21 columnas, cero IDs duplicados, 256 valores faltantes y churn de 24%. Se regeneró con semilla 42 en una copia temporal y se comprobó igualdad de todos los valores con el CSV incluido. Los faltantes se imputan dentro del pipeline.

Se separan **800 filas de entrenamiento y 200 de evaluación**, estratificadas, semilla 42, antes de ajustar cualquier transformación. El `.joblib` conserva el `ColumnTransformer` con imputación, escalado y OneHotEncoder. Las pruebas comprueban que el escalador vio únicamente las filas de entrenamiento y que las probabilidades se conservan al guardar/cargar.

### DVC

Con el entorno activo y Git inicializado:

```bash
dvc init
dvc repro
dvc metrics show
```

Se verificó `dvc repro --force` con `.venv/Scripts` primero en PATH; ambas etapas terminaron y se generó `dvc.lock`. `dvc init` y `dvc metrics show` encontraron una restricción de propiedad de Git bajo el usuario de ejecución automática de Windows; las métricas se verificaron leyendo su JSON. La excepción `safe.directory` para Git se limitó al proceso, sin cambiar configuración global. No se configuró un almacenamiento remoto DVC. `scripts/setup_git_dvc.sh` es un ejemplo para Bash/Linux y usa `/tmp/dvc-storage`; no es un script de PowerShell.

### Verificación del Módulo I en GitHub Codespaces

Abrir el repositorio público, seleccionar **Code > Codespaces > Create codespace on main**. Esperar el `postCreateCommand`, que instala ambas listas de dependencias. El Dev Container usa Python 3.11, compatible con el requisito >=3.11; la verificación local usó Python 3.12.13. No hace falta volver a cargar el ZIP: el código ya está en la raíz del repositorio.

Desde la terminal del Codespace, en la raíz:

```bash
git switch main
git pull --ff-only
python --version
python -c "import pandas, sklearn, dvc; print('pandas', pandas.__version__, 'sklearn', sklearn.__version__, 'dvc', dvc.__version__)"
pytest -v
python -c "from src.data import load_customer_data, validate_customer_data; print(validate_customer_data(load_customer_data()).to_dict())"
python main.py train --data data/raw/customer_churn.csv
python main.py predict --data data/raw/customer_churn.csv --model artifacts/models/churn_pipeline.joblib
python scripts/evaluate_thresholds.py
ls -lh artifacts/models/churn_pipeline.joblib reports/metrics/training_metrics.json reports/predictions/customer_predictions.csv
python -c "import pandas as pd; d=pd.read_csv('reports/predictions/customer_predictions.csv'); assert len(d)==1000; assert d.churn_probability.between(0,1).all(); assert (d.churn_prediction==(d.churn_probability>=0.45).astype(int)).all(); print('1000 predicciones verificadas, threshold 0.45')"
dvc repro
dvc metrics show
```

La evidencia histórica del Módulo I registra 12 tests; el repositorio integrado incluye 33 tests al instalar también las dependencias API. Con el perfil original, instalar esas dependencias requiere actualizar a Python 3.12; para verificar únicamente el Módulo I, ejecutar `pytest -v --ignore=tests/test_api.py`. Se espera un dataset de 1000 filas, 21 columnas, 256 nulos y churn de 24%. El comparador usa las mismas 200 filas reservadas, no las predicciones de todo el dataset. Confirmar que sus costos reproducen 8950 y 7350; si cambian, registrar las versiones y resultados reales antes de atribuir la diferencia al umbral. Los rangos de dependencias permiten actualizaciones y no garantizan idénticas versiones entre Python 3.11 y 3.12.

Esta secuencia está documentada para completar el requisito del laboratorio. La ejecución local y GitHub Actions no equivalen a ejecutar un Codespace; conservar la salida de la terminal como evidencia del paso realizado en Codespaces. Detener el Codespace al terminar desde su menú de administración.

### Módulo II: reproducción Docker

Usar Python 3.12 (perfil `.devcontainer/serving`), instalar `requirements.txt`, `requirements-api.txt` y `requirements-api-dev.txt`, y ejecutar en un entorno con Docker operativo:

```bash
pytest -v
docker compose up --build -d --wait
python scripts/verify_container_monitoring.py
docker compose down
```

Estas instrucciones no acreditan una ejecución en Codespaces. La evidencia Docker publicada procede de Actions, y no debe confundirse con el despliegue AWS.

## Antecedentes secundarios: intento AWS fallido

El primer intento autorizado del 3 de octubre de 2026 publicó la imagen y ECS Express aceptó el servicio, pero el aprovisionamiento falló sin tareas en ejecución ni HTTPS satisfactorio. CloudTrail registró permisos explícitamente ausentes para `ecs:UpdateService` y `cloudwatch:DeleteAlarms`; `RegisterScalableTarget` indicó imposibilidad de asumir el rol vinculado recién creado. `CreateLoadBalancer` devolvió un AccessDenied genérico: no acredita por sí solo una acción IAM concreta faltante ni una restricción del plan.

Se corrigieron los permisos autorizados y se esperó la propagación de roles antes del único reintento exitoso descrito arriba. La limpieza inicial y los estados DRAINING registrados durante el desmontaje son históricos; el cierre más reciente del servicio es INACTIVE. No se ampliaron permisos ni se cambió el plan durante el reintento.

Evidencias históricas: [resultado del intento inicial](reports/metrics/aws_lab/outcome.json) y [comprobación de limpieza inicial](reports/metrics/aws_lab/cleanup_verification.json). Estos registros no sustituyen la evidencia del despliegue exitoso ni las comprobaciones posteriores de cierre.
