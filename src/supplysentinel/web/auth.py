from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
from dataclasses import dataclass

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field


SESSION_COOKIE_NAME = "buildshield_session"
PASSWORD_SCHEME = "pbkdf2_sha256"
DEFAULT_PBKDF2_ITERATIONS = 600_000

ADMIN_USERNAME_ENV = "BUILDSHIELD_ADMIN_USERNAME"
ADMIN_PASSWORD_HASH_ENV = "BUILDSHIELD_ADMIN_PASSWORD_HASH"
SESSION_TTL_ENV = "BUILDSHIELD_SESSION_TTL_SECONDS"
COOKIE_SECURE_ENV = "BUILDSHIELD_COOKIE_SECURE"
LOGIN_MAX_FAILURES_ENV = "BUILDSHIELD_LOGIN_MAX_FAILURES"
LOGIN_LOCKOUT_SECONDS_ENV = "BUILDSHIELD_LOGIN_LOCKOUT_SECONDS"

DEFAULT_SESSION_TTL_SECONDS = 3600
DEFAULT_LOGIN_MAX_FAILURES = 5
DEFAULT_LOGIN_LOCKOUT_SECONDS = 60

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@dataclass(frozen=True)
class AuthSettings:
    username: str
    password_hash: str
    session_ttl_seconds: int
    cookie_secure: bool
    login_max_failures: int
    login_lockout_seconds: int


@dataclass
class SessionRecord:
    username: str
    csrf_token: str
    expires_at: float


@dataclass
class LoginFailureRecord:
    failures: int
    locked_until: float


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


_SESSION_STORE: dict[str, SessionRecord] = {}
_LOGIN_FAILURES: dict[str, LoginFailureRecord] = {}
_STATE_LOCK = threading.RLock()


def _parse_positive_int(
    env_name: str,
    default: int,
    minimum: int = 1,
    maximum: int = 86_400,
) -> int:
    raw_value = os.getenv(env_name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Authentication configuration is invalid: {env_name}.",
        ) from error

    if value < minimum or value > maximum:
        raise HTTPException(
            status_code=503,
            detail=f"Authentication configuration is invalid: {env_name}.",
        )

    return value


def _parse_bool(env_name: str, default: bool) -> bool:
    raw_value = os.getenv(env_name)

    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise HTTPException(
        status_code=503,
        detail=f"Authentication configuration is invalid: {env_name}.",
    )


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(
    password: str,
    *,
    iterations: int = DEFAULT_PBKDF2_ITERATIONS,
    salt: bytes | None = None,
) -> str:
    if not password:
        raise ValueError("Password must not be empty.")

    if iterations < 100_000:
        raise ValueError("PBKDF2 iteration count is too low.")

    password_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        password_salt,
        iterations,
    )

    return (
        f"{PASSWORD_SCHEME}"
        f"${iterations}"
        f"${_b64encode(password_salt)}"
        f"${_b64encode(digest)}"
    )


def _parse_password_hash(encoded: str) -> tuple[int, bytes, bytes]:
    try:
        scheme, iteration_text, salt_text, digest_text = encoded.split("$", 3)
        iterations = int(iteration_text)
        salt = _b64decode(salt_text)
        expected_digest = _b64decode(digest_text)
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid password hash format.") from error

    if scheme != PASSWORD_SCHEME:
        raise ValueError("Unsupported password hash scheme.")

    if iterations < 100_000 or iterations > 2_000_000:
        raise ValueError("Invalid PBKDF2 iteration count.")

    if len(salt) < 16 or len(expected_digest) != 32:
        raise ValueError("Invalid password hash material.")

    return iterations, salt, expected_digest


def verify_password(password: str, encoded: str) -> bool:
    try:
        iterations, salt, expected_digest = _parse_password_hash(encoded)
    except ValueError:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )

    return hmac.compare_digest(actual_digest, expected_digest)


def get_auth_settings() -> AuthSettings:
    username = os.getenv(ADMIN_USERNAME_ENV, "").strip()
    password_hash = os.getenv(ADMIN_PASSWORD_HASH_ENV, "").strip()

    if not username or not password_hash:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured.",
        )

    try:
        _parse_password_hash(password_hash)
    except ValueError as error:
        raise HTTPException(
            status_code=503,
            detail="Authentication password hash is invalid.",
        ) from error

    return AuthSettings(
        username=username,
        password_hash=password_hash,
        session_ttl_seconds=_parse_positive_int(
            SESSION_TTL_ENV,
            DEFAULT_SESSION_TTL_SECONDS,
            minimum=300,
            maximum=86_400,
        ),
        cookie_secure=_parse_bool(COOKIE_SECURE_ENV, False),
        login_max_failures=_parse_positive_int(
            LOGIN_MAX_FAILURES_ENV,
            DEFAULT_LOGIN_MAX_FAILURES,
            minimum=1,
            maximum=100,
        ),
        login_lockout_seconds=_parse_positive_int(
            LOGIN_LOCKOUT_SECONDS_ENV,
            DEFAULT_LOGIN_LOCKOUT_SECONDS,
            minimum=1,
            maximum=3600,
        ),
    )


