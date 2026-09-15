from __future__ import annotations

import pytest
from fastapi import HTTPException

import supplysentinel.web.app as web_app
from supplysentinel.web.resource_controls import (
    MAX_CONCURRENT_OPERATIONS_ENV,
    MAX_REQUEST_BODY_BYTES_ENV,
    RATE_LIMIT_REQUESTS_ENV,
    RATE_LIMIT_WINDOW_SECONDS_ENV,
    acquire_concurrency_slot,
    get_resource_control_settings,
    reset_resource_control_state,
)


def _csrf_headers(token: str) -> dict[str, str]:
    return {"X-CSRF-Token": token}


@pytest.fixture(autouse=True)
def _reset_resource_controls():
    reset_resource_control_state()
    yield
    reset_resource_control_state()


def test_default_resource_control_settings_are_bounded(monkeypatch):
    for env_name in (
        MAX_REQUEST_BODY_BYTES_ENV,
        RATE_LIMIT_REQUESTS_ENV,
        RATE_LIMIT_WINDOW_SECONDS_ENV,
        MAX_CONCURRENT_OPERATIONS_ENV,
    ):
        monkeypatch.delenv(env_name, raising=False)

    settings = get_resource_control_settings()

    assert 256 <= settings.max_request_body_bytes <= 1_048_576
    assert 1 <= settings.rate_limit_requests <= 1_000
    assert 1 <= settings.rate_limit_window_seconds <= 3_600
    assert 1 <= settings.max_concurrent_operations <= 16


def test_invalid_resource_control_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv(MAX_CONCURRENT_OPERATIONS_ENV, "0")

    with pytest.raises(HTTPException) as error:
        get_resource_control_settings()

    assert error.value.status_code == 503


def test_api_rejects_oversized_request_body(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client
    monkeypatch.setenv(MAX_REQUEST_BODY_BYTES_ENV, "256")

    response = client.post(
        "/api/scan",
        headers=_csrf_headers(csrf_token),
        json={
            "target_path": "x" * 1_000,
            "policy_path": None,
            "report_formats": [],
        },
    )

    assert response.status_code == 413
    assert "size limit" in response.json()["detail"]


def test_api_allows_normal_request_under_body_limit(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client
    monkeypatch.setenv(MAX_REQUEST_BODY_BYTES_ENV, "2048")

    response = client.post(
        "/api/inventory",
        headers=_csrf_headers(csrf_token),
        json={"target_path": "samples/secure-repo"},
    )

    assert response.status_code == 200


def test_authenticated_expensive_operations_are_rate_limited(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client

    monkeypatch.setenv(RATE_LIMIT_REQUESTS_ENV, "2")
    monkeypatch.setenv(RATE_LIMIT_WINDOW_SECONDS_ENV, "60")
    monkeypatch.setenv(MAX_CONCURRENT_OPERATIONS_ENV, "2")

    statuses = []

    for _ in range(3):
        response = client.post(
            "/api/inventory",
            headers=_csrf_headers(csrf_token),
            json={"target_path": "samples/secure-repo"},
        )
        statuses.append(response.status_code)

    assert statuses == [200, 200, 429]

    limited_response = client.post(
        "/api/inventory",
        headers=_csrf_headers(csrf_token),
        json={"target_path": "samples/secure-repo"},
    )

    assert limited_response.status_code == 429
    assert "Retry-After" in limited_response.headers


def test_concurrency_gate_rejects_and_recovers_without_sleep():
    first_lease = acquire_concurrency_slot(1)

    try:
        with pytest.raises(HTTPException) as error:
            acquire_concurrency_slot(1)

        assert error.value.status_code == 429
        assert error.value.headers == {"Retry-After": "1"}
    finally:
        first_lease.release()

    second_lease = acquire_concurrency_slot(1)
    second_lease.release()


def test_endpoint_guard_releases_concurrency_after_failure(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client

    monkeypatch.setenv(MAX_CONCURRENT_OPERATIONS_ENV, "1")
    monkeypatch.setenv(RATE_LIMIT_REQUESTS_ENV, "10")
    monkeypatch.setenv(RATE_LIMIT_WINDOW_SECONDS_ENV, "60")

    def fail_inventory(_target: str):
        raise RuntimeError("controlled test failure")

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

    lease = acquire_concurrency_slot(1)
    lease.release()
