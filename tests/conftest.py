from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from supplysentinel.core.scanner import scan_repository
from supplysentinel.web.app import app
from supplysentinel.web.auth import (
    ADMIN_PASSWORD_HASH_ENV,
    ADMIN_USERNAME_ENV,
    COOKIE_SECURE_ENV,
    LOGIN_LOCKOUT_SECONDS_ENV,
    LOGIN_MAX_FAILURES_ENV,
    SESSION_TTL_ENV,
    hash_password,
    reset_auth_state,
)


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def vulnerable_repo(project_root: Path) -> Path:
    return project_root / "samples" / "vulnerable-repo"


@pytest.fixture(scope="session")
def secure_repo(project_root: Path) -> Path:
    return project_root / "samples" / "secure-repo"


@pytest.fixture(scope="session")
def policy_file(project_root: Path) -> Path:
    return project_root / "buildshield-policy.yml"


@pytest.fixture(scope="session")
def vulnerable_scan(vulnerable_repo: Path):
    return scan_repository(str(vulnerable_repo))


@pytest.fixture(scope="session")
def secure_scan(secure_repo: Path):
    return scan_repository(str(secure_repo))


@pytest.fixture
def authenticated_client(monkeypatch):
    reset_auth_state()

    monkeypatch.setenv(ADMIN_USERNAME_ENV, "test-admin")
    monkeypatch.setenv(
        ADMIN_PASSWORD_HASH_ENV,
        hash_password(
            "test-password",
            iterations=100_000,
            salt=b"0123456789abcdef",
        ),
    )
    monkeypatch.setenv(SESSION_TTL_ENV, "3600")
    monkeypatch.setenv(COOKIE_SECURE_ENV, "false")
    monkeypatch.setenv(LOGIN_MAX_FAILURES_ENV, "5")
    monkeypatch.setenv(LOGIN_LOCKOUT_SECONDS_ENV, "60")

    client = TestClient(app)

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "test-admin",
            "password": "test-password",
        },
    )

    assert login_response.status_code == 200

    csrf_token = login_response.json()["csrf_token"]

    try:
        yield client, csrf_token
    finally:
        client.cookies.clear()
        reset_auth_state()
