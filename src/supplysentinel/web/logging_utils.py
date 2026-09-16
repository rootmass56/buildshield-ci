from __future__ import annotations

import contextvars
import json
import logging
import re
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send


REQUEST_ID_HEADER = "X-Request-ID"
LOGGER_NAME = "buildshield.security"

_REQUEST_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_REQUEST_ID_CONTEXT: contextvars.ContextVar[str | None] = (
    contextvars.ContextVar(
        "buildshield_request_id",
        default=None,
    )
)

_SAFE_EXTRA_FIELDS = (
    "event",
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "operation",
    "exception_type",
    "outcome",
    "actor",
    "reason",
    "details",
)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field_name in _SAFE_EXTRA_FIELDS:
            value = getattr(record, field_name, None)

            if value is not None:
                payload[field_name] = value

        return json.dumps(
            payload,
            separators=(",", ":"),
            sort_keys=True,
        )


LOGGER = logging.getLogger(LOGGER_NAME)


def configure_structured_logging() -> None:
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False

    if any(
        getattr(handler, "_buildshield_structured", False)
        for handler in LOGGER.handlers
    ):
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    handler._buildshield_structured = True  # type: ignore[attr-defined]
    LOGGER.addHandler(handler)


def new_request_id() -> str:
    return uuid4().hex


def current_request_id() -> str | None:
    return _REQUEST_ID_CONTEXT.get()


def request_id_from_request(request: Request) -> str:
    existing = getattr(request.state, "request_id", None)

    if (
        isinstance(existing, str)
        and _REQUEST_ID_PATTERN.fullmatch(existing)
    ):
        return existing

    request_id = new_request_id()
    request.state.request_id = request_id

    return request_id


def log_request_completed(
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> None:
    LOGGER.info(
        "request_completed",
        extra={
            "event": "request.completed",
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 3),
        },
    )


def log_internal_failure(
    *,
    operation: str,
    error: Exception,
    request_id: str | None = None,
) -> None:
    LOGGER.error(
        "internal_operation_failed",
        extra={
            "event": "operation.failed",
            "request_id": request_id or current_request_id(),
            "operation": operation,
            "exception_type": type(error).__name__,
        },
    )


def log_unhandled_exception(
    *,
    request: Request,
    error: Exception,
) -> str:
    request_id = request_id_from_request(request)

    LOGGER.error(
        "unhandled_request_exception",
        extra={
            "event": "request.unhandled_exception",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": 500,
            "exception_type": type(error).__name__,
        },
    )

    return request_id


class RequestCorrelationMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        request_id = new_request_id()
        state["request_id"] = request_id

        token = _REQUEST_ID_CONTEXT.set(request_id)
        started = time.perf_counter()
        status_code: int | None = None
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code, response_started

            if message["type"] == "http.response.start":
                response_started = True
                status_code = int(message["status"])

                headers = list(message.get("headers", []))
                headers = [
                    (name, value)
                    for name, value in headers
                    if name.lower() != b"x-request-id"
                ]
                headers.append(
                    (
                        b"x-request-id",
                        request_id.encode("ascii"),
                    )
                )
                message["headers"] = headers

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_request_id,
            )
        except Exception:
            raise
        else:
            if response_started and status_code is not None:
                duration_ms = (
                    time.perf_counter() - started
                ) * 1000.0
                log_request_completed(
                    request_id=request_id,
                    method=str(scope.get("method", "")),
                    path=str(scope.get("path", "")),
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
        finally:
            _REQUEST_ID_CONTEXT.reset(token)
