from __future__ import annotations

import hashlib
import math
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Iterator

from fastapi import Depends, HTTPException, Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from supplysentinel.web.audit import audit_event
from supplysentinel.web.auth import (
    SESSION_COOKIE_NAME,
    SessionRecord,
    require_csrf_token,
)


MAX_REQUEST_BODY_BYTES_ENV = "BUILDSHIELD_MAX_REQUEST_BODY_BYTES"
RATE_LIMIT_REQUESTS_ENV = "BUILDSHIELD_API_RATE_LIMIT_REQUESTS"
RATE_LIMIT_WINDOW_SECONDS_ENV = "BUILDSHIELD_API_RATE_LIMIT_WINDOW_SECONDS"
MAX_CONCURRENT_OPERATIONS_ENV = "BUILDSHIELD_MAX_CONCURRENT_OPERATIONS"

DEFAULT_MAX_REQUEST_BODY_BYTES = 65_536
DEFAULT_RATE_LIMIT_REQUESTS = 30
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_MAX_CONCURRENT_OPERATIONS = 2


@dataclass(frozen=True)
class ResourceControlSettings:
    max_request_body_bytes: int
    rate_limit_requests: int
    rate_limit_window_seconds: int
    max_concurrent_operations: int


@dataclass
class _RateBucket:
    events: deque[float]
    last_seen: float


class _RequestBodyTooLarge(Exception):
    pass


class ConcurrencyLease:
    def __init__(self) -> None:
        self._released = False

    def release(self) -> None:
        global _ACTIVE_OPERATIONS

        if self._released:
            return

        with _STATE_LOCK:
            _ACTIVE_OPERATIONS = max(0, _ACTIVE_OPERATIONS - 1)

        self._released = True


_STATE_LOCK = threading.RLock()
_RATE_BUCKETS: dict[str, _RateBucket] = {}
_ACTIVE_OPERATIONS = 0


