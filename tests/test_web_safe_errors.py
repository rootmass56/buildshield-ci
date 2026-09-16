from __future__ import annotations

from fastapi.testclient import TestClient

import supplysentinel.web.app as web_app
from supplysentinel.core.resource_budget import RepositoryResourceLimitError
from supplysentinel.web.app import app
from supplysentinel.web.error_handling import (
    GENERIC_INTERNAL_ERROR_DETAIL,
    safe_internal_error,
)


SECRET_ERROR = (
    "INTERNAL_SECRET token=super-secret "
    "path=C:\\Users\\private\\sensitive.txt"
)


def _csrf_headers(token: str) -> dict[str, str]:
    return {"X-CSRF-Token": token}


def test_safe_internal_error_only_returns_allowlisted_public_detail():
    error = safe_internal_error("scan")

    assert error.status_code == 500
    assert error.detail == "Repository scan failed."
    assert "secret" not in str(error.detail).lower()

    unknown = safe_internal_error("not-registered")

    assert unknown.status_code == 500
    assert unknown.detail == GENERIC_INTERNAL_ERROR_DETAIL


def test_scan_internal_exception_is_not_disclosed(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client

    def fail_scan(_target: str):
        raise RuntimeError(SECRET_ERROR)

    monkeypatch.setattr(web_app, "scan_repository", fail_scan)

    response = client.post(
        "/api/scan",
        headers=_csrf_headers(csrf_token),
        json={
            "target_path": "samples/secure-repo",
            "policy_path": None,
            "report_formats": [],
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Repository scan failed."}
    assert SECRET_ERROR not in response.text
    assert "super-secret" not in response.text
    assert "sensitive.txt" not in response.text


def test_inventory_internal_exception_is_not_disclosed(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client

    def fail_inventory(_target: str):
        raise RuntimeError(SECRET_ERROR)

    monkeypatch.setattr(
        web_app,
        "build_dependency_inventory",
        fail_inventory,
    )

    response = client.post(
        "/api/inventory",
        headers=_csrf_headers(csrf_token),
        json={"target_path": "samples/secure-repo"},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Dependency inventory failed."}
    assert SECRET_ERROR not in response.text


def test_osv_internal_exception_is_not_disclosed(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client

    def fail_osv(**_kwargs):
        raise RuntimeError(SECRET_ERROR)

    monkeypatch.setattr(
        web_app,
        "build_osv_vulnerability_report",
        fail_osv,
    )

    response = client.post(
        "/api/vulnerability-intelligence",
        headers=_csrf_headers(csrf_token),
        json={
            "target_path": "samples/secure-repo",
            "online_lookup": False,
            "timeout_seconds": 10,
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Vulnerability intelligence failed."
    }
    assert SECRET_ERROR not in response.text


def test_compare_internal_exception_is_not_disclosed(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client

    def fail_scan(_target: str):
        raise RuntimeError(SECRET_ERROR)

    monkeypatch.setattr(web_app, "scan_repository", fail_scan)

    response = client.post(
        "/api/compare",
        headers=_csrf_headers(csrf_token),
        json={
            "baseline_path": "samples/vulnerable-repo",
            "target_path": "samples/secure-repo",
            "baseline_label": "Baseline",
            "target_label": "Target",
            "report_formats": [],
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Repository comparison failed."}
    assert SECRET_ERROR not in response.text


def test_controlled_resource_limit_error_remains_413(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client

    def fail_scan(_target: str):
        raise RepositoryResourceLimitError(
            "Repository scan resource budget exceeded: test limit."
        )

    monkeypatch.setattr(web_app, "scan_repository", fail_scan)

    response = client.post(
        "/api/scan",
        headers=_csrf_headers(csrf_token),
        json={
            "target_path": "samples/secure-repo",
            "policy_path": None,
            "report_formats": [],
        },
    )

    assert response.status_code == 413
    assert "resource budget exceeded" in response.json()["detail"]


def test_unhandled_api_exception_uses_generic_json_boundary(
    authenticated_client,
    monkeypatch,
):
    _fixture_client, _csrf_token = authenticated_client

    def fail_history(*, limit: int):
        raise RuntimeError(SECRET_ERROR)

    monkeypatch.setattr(web_app, "get_recent_scan_history", fail_history)

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    login = client.post(
        "/api/auth/login",
        json={
            "username": "test-admin",
            "password": "test-password",
        },
    )

    assert login.status_code == 200

    response = client.get("/api/history")

    assert response.status_code == 500
    assert response.json() == {
        "detail": GENERIC_INTERNAL_ERROR_DETAIL
    }
    assert SECRET_ERROR not in response.text
    assert "super-secret" not in response.text
    client.close()