def _client_key(request: Request) -> str:
    if request.client is None or request.client.host is None:
        return "unknown"

    return request.client.host


def _check_login_lockout(
    client_key: str,
    settings: AuthSettings,
    now: float,
) -> None:
    with _STATE_LOCK:
        record = _LOGIN_FAILURES.get(client_key)

        if record is None:
            return

        if record.locked_until > now:
            retry_after = max(1, int(record.locked_until - now))
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        if record.locked_until > 0 and record.locked_until <= now:
            _LOGIN_FAILURES.pop(client_key, None)


def _record_login_failure(
    client_key: str,
    settings: AuthSettings,
    now: float,
) -> None:
    with _STATE_LOCK:
        current = _LOGIN_FAILURES.get(client_key)
        failures = 1 if current is None else current.failures + 1

        locked_until = 0.0
        if failures >= settings.login_max_failures:
            locked_until = now + settings.login_lockout_seconds

        _LOGIN_FAILURES[client_key] = LoginFailureRecord(
            failures=failures,
            locked_until=locked_until,
        )


def _clear_login_failures(client_key: str) -> None:
    with _STATE_LOCK:
        _LOGIN_FAILURES.pop(client_key, None)


def _create_session(
    username: str,
    ttl_seconds: int,
    now: float,
) -> tuple[str, SessionRecord]:
    session_id = secrets.token_urlsafe(32)
    record = SessionRecord(
        username=username,
        csrf_token=secrets.token_urlsafe(32),
        expires_at=now + ttl_seconds,
    )

    with _STATE_LOCK:
        _SESSION_STORE[session_id] = record

    return session_id, record


def _get_session_record(
    session_id: str | None,
    now: float | None = None,
) -> SessionRecord | None:
    if not session_id:
        return None

    current_time = time.time() if now is None else now

    with _STATE_LOCK:
        record = _SESSION_STORE.get(session_id)

        if record is None:
            return None

        if record.expires_at <= current_time:
            _SESSION_STORE.pop(session_id, None)
            return None

        return record


def get_authenticated_session(request: Request) -> SessionRecord | None:
    return _get_session_record(
        request.cookies.get(SESSION_COOKIE_NAME)
    )


def require_authenticated_session(request: Request) -> SessionRecord:
    record = get_authenticated_session(request)

    if record is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    return record


def require_csrf_token(
    request: Request,
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> SessionRecord:
    record = require_authenticated_session(request)

    if not x_csrf_token or not hmac.compare_digest(
        x_csrf_token,
        record.csrf_token,
    ):
        raise HTTPException(
            status_code=403,
            detail="CSRF validation failed.",
        )

    return record


def _invalidate_session(session_id: str | None) -> None:
    if not session_id:
        return

    with _STATE_LOCK:
        _SESSION_STORE.pop(session_id, None)


def reset_auth_state() -> None:
    with _STATE_LOCK:
        _SESSION_STORE.clear()
        _LOGIN_FAILURES.clear()


@router.post("/login")
def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
) -> dict[str, object]:
    settings = get_auth_settings()
    now = time.time()
    client_key = _client_key(request)

    _check_login_lockout(
        client_key=client_key,
        settings=settings,
        now=now,
    )

    username_matches = hmac.compare_digest(
        credentials.username,
        settings.username,
    )
    password_matches = verify_password(
        credentials.password,
        settings.password_hash,
    )

    if not (username_matches and password_matches):
        _record_login_failure(
            client_key=client_key,
            settings=settings,
            now=now,
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    _clear_login_failures(client_key)

    session_id, record = _create_session(
        username=settings.username,
        ttl_seconds=settings.session_ttl_seconds,
        now=now,
    )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )

    return {
        "authenticated": True,
        "username": record.username,
        "csrf_token": record.csrf_token,
        "expires_in_seconds": settings.session_ttl_seconds,
    }


@router.get("/session")
def session_status(request: Request) -> dict[str, object]:
    record = get_authenticated_session(request)

    if record is None:
        return {
            "authenticated": False,
        }

    return {
        "authenticated": True,
        "username": record.username,
        "csrf_token": record.csrf_token,
        "expires_at": record.expires_at,
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> dict[str, bool]:
    record = require_csrf_token(
        request=request,
        x_csrf_token=x_csrf_token,
    )

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    _invalidate_session(session_id)

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="strict",
    )

    return {
        "authenticated": False,
    }
