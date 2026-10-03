"""Validate a stable local artifact and atomically restore a serving copy."""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.dependencies import load_serving_model
from src.utils.configuration import resolve_project_path


def rollback(backup: Path, active: Path) -> dict:
    """Validate backup, archive active bytes, then atomically replace active.

    Args:
        backup: Trusted previously validated artifact; never modified.
        active: Working serving copy to restore; must differ from backup.
    Returns:
        Hashes and archive path; the API still requires restart/reload afterward.
    """
    backup = backup.resolve()
    active = active.resolve()
    if backup == active:
        raise ValueError("Backup and active must differ")
    _, digest = load_serving_model(backup)
    old_hash = (
        hashlib.sha256(active.read_bytes()).hexdigest() if active.exists() else None
    )
    archive = None
    if active.exists():
        archive = active.with_name(
            active.name + ".before-rollback-" + uuid.uuid4().hex[:12]
        )
        if archive.exists():
            raise FileExistsError("Previous rollback archive exists; preserve it first")
        shutil.copy2(active, archive)
    active.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(
        prefix=".restore-", suffix=".joblib", dir=active.parent
    )
    os.close(descriptor)
    temporary = Path(name)
    try:
        shutil.copy2(backup, temporary)
        load_serving_model(temporary)
        os.replace(temporary, active)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "restored_sha256": digest,
        "previous_sha256": old_hash,
        "archive": archive.name if archive else None,
        "requires_restart": True,
    }


def main():
    """Restore a working model copy; never restart or redeploy automatically."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", default="models/churn_pipeline_v1.joblib")
    parser.add_argument("--active", default="models/churn_pipeline.joblib")
    args = parser.parse_args()
    print(
        json.dumps(
            rollback(
                resolve_project_path(args.backup), resolve_project_path(args.active)
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
