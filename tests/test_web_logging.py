from __future__ import annotations

import json
import logging
import re

from fastapi.testclient import TestClient

import supplysentinel.web.app as web_app
import supplysentinel.web.logging_utils as logging_utils
from supplysentinel.web.app import app
from supplysentinel.web.logging_utils import (
    JsonLogFormatter,
    REQUEST_ID_HEADER,
    log_internal_failure,
)


REQUEST_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
SECRET_ERROR = (
    "password=top-secret "
    "session=deadbeef "
    "csrf=should-not-log "
    "C:\\Users\\private\\secret.txt"
)


def test_response_receives_server_generated_request_id():
    client = TestClient(app)

    first = client.get("/health")
    second = client.get("/health")

    first_id = first.headers[REQUEST_ID_HEADER]
    second_id = second.headers[REQUEST_ID_HEADER]

    assert REQUEST_ID_PATTERN.fullmatch(first_id)
    assert REQUEST_ID_PATTERN.fullmatch(second_id)
    assert first_id != second_id


def test_client_supplied_request_id_is_not_trusted():
    client = TestClient(app)

    response = client.get(
        "/health",
        headers={REQUEST_ID_HEADER: "client-controlled-id"},
    )

    response_id = response.headers[REQUEST_ID_HEADER]

    assert response_id != "client-controlled-id"
    assert REQUEST_ID_PATTERN.fullmatch(response_id)


def test_structured_formatter_ignores_sensitive_extra_fields():
    formatter = JsonLogFormatter()

    record = logging.LogRecord(
        name="buildshield.security",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.event = "request.completed"
    record.request_id = "a" * 32
    record.method = "POST"
    record.path = "/api/scan"
    record.status_code = 200
    record.password = "top-secret"
    record.session_token = "deadbeef"
    record.csrf_token = "should-not-log"
    record.raw_body = '{"password":"top-secret"}'

    payload = formatter.format(record)
    decoded = json.loads(payload)

    assert decoded["event"] == "request.completed"
    assert decoded["request_id"] == "a" * 32
    assert decoded["path"] == "/api/scan"
    assert "top-secret" not in payload
    assert "deadbeef" not in payload
    assert "should-not-log" not in payload
    assert "raw_body" not in decoded
    assert "password" not in decoded
    assert "session_token" not in decoded
    assert "csrf_token" not in decoded


def test_internal_failure_logging_omits_exception_message(monkeypatch):
    captured: dict[str, object] = {}

    class FakeLogger:
        def error(self, message, *, extra):
            captured["message"] = message
            captured["extra"] = dict(extra)

    monkeypatch.setattr(
        logging_utils,
        "LOGGER",
        FakeLogger(),
    )

    log_internal_failure(
        operation="scan",
        error=RuntimeError(SECRET_ERROR),
        request_id="b" * 32,
    )

    serialized = json.dumps(captured)

    assert "RuntimeError" in serialized
    assert "operation.failed" in serialized
    assert SECRET_ERROR not in serialized
    assert "top-secret" not in serialized
    assert "deadbeef" not in serialized


def test_request_log_uses_path_without_query_string(monkeypatch):
    events: list[dict[str, object]] = []

    def capture_event(**event):
        events.append(dict(event))

    monkeypatch.setattr(
        logging_utils,
        "log_request_completed",
        capture_event,
    )

    client = TestClient(app)

    response = client.get(
        "/health?token=super-secret&password=hidden"
    )

    assert response.status_code == 200
    assert events

    event = events[-1]

    assert event["path"] == "/health"
    assert event["method"] == "GET"
    assert event["status_code"] == 200

    serialized = json.dumps(event)

    assert "super-secret" not in serialized
    assert "password" not in serialized
    assert "token=" not in serialized


def test_unhandled_api_exception_has_correlation_header(
    authenticated_client,
    monkeypatch,
):
    _client, _csrf_token = authenticated_client

    def fail_history(*, limit: int):
        raise RuntimeError(SECRET_ERROR)

    monkeypatch.setattr(
        web_app,
        "get_recent_scan_history",
        fail_history,
    )

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
    assert REQUEST_ID_PATTERN.fullmatch(
        response.headers[REQUEST_ID_HEADER]
    )
    assert response.headers["Cache-Control"] == "no-store"
    assert SECRET_ERROR not in response.text


def test_safe_endpoint_error_has_request_id_and_no_secret(
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
        headers={"X-CSRF-Token": csrf_token},
        json={"target_path": "samples/secure-repo"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Dependency inventory failed."
    }
    assert REQUEST_ID_PATTERN.fullmatch(
        response.headers[REQUEST_ID_HEADER]
    )
    assert SECRET_ERROR not in response.text
