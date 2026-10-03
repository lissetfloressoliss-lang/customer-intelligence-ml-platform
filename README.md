# Customer Intelligence ML Platform — NovaTel Perú

Pipeline educativo de churn con datos completamente sintéticos. Incluye 6 notebooks (281 celdas), módulos en `src/`, CLI, pruebas, DVC y workflow de GitHub Actions en `.github/workflows/tests.yml`.

## Entorno aislado

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

## Configuración

La fuente real es **`params.yaml` en la raíz**, no `config/params.yaml`.
Ver [diferencias con la guía](docs/course_notes/laboratory_alignment.md).
El YAML configura la división, semilla, algoritmo, iteraciones, pesos, umbral y rutas de salida. `--params` permite otra configuración. `--test-size`, `--seed`, `--threshold` y rutas de salida explícitas tienen prioridad sobre el YAML. El umbral vigente es **0.45**. La versión funcional inicial de `main` (`9403276`) se registró con **0.50** antes de crear `feature/threshold-configuration`.

## Verificaciones y ejecución

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

## Comparación de umbrales y costo

Mismo modelo persistido y mismas 200 filas reservadas, con 48 casos de churn:

| Threshold | Recall | Precision | FP | FN | Costo: 50*FP + 500*FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.50 | 0.750000 | 0.378947 | 59 | 12 | 8950 |
| 0.45 | 0.833333 | 0.373832 | 67 | 8 | 7350 |

0.45 reduce el costo observado en **1600 (17.88%)**, evita 4 FN y agrega 8 FP. La precisión baja ligeramente. La evaluación por defecto del clasificador a 0.50 dio accuracy 0.645, F1 0.503497 y ROC AUC 0.728344.
Las predicciones batch sobre las 1000 filas sirven para demostrar inferencia, no para justificar el cambio de umbral.

## DVC

Con el entorno activo y Git inicializado:

```bash
dvc init
dvc repro
dvc metrics show
```

Se verificó `dvc repro --force` con `.venv/Scripts` primero en PATH; ambas etapas terminaron y se generó `dvc.lock`. `dvc init` y `dvc metrics show` encontraron una restricción de propiedad de Git bajo el usuario de ejecución automática de Windows; las métricas se verificaron leyendo su JSON. La excepción `safe.directory` para Git se limitó al proceso, sin cambiar configuración global. No se configuró un almacenamiento remoto DVC. `scripts/setup_git_dvc.sh` es un ejemplo para Bash/Linux y usa `/tmp/dvc-storage`; no es un script de PowerShell.

## Límites y publicación

La comparación es exploratoria sobre un único split sintético. Al comparar umbrales en ese split se usa para selección; falta un conjunto final independiente o validación cruzada para confirmar la mejora. Los costos de 50 y 500 son supuestos de la guía, no resultados financieros reales. No hay servicio FastAPI, Docker, AWS ni monitoreo Prometheus: corresponden a una extensión posterior.

Los artefactos `.joblib`, predicciones, entorno virtual, cachés, herramientas y temporales están excluidos de Git y se regeneran con los comandos anteriores. La revisión de los archivos candidatos, incluidos los notebooks, no detectó claves ni tokens; el correo `correo@example.com` de la guía Git es un ejemplo. El CSV no contiene nombres, correos, teléfonos ni direcciones reales. El análisis por patrones no reemplaza una auditoría de seguridad formal. Los manifiestos originales reflejan la validación histórica del ZIP (9 pruebas), no sustituyen los resultados actuales.

Estado remoto: repositorio público publicado en la cuenta verificada `lissetfloressoliss-lang` de Lisset Flores. Ambas ramas están publicadas y el [PR #1](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/pull/1) fue integrado mediante merge; `main` local se sincronizó con el remoto. [GitHub Actions](https://github.com/lissetfloressoliss-lang/customer-intelligence-ml-platform/actions/runs/37139590833) aprobó las 12 pruebas en Ubuntu y Python 3.12. La ejecución dentro de Codespaces permanece pendiente y se describe a continuación.

## Verificación final en GitHub Codespaces

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

Se esperan 12 tests aprobados y un dataset de 1000 filas, 21 columnas, 256 nulos y churn de 24%. El comparador usa las mismas 200 filas reservadas, no las predicciones de todo el dataset. Confirmar que sus costos reproducen 8950 y 7350; si cambian, registrar las versiones y resultados reales antes de atribuir la diferencia al umbral. Los rangos de dependencias permiten actualizaciones y no garantizan idénticas versiones entre Python 3.11 y 3.12.

Esta secuencia está documentada para completar el requisito del laboratorio. La ejecución local y GitHub Actions no equivalen a ejecutar un Codespace; conservar la salida de la terminal como evidencia del paso realizado en Codespaces. Detener el Codespace al terminar desde su menú de administración.

## Curso 2: serving local

La guía completa se contrastó en [adaptaciones, resultados propios y bloqueos](docs/course_2/guide_alignment.md). Hay 33 tests aprobados, simulación real NORMAL/DRIFT con Prometheus portátil y alerta FIRING, y rollback local con hash comprobado. Docker y AWS siguen pendientes. El [inventario inicial](docs/course_2/materials_and_readiness.md) describe el estado previo a recibir la guía. Los modelos de serving sintéticos están en models/, con manifiesto de versiones; artifacts/models/ conserva el Curso 1.
