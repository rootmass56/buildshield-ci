from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

import supplysentinel.web.app as web_app
import supplysentinel.web.audit as audit_module
import supplysentinel.web.auth as auth_module
import supplysentinel.web.resource_controls as resource_controls
from supplysentinel.core.resource_budget import RepositoryResourceLimitError
from supplysentinel.web.audit import (
    REDACTED,
    audit_event,
    sanitize_audit_value,
)
from supplysentinel.web.auth import (
    LOGIN_MAX_FAILURES_ENV,
    reset_auth_state,
)
from supplysentinel.web.resource_controls import (
    _consume_rate_limit,
    acquire_concurrency_slot,
    reset_resource_control_state,
)


SECRET = "super-secret-value"


@pytest.fixture(autouse=True)
def _reset_security_state():
    reset_resource_control_state()
    yield
    reset_resource_control_state()


def test_audit_redaction_handles_nested_sensitive_fields():
    sanitized = sanitize_audit_value(
        {
            "safe_count": 3,
            "password": SECRET,
            "csrf_token": SECRET,
            "nested": {
                "authorization": SECRET,
                "session_id": SECRET,
                "safe": "visible",
            },
        }
    )

    assert sanitized["safe_count"] == 3
    assert sanitized["password"] == REDACTED
    assert sanitized["csrf_token"] == REDACTED
    assert sanitized["nested"]["authorization"] == REDACTED
    assert sanitized["nested"]["session_id"] == REDACTED
    assert sanitized["nested"]["safe"] == "visible"

    serialized = json.dumps(sanitized)

    assert SECRET not in serialized


def test_audit_event_emits_stable_safe_schema(monkeypatch):
    captured: dict[str, object] = {}

    class FakeLogger:
        def info(self, message, *, extra):
            captured["message"] = message
            captured["extra"] = dict(extra)

    monkeypatch.setattr(
        audit_module,
        "LOGGER",
        FakeLogger(),
    )

    audit_event(
        "security.operation",
        outcome="success",
        actor="admin",
        operation="scan",
        reason="completed",
        details={
            "reports_generated": 2,
            "password": SECRET,
            "nested": {"csrf_token": SECRET},
        },
    )

    assert captured["message"] == "audit_event"

    extra = captured["extra"]

    assert extra["event"] == "security.operation"
    assert extra["outcome"] == "success"
    assert extra["actor"] == "admin"
    assert extra["operation"] == "scan"
    assert extra["reason"] == "completed"
    assert extra["details"]["reports_generated"] == 2
    assert extra["details"]["password"] == REDACTED
    assert extra["details"]["nested"]["csrf_token"] == REDACTED
    assert SECRET not in json.dumps(captured)


def test_login_success_failure_lockout_and_logout_are_audited(
    authenticated_client,
    monkeypatch,
):
    client, _initial_csrf = authenticated_client
    events: list[dict[str, object]] = []

    def capture(event, **kwargs):
        events.append({"event": event, **kwargs})

    monkeypatch.setattr(
        auth_module,
        "audit_event",
        capture,
    )
    monkeypatch.setenv(LOGIN_MAX_FAILURES_ENV, "1")

    client.cookies.clear()
    reset_auth_state()

    failure = client.post(
        "/api/auth/login",
        json={
            "username": "test-admin",
            "password": "wrong-password",
        },
    )
    assert failure.status_code == 401

    blocked = client.post(
        "/api/auth/login",
        json={
            "username": "test-admin",
            "password": "wrong-password",
        },
    )
    assert blocked.status_code == 429

    reset_auth_state()

    success = client.post(
        "/api/auth/login",
        json={
            "username": "test-admin",
            "password": "test-password",
        },
    )
    assert success.status_code == 200

    csrf_token = success.json()["csrf_token"]

    logout = client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout.status_code == 200

    outcomes = [
        (
            event["event"],
            event["outcome"],
            event.get("reason"),
        )
        for event in events
    ]

    assert (
        "auth.login",
        "failure",
        "invalid_credentials",
    ) in outcomes
    assert (
        "auth.login",
        "blocked",
        "lockout_active",
    ) in outcomes
    assert (
        "auth.login",
        "success",
        None,
    ) in outcomes
    assert (
        "auth.logout",
        "success",
        None,
    ) in outcomes

    serialized = json.dumps(events)

    assert "wrong-password" not in serialized
    assert csrf_token not in serialized


