from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException

from supplysentinel.web.auth import get_auth_settings
from supplysentinel.web.path_security import get_workspace_root


ENVIRONMENT_ENV = "BUILDSHIELD_ENV"
COOKIE_SECURE_ENV = "BUILDSHIELD_COOKIE_SECURE"
ADMIN_USERNAME_ENV = "BUILDSHIELD_ADMIN_USERNAME"
ADMIN_PASSWORD_HASH_ENV = "BUILDSHIELD_ADMIN_PASSWORD_HASH"
WORKSPACE_ROOT_ENV = "BUILDSHIELD_WORKSPACE_ROOT"

ALLOWED_ENVIRONMENTS = {"development", "test", "production"}


class RuntimeConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeReadiness:
    environment: str
    workspace_root: str | None
    frontend_ready: bool
    reports_writable: bool
    data_writable: bool


def get_runtime_environment() -> str:
    environment = os.getenv(
        ENVIRONMENT_ENV,
        "development",
    ).strip().lower()

    if environment not in ALLOWED_ENVIRONMENTS:
        raise RuntimeConfigurationError(
            "Runtime environment configuration is invalid."
        )

    return environment


def _require_explicit_production_environment_values() -> None:
    required = (
        ADMIN_USERNAME_ENV,
        ADMIN_PASSWORD_HASH_ENV,
        COOKIE_SECURE_ENV,
        WORKSPACE_ROOT_ENV,
    )

    if any(not os.getenv(name, "").strip() for name in required):
        raise RuntimeConfigurationError(
            "Production runtime configuration is incomplete."
        )


def _directory_is_writable(path: Path) -> bool:
    return (
        path.exists()
        and path.is_dir()
        and os.access(path, os.W_OK)
    )


def validate_runtime_readiness(
    *,
    project_root: Path | None = None,
    frontend_index: Path | None = None,
    reports_root: Path | None = None,
    data_dir: Path | None = None,
) -> RuntimeReadiness:
    environment = get_runtime_environment()

    if environment != "production":
        return RuntimeReadiness(
            environment=environment,
            workspace_root=None,
            frontend_ready=True,
            reports_writable=True,
            data_writable=True,
        )

    _require_explicit_production_environment_values()

    try:
        get_auth_settings()
        workspace_root = get_workspace_root()
    except HTTPException as error:
        raise RuntimeConfigurationError(
            "Production runtime security configuration is invalid."
        ) from error

    root = (project_root or Path.cwd()).resolve()
    resolved_frontend = (
        frontend_index
        or root / "frontend" / "dist" / "index.html"
    )
    resolved_reports = (
        reports_root
        or root / "reports" / "dashboard"
    )
    resolved_data = data_dir or root / "data"

    frontend_ready = (
        resolved_frontend.exists()
        and resolved_frontend.is_file()
    )
    reports_writable = _directory_is_writable(
        resolved_reports
    )
    data_writable = _directory_is_writable(
        resolved_data
    )

    if not frontend_ready:
        raise RuntimeConfigurationError(
            "Production frontend assets are unavailable."
        )

    if not reports_writable or not data_writable:
        raise RuntimeConfigurationError(
            "Production writable runtime directories are unavailable."
        )

    return RuntimeReadiness(
        environment=environment,
        workspace_root=str(workspace_root),
        frontend_ready=frontend_ready,
        reports_writable=reports_writable,
        data_writable=data_writable,
    )


def ensure_runtime_ready() -> None:
    validate_runtime_readiness()


def runtime_readiness_payload() -> dict[str, str]:
    readiness = validate_runtime_readiness()

    return {
        "status": "ready",
        "environment": readiness.environment,
    }
