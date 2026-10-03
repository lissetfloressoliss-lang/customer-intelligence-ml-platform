# Contraste con la guía del profesor

Referencia leída: Guía Práctica de Laboratorio.docx, Customer Intelligence ML Platform (NovaTel Perú). El documento original se conserva fuera del repositorio.

| Guía | Proyecto y decisión aplicada |
| --- | --- |
| Editar `config/params.yaml` | El ZIP solo incluye `params.yaml` en la raíz; `config/` contiene `.gitkeep`. Se conserva una única fuente de configuración en la raíz, compatible con `dvc.yaml`. |
| Codespaces, `unzip` y `cp -a` | La ejecución actual usa Windows y `.venv` con una instalación existente de Python 3.12.13. La raíz es la carpeta con `main.py` y `pyproject.toml`; no se publica la carpeta exterior de extracción. |
| DVC como dependencia de desarrollo | El ZIP declara DVC en `requirements.txt`; se conserva esa declaración. |
| Churn cercano al 20% | El CSV incluido y reproducido tiene churn de 24% (240 de 1000). |
| `python main.py train` en la validación | `--data` es obligatorio: usar `python main.py train --data data/raw/customer_churn.csv`. |
| Umbral 0.45 como optimización | Se compara con 0.50 sobre las mismas 200 filas reservadas, split estratificado y semilla 42; no se usan las 1000 predicciones batch. |
| Transformaciones persistidas | Imputación, escalado y codificación están dentro del pipeline y se ajustan después de separar 800 filas de entrenamiento. Se verifica persistencia, medias del escalador y número de filas ajustadas. |

Valores iniciales conservados: `test_size=0.20`, `random_state=42`, `algorithm=logistic_regression`, `max_iter=1000`, `class_weight=balanced`, `threshold=0.50` en la versión funcional inicial.

El entrenamiento consume todos los parámetros de `training` y `model` del YAML. `--test-size` y `--seed` tienen prioridad. La inferencia usa el umbral YAML salvo que se indique `--threshold`. Las rutas relativas de la CLI se resuelven respecto a la raíz del proyecto.

No se encontró `AGENTS.md` en el material extraído. El flujo remoto debe ejecutarse únicamente en la nueva cuenta de Lisset Flores, después de verificar la identidad autenticada.