def _parse_int_setting(
    env_name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    raw_value = os.getenv(env_name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Resource-control configuration is invalid: {env_name}.",
        ) from error

    if value < minimum or value > maximum:
        raise HTTPException(
            status_code=503,
            detail=f"Resource-control configuration is invalid: {env_name}.",
        )

    return value


def get_resource_control_settings() -> ResourceControlSettings:
    return ResourceControlSettings(
        max_request_body_bytes=_parse_int_setting(
            MAX_REQUEST_BODY_BYTES_ENV,
            DEFAULT_MAX_REQUEST_BODY_BYTES,
            minimum=256,
            maximum=1_048_576,
        ),
        rate_limit_requests=_parse_int_setting(
            RATE_LIMIT_REQUESTS_ENV,
            DEFAULT_RATE_LIMIT_REQUESTS,
            minimum=1,
            maximum=1_000,
        ),
        rate_limit_window_seconds=_parse_int_setting(
            RATE_LIMIT_WINDOW_SECONDS_ENV,
            DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
            minimum=1,
            maximum=3_600,
        ),
        max_concurrent_operations=_parse_int_setting(
            MAX_CONCURRENT_OPERATIONS_ENV,
            DEFAULT_MAX_CONCURRENT_OPERATIONS,
            minimum=1,
            maximum=16,
        ),
    )


def _session_rate_key(
    request: Request,
    session: SessionRecord,
) -> str:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        material = session_id
    else:
        material = session.username

    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()

    return f"session:{digest}"


def _consume_rate_limit(
    key: str,
    *,
    max_requests: int,
    window_seconds: int,
    now: float | None = None,
) -> None:
    current_time = time.monotonic() if now is None else now
    cutoff = current_time - window_seconds

    with _STATE_LOCK:
        bucket = _RATE_BUCKETS.get(key)

        if bucket is None:
            bucket = _RateBucket(
                events=deque(),
                last_seen=current_time,
            )
            _RATE_BUCKETS[key] = bucket

        while bucket.events and bucket.events[0] <= cutoff:
            bucket.events.popleft()

        if len(bucket.events) >= max_requests:
            oldest = bucket.events[0]
            retry_after = max(
                1,
                math.ceil(window_seconds - (current_time - oldest)),
            )
            audit_event(
                "resource.rate_limit",
                outcome="blocked",
                reason="rate_limit_exceeded",
                details={
                    "limit": max_requests,
                    "window_seconds": window_seconds,
                },
            )
            raise HTTPException(
                status_code=429,
                detail="Too many security operations. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        bucket.events.append(current_time)
        bucket.last_seen = current_time

        if len(_RATE_BUCKETS) > 256:
            stale_keys = [
                bucket_key
                for bucket_key, candidate in _RATE_BUCKETS.items()
                if candidate.last_seen <= cutoff
            ]

            for stale_key in stale_keys:
                _RATE_BUCKETS.pop(stale_key, None)


def acquire_concurrency_slot(
    max_concurrent_operations: int,
) -> ConcurrencyLease:
    global _ACTIVE_OPERATIONS

    with _STATE_LOCK:
        if _ACTIVE_OPERATIONS >= max_concurrent_operations:
            audit_event(
                "resource.concurrency",
                outcome="blocked",
                reason="concurrency_limit_exceeded",
                details={
                    "limit": max_concurrent_operations,
                },
            )
            raise HTTPException(
                status_code=429,
                detail="Too many concurrent security operations.",
                headers={"Retry-After": "1"},
            )

        _ACTIVE_OPERATIONS += 1

    return ConcurrencyLease()


def require_expensive_operation_access(
    request: Request,
    session: SessionRecord = Depends(require_csrf_token),
) -> Iterator[SessionRecord]:
    settings = get_resource_control_settings()
    rate_key = _session_rate_key(request, session)

    _consume_rate_limit(
        rate_key,
        max_requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

    lease = acquire_concurrency_slot(
        settings.max_concurrent_operations
    )

    try:
        yield session
    finally:
        lease.release()


def reset_resource_control_state() -> None:
    global _ACTIVE_OPERATIONS

    with _STATE_LOCK:
        _RATE_BUCKETS.clear()
        _ACTIVE_OPERATIONS = 0


async def _send_json_error(
    scope: Scope,
    receive: Receive,
    send: Send,
    *,
    status_code: int,
    detail: str,
    headers: dict[str, str] | None = None,
) -> None:
    response = JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=headers,
    )
    await response(scope, receive, send)


class RequestBodyLimitMiddleware:
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

        method = str(scope.get("method", "")).upper()
        path = str(scope.get("path", ""))

        if (
            not path.startswith("/api/")
            or method not in {"POST", "PUT", "PATCH", "DELETE"}
        ):
            await self.app(scope, receive, send)
            return

        try:
            settings = get_resource_control_settings()
        except HTTPException as error:
            await _send_json_error(
                scope,
                receive,
                send,
                status_code=error.status_code,
                detail=str(error.detail),
                headers=error.headers,
            )
            return

        max_bytes = settings.max_request_body_bytes

        content_length: int | None = None
        for raw_name, raw_value in scope.get("headers", []):
            if raw_name.lower() == b"content-length":
                try:
                    content_length = int(raw_value.decode("ascii"))
                except (UnicodeDecodeError, ValueError):
                    content_length = None
                break

        if content_length is not None and content_length > max_bytes:
            audit_event(
                "resource.request_body",
                outcome="blocked",
                reason="content_length_exceeded",
                details={
                    "limit_bytes": max_bytes,
                    "method": method,
                },
            )
            await _send_json_error(
                scope,
                receive,
                send,
                status_code=413,
                detail="Request body exceeds the configured size limit.",
            )
            return

        consumed = 0

        async def limited_receive() -> Message:
            nonlocal consumed

            message = await receive()

            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))

                if consumed > max_bytes:
                    audit_event(
                        "resource.request_body",
                        outcome="blocked",
                        reason="streamed_body_exceeded",
                        details={
                            "limit_bytes": max_bytes,
                            "method": method,
                        },
                    )
                    raise _RequestBodyTooLarge

            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            await _send_json_error(
                scope,
                receive,
                send,
                status_code=413,
                detail="Request body exceeds the configured size limit.",
            )