def test_rate_and_concurrency_rejections_are_audited(monkeypatch):
    events: list[dict[str, object]] = []

    def capture(event, **kwargs):
        events.append({"event": event, **kwargs})

    monkeypatch.setattr(
        resource_controls,
        "audit_event",
        capture,
    )

    _consume_rate_limit(
        "test-key",
        max_requests=1,
        window_seconds=60,
        now=100.0,
    )

    with pytest.raises(HTTPException) as rate_error:
        _consume_rate_limit(
            "test-key",
            max_requests=1,
            window_seconds=60,
            now=101.0,
        )

    assert rate_error.value.status_code == 429

    lease = acquire_concurrency_slot(1)

    try:
        with pytest.raises(HTTPException) as concurrency_error:
            acquire_concurrency_slot(1)

        assert concurrency_error.value.status_code == 429
    finally:
        lease.release()

    event_names = [event["event"] for event in events]

    assert "resource.rate_limit" in event_names
    assert "resource.concurrency" in event_names

    serialized = json.dumps(events)

    assert "test-key" not in serialized


def test_security_operations_emit_success_audit_events(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client
    events: list[dict[str, object]] = []

    def capture(event, **kwargs):
        events.append({"event": event, **kwargs})

    monkeypatch.setattr(
        web_app,
        "audit_event",
        capture,
    )
    monkeypatch.setattr(
        web_app,
        "save_scan_reports",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        web_app,
        "save_scan_history",
        lambda **_kwargs: {},
    )
    monkeypatch.setattr(
        web_app,
        "save_inventory_report",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        web_app,
        "save_vulnerability_intelligence_report",
        lambda **_kwargs: [],
    )
    monkeypatch.setattr(
        web_app,
        "save_comparison_reports",
        lambda **_kwargs: [],
    )

    scan = client.post(
        "/api/scan",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "target_path": "samples/secure-repo",
            "policy_path": None,
            "report_formats": [],
        },
    )
    inventory = client.post(
        "/api/inventory",
        headers={"X-CSRF-Token": csrf_token},
        json={"target_path": "samples/secure-repo"},
    )
    osv = client.post(
        "/api/vulnerability-intelligence",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "target_path": "samples/secure-repo",
            "online_lookup": False,
            "timeout_seconds": 10,
        },
    )
    compare = client.post(
        "/api/compare",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "baseline_path": "samples/vulnerable-repo",
            "target_path": "samples/secure-repo",
            "baseline_label": "Baseline",
            "target_label": "Target",
            "report_formats": [],
        },
    )

    assert scan.status_code == 200
    assert inventory.status_code == 200
    assert osv.status_code == 200
    assert compare.status_code == 200

    successful_operations = {
        event.get("operation")
        for event in events
        if (
            event["event"] == "security.operation"
            and event["outcome"] == "success"
        )
    }

    assert successful_operations == {
        "scan",
        "inventory",
        "vulnerability_intelligence",
        "compare",
    }


def test_scanner_budget_rejection_is_audited_without_raw_error(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client
    events: list[dict[str, object]] = []

    def capture(event, **kwargs):
        events.append({"event": event, **kwargs})

    def fail_scan(_target: str):
        raise RepositoryResourceLimitError(
            "Repository scan resource budget exceeded: "
            "C:\\secret\\private\\repo."
        )

    monkeypatch.setattr(
        web_app,
        "audit_event",
        capture,
    )
    monkeypatch.setattr(
        web_app,
        "scan_repository",
        fail_scan,
    )

    response = client.post(
        "/api/scan",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "target_path": "samples/secure-repo",
            "policy_path": None,
            "report_formats": [],
        },
    )

    assert response.status_code == 413

    assert any(
        event["event"] == "resource.scanner_budget"
        and event["outcome"] == "blocked"
        and event["operation"] == "scan"
        for event in events
    )

    serialized = json.dumps(events)

    assert "C:\\secret\\private\\repo" not in serialized
