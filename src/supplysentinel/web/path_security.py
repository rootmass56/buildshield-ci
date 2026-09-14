from __future__ import annotations

import os
from pathlib import Path

from fastapi import HTTPException


WORKSPACE_ROOT_ENV = "BUILDSHIELD_WORKSPACE_ROOT"
DEFAULT_WORKSPACE_ROOT = Path.cwd().resolve()


def get_workspace_root() -> Path:
    raw_value = os.getenv(WORKSPACE_ROOT_ENV)

    if raw_value:
        configured_root = Path(raw_value)

        if not configured_root.is_absolute():
            configured_root = DEFAULT_WORKSPACE_ROOT / configured_root
    else:
        configured_root = DEFAULT_WORKSPACE_ROOT

    try:
        workspace_root = configured_root.resolve()
    except (OSError, RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail="Configured workspace root is unavailable.",
        ) from error

    if not workspace_root.exists() or not workspace_root.is_dir():
        raise HTTPException(
            status_code=500,
            detail="Configured workspace root is unavailable.",
        )

    return workspace_root


def _resolve_workspace_candidate(path_value: str) -> Path:
    if not path_value or not path_value.strip():
        raise HTTPException(
            status_code=400,
            detail="Path must not be empty.",
        )

    workspace_root = get_workspace_root()
    candidate = Path(path_value)

    if not candidate.is_absolute():
        candidate = workspace_root / candidate

    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid path.",
        ) from error

    if not resolved.is_relative_to(workspace_root):
        raise HTTPException(
            status_code=403,
            detail="Path is outside the configured workspace.",
        )

    return resolved


def resolve_workspace_directory(path_value: str) -> Path:
    resolved = _resolve_workspace_candidate(path_value)

    if not resolved.exists():
        raise HTTPException(
            status_code=404,
            detail="Repository path does not exist.",
        )

    if not resolved.is_dir():
        raise HTTPException(
            status_code=400,
            detail="Repository path must be a directory.",
        )

    return resolved


def resolve_workspace_file(path_value: str) -> Path:
    resolved = _resolve_workspace_candidate(path_value)

    if not resolved.exists():
        raise HTTPException(
            status_code=404,
            detail="File path does not exist.",
        )

    if not resolved.is_file():
        raise HTTPException(
            status_code=400,
            detail="Path must reference a file.",
        )

    return resolved


def _validate_single_path_component(value: str, field_name: str) -> None:
    if (
        not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or "\x00" in value
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}.",
        )


def resolve_report_file(
    reports_root: Path,
    run_id: str,
    filename: str,
) -> Path:
    _validate_single_path_component(run_id, "report run ID")
    _validate_single_path_component(filename, "report filename")

    try:
        canonical_root = reports_root.resolve()
        run_dir = (canonical_root / run_id).resolve(strict=False)
        target = (run_dir / filename).resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid report path.",
        ) from error

    if not run_dir.is_relative_to(canonical_root):
        raise HTTPException(
            status_code=400,
            detail="Invalid report path.",
        )

    if not target.is_relative_to(run_dir):
        raise HTTPException(
            status_code=400,
            detail="Invalid report path.",
        )

    if not target.is_relative_to(canonical_root):
        raise HTTPException(
            status_code=400,
            detail="Invalid report path.",
        )

    if not target.exists() or not target.is_file():
        raise HTTPException(
            status_code=404,
            detail="Report file not found.",
        )

    return target
