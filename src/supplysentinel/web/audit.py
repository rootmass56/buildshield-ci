from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from supplysentinel.web.logging_utils import (
    LOGGER,
    current_request_id,
)


REDACTED = "[REDACTED]"
MAX_AUDIT_TEXT_LENGTH = 256
MAX_AUDIT_COLLECTION_ITEMS = 32

_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "session",
    "csrf",
    "cookie",
    "authorization",
    "credential",
    "api_key",
    "apikey",
    "private_key",
    "hash",
)


def _normalize_text(value: str) -> str:
    normalized = (
        value.replace("\r", " ")
        .replace("\n", " ")
        .replace("\t", " ")
        .strip()
    )

    if len(normalized) > MAX_AUDIT_TEXT_LENGTH:
        return normalized[:MAX_AUDIT_TEXT_LENGTH] + "…"

    return normalized


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower()

    return any(
        fragment in normalized
        for fragment in _SENSITIVE_KEY_FRAGMENTS
    )


def sanitize_audit_value(
    value: Any,
    *,
    key: str | None = None,
    depth: int = 0,
) -> Any:
    if key is not None and _is_sensitive_key(key):
        return REDACTED

    if depth > 4:
        return "[TRUNCATED]"

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _normalize_text(value)

    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}

        for index, (raw_key, raw_value) in enumerate(value.items()):
            if index >= MAX_AUDIT_COLLECTION_ITEMS:
                sanitized["_truncated"] = True
                break

            field_name = _normalize_text(str(raw_key))

            sanitized[field_name] = sanitize_audit_value(
                raw_value,
                key=field_name,
                depth=depth + 1,
            )

        return sanitized

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [
            sanitize_audit_value(
                item,
                depth=depth + 1,
            )
            for item in list(value)[:MAX_AUDIT_COLLECTION_ITEMS]
        ]

    return _normalize_text(type(value).__name__)


def audit_event(
    event: str,
    *,
    outcome: str,
    actor: str | None = None,
    operation: str | None = None,
    reason: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> None:
    safe_event = _normalize_text(event)
    safe_outcome = _normalize_text(outcome)
    safe_actor = (
        _normalize_text(actor)
        if actor is not None
        else None
    )
    safe_operation = (
        _normalize_text(operation)
        if operation is not None
        else None
    )
    safe_reason = (
        _normalize_text(reason)
        if reason is not None
        else None
    )
    safe_details = (
        sanitize_audit_value(details)
        if details is not None
        else None
    )

    LOGGER.info(
        "audit_event",
        extra={
            "event": safe_event,
            "request_id": current_request_id(),
            "outcome": safe_outcome,
            "actor": safe_actor,
            "operation": safe_operation,
            "reason": safe_reason,
            "details": safe_details,
        },
    )
