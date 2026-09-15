from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import supplysentinel.web.runtime_config as runtime_config
from supplysentinel.web.app import app
from supplysentinel.web.auth import hash_password


PRODUCTION_ENV_VARS = (
    runtime_config.ADMIN_USERNAME_ENV,
    runtime_config.ADMIN_PASSWORD_HASH_ENV,
    runtime_config.COOKIE_SECURE_ENV,
    runtime_config.WORKSPACE_ROOT_ENV,
)


def _clear_production_env(monkeypatch):
    for name in PRODUCTION_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def _configure_valid_production(
    monkeypatch,
    workspace_root: Path,
):
    monkeypatch.setenv(
        runtime_config.ENVIRONMENT_ENV,
        "production",
    )
    monkeypatch.setenv(
        runtime_config.ADMIN_USERNAME_ENV,
        "h7c-admin",
    )
    monkeypatch.setenv(
        runtime_config.ADMIN_PASSWORD_HASH_ENV,
        hash_password("H7C-test-password"),
    )
    monkeypatch.setenv(
        runtime_config.COOKIE_SECURE_ENV,
        "false",
    )
    monkeypatch.setenv(
        runtime_config.WORKSPACE_ROOT_ENV,
        str(workspace_root),
    )


def test_development_runtime_does_not_require_production_secrets(
    monkeypatch,
):
    monkeypatch.setenv(
        runtime_config.ENVIRONMENT_ENV,
        "development",
    )
    _clear_production_env(monkeypatch)

    readiness = runtime_config.validate_runtime_readiness()

    assert readiness.environment == "development"
    assert readiness.frontend_ready is True
    assert readiness.reports_writable is True
    assert readiness.data_writable is True


def test_invalid_runtime_environment_fails_closed(monkeypatch):
    monkeypatch.setenv(
        runtime_config.ENVIRONMENT_ENV,
        "unexpected",
    )

    with pytest.raises(
        runtime_config.RuntimeConfigurationError,
        match="environment configuration is invalid",
    ):
        runtime_config.validate_runtime_readiness()


def test_production_runtime_requires_explicit_security_config(
    monkeypatch,
):
    monkeypatch.setenv(
        runtime_config.ENVIRONMENT_ENV,
        "production",
    )
    _clear_production_env(monkeypatch)

    with pytest.raises(
        runtime_config.RuntimeConfigurationError,
        match="configuration is incomplete",
    ):
        runtime_config.validate_runtime_readiness()


def test_production_runtime_rejects_invalid_password_hash(
    tmp_path,
    monkeypatch,
):
    _configure_valid_production(
        monkeypatch,
        tmp_path,
    )
    monkeypatch.setenv(
        runtime_config.ADMIN_PASSWORD_HASH_ENV,
        "not-a-valid-password-hash",
    )

    with pytest.raises(
        runtime_config.RuntimeConfigurationError,
        match="security configuration is invalid",
    ):
        runtime_config.validate_runtime_readiness(
            project_root=tmp_path,
            frontend_index=tmp_path / "frontend.html",
            reports_root=tmp_path / "reports",
            data_dir=tmp_path / "data",
        )


def test_valid_production_runtime_requires_frontend_and_writable_state(
    tmp_path,
    monkeypatch,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    frontend = tmp_path / "frontend" / "dist" / "index.html"
    frontend.parent.mkdir(parents=True)
    frontend.write_text(
        "<!doctype html>",
        encoding="utf-8",
    )

    reports = tmp_path / "reports" / "dashboard"
    reports.mkdir(parents=True)

    data = tmp_path / "data"
    data.mkdir()

    _configure_valid_production(
        monkeypatch,
        workspace,
    )

    readiness = runtime_config.validate_runtime_readiness(
        project_root=tmp_path,
        frontend_index=frontend,
        reports_root=reports,
        data_dir=data,
    )

    assert readiness.environment == "production"
    assert readiness.workspace_root == str(workspace.resolve())
    assert readiness.frontend_ready is True
    assert readiness.reports_writable is True
    assert readiness.data_writable is True


def test_production_runtime_rejects_missing_frontend_assets(
    tmp_path,
    monkeypatch,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    reports = tmp_path / "reports"
    reports.mkdir()

    data = tmp_path / "data"
    data.mkdir()

    _configure_valid_production(
        monkeypatch,
        workspace,
    )

    with pytest.raises(
        runtime_config.RuntimeConfigurationError,
        match="frontend assets are unavailable",
    ):
        runtime_config.validate_runtime_readiness(
            project_root=tmp_path,
            frontend_index=tmp_path / "missing-index.html",
            reports_root=reports,
            data_dir=data,
        )


def test_liveness_and_readiness_are_separate_public_endpoints(
    monkeypatch,
):
    monkeypatch.setenv(
        runtime_config.ENVIRONMENT_ENV,
        "development",
    )

    with TestClient(app) as client:
        liveness = client.get("/health")
        readiness = client.get("/ready")

    assert liveness.status_code == 200
    assert liveness.json()["status"] == "ok"
    assert readiness.status_code == 200
    assert readiness.json() == {
        "status": "ready",
        "environment": "development",
    }
