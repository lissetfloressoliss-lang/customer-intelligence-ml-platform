"""Read the canonical root params.yaml without depending on the working directory."""

from pathlib import Path

import yaml

from src.utils.paths import get_project_path


def resolve_project_path(path: str | Path) -> Path:
    """Resolve relative paths against the repository root; preserve absolute paths.

    Args:
        path: CSV or YAML path; relative configuration paths resolve from the project root.

    Returns:
        Absolute Path, preserving absolute inputs and resolving relative inputs.
    """
    path = Path(path)
    return path if path.is_absolute() else get_project_path(path)


def load_parameters(path: str | Path = "params.yaml") -> dict:
    """Load the project configuration, rejecting missing configuration sections.

    Args:
        path: CSV or YAML path; relative configuration paths resolve from the project root.

    Returns:
        Dictionary containing training, model, prediction and paths sections.
    """
    with resolve_project_path(path).open(encoding="utf-8") as stream:
        params = yaml.safe_load(stream)
    if not isinstance(params, dict):
        raise TypeError("Parameters must be a YAML mapping.")
    for section in ("training", "model", "prediction", "paths"):
        if not isinstance(params.get(section), dict):
            raise TypeError(f"Missing or invalid parameters section: {section}")
    return params
