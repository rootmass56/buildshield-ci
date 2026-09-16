from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

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
    verify_password,
)


client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def _close_module_client():
    yield
    client.close()


@pytest.fixture(autouse=True)
def clean_auth_state():
    reset_auth_state()
    client.cookies.clear()
    yield
    client.cookies.clear()
    reset_auth_state()


@pytest.fixture
def configured_auth(monkeypatch):
    monkeypatch.setenv(ADMIN_USERNAME_ENV, "admin")
    monkeypatch.setenv(
        ADMIN_PASSWORD_HASH_ENV,
        hash_password(
            "correct-horse-battery-staple",
            iterations=100_000,
            salt=b"0123456789abcdef",
        ),
    )
    monkeypatch.setenv(SESSION_TTL_ENV, "3600")
    monkeypatch.setenv(COOKIE_SECURE_ENV, "false")
    monkeypatch.setenv(LOGIN_MAX_FAILURES_ENV, "5")
    monkeypatch.setenv(LOGIN_LOCKOUT_SECONDS_ENV, "60")


def test_password_hash_verification_round_trip():
    encoded = hash_password(
        "example-password",
        iterations=100_000,
        salt=b"0123456789abcdef",
    )

    assert verify_password("example-password", encoded) is True
    assert verify_password("wrong-password", encoded) is False


def test_login_fails_closed_when_authentication_is_not_configured(monkeypatch):
    monkeypatch.delenv(ADMIN_USERNAME_ENV, raising=False)
    monkeypatch.delenv(ADMIN_PASSWORD_HASH_ENV, raising=False)

    response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "anything",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Authentication is not configured."


def test_valid_login_creates_http_only_strict_session_cookie(configured_auth):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["authenticated"] is True
    assert data["username"] == "admin"
    assert data["csrf_token"]
    assert data["expires_in_seconds"] == 3600

    set_cookie = response.headers["set-cookie"].lower()

    assert "buildshield_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=strict" in set_cookie


def test_invalid_login_returns_generic_unauthorized(configured_auth):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."


def test_session_endpoint_reports_authenticated_session(configured_auth):
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "correct-horse-battery-staple",
        },
    )

    assert login_response.status_code == 200

    response = client.get("/api/auth/session")

    assert response.status_code == 200

    data = response.json()

    assert data["authenticated"] is True
    assert data["username"] == "admin"
    assert data["csrf_token"] == login_response.json()["csrf_token"]


def test_logout_requires_csrf_token(configured_auth):
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "correct-horse-battery-staple",
        },
    )

    assert login_response.status_code == 200

    response = client.post("/api/auth/logout")

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed."


def test_logout_invalidates_session(configured_auth):
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "correct-horse-battery-staple",
        },
    )

    csrf_token = login_response.json()["csrf_token"]

    logout_response = client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert logout_response.status_code == 200
    assert logout_response.json()["authenticated"] is False

    session_response = client.get("/api/auth/session")

    assert session_response.status_code == 200
    assert session_response.json()["authenticated"] is False


def test_repeated_failed_logins_trigger_temporary_lockout(
    monkeypatch,
    configured_auth,
):
    monkeypatch.setenv(LOGIN_MAX_FAILURES_ENV, "2")
    monkeypatch.setenv(LOGIN_LOCKOUT_SECONDS_ENV, "60")

    for _ in range(2):
        response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "wrong-password",
            },
        )
        assert response.status_code == 401

    locked_response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "correct-horse-battery-staple",
        },
    )

    assert locked_response.status_code == 429
    assert "Retry-After" in locked_response.headers


def test_public_health_and_homepage_remain_available_without_authentication():
    health_response = client.get("/health")
    home_response = client.get("/")

    assert health_response.status_code == 200
    assert home_response.status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/api/sample-repositories",
        "/api/history",
        "/api/history/trend",
        "/api/reports",
        "/api/reports/fake-run/fake-report.json",
    ],
)
def test_sensitive_get_endpoints_require_authentication(path):
    response = client.get(path)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (
            "/api/scan",
            {
                "target_path": "samples/secure-repo",
                "policy_path": "buildshield-policy.yml",
                "report_formats": [],
            },
        ),
        (
            "/api/inventory",
            {
                "target_path": "samples/secure-repo",
            },
        ),
        (
            "/api/vulnerability-intelligence",
            {
                "target_path": "samples/secure-repo",
                "online_lookup": False,
                "timeout_seconds": 3,
            },
        ),
        (
            "/api/compare",
            {
                "baseline_path": "samples/vulnerable-repo",
                "target_path": "samples/secure-repo",
                "baseline_label": "Vulnerable",
                "target_label": "Secure",
                "report_formats": [],
            },
        ),
    ],
)
def test_sensitive_post_endpoints_require_authentication(path, payload):
    response = client.post(path, json=payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_authenticated_state_change_requires_csrf(configured_auth):
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "correct-horse-battery-staple",
        },
    )

    assert login_response.status_code == 200

    response = client.post(
        "/api/inventory",
        json={
            "target_path": "samples/secure-repo",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed."


def test_authenticated_state_change_accepts_valid_csrf(configured_auth):
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "admin",
            "password": "correct-horse-battery-staple",
        },
    )

    csrf_token = login_response.json()["csrf_token"]

    response = client.post(
        "/api/inventory",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "target_path": "samples/secure-repo",
        },
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "inventory"
