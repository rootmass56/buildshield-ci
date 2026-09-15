import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException


DATA_DIR = Path.cwd() / "data"
DATABASE_PATH = DATA_DIR / "buildshield_history.db"

HISTORY_MAX_ROWS_ENV = "BUILDSHIELD_HISTORY_MAX_ROWS"
HISTORY_RETENTION_DAYS_ENV = "BUILDSHIELD_HISTORY_RETENTION_DAYS"

DEFAULT_HISTORY_MAX_ROWS = 1_000
DEFAULT_HISTORY_RETENTION_DAYS = 90


@dataclass(frozen=True)
class HistoryRetentionSettings:
    max_rows: int
    retention_days: int


def _parse_positive_int(
    env_name: str,
    default: int,
    *,
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
            detail=f"History retention configuration is invalid: {env_name}.",
        ) from error

    if value < 1 or value > maximum:
        raise HTTPException(
            status_code=503,
            detail=f"History retention configuration is invalid: {env_name}.",
        )

    return value


def get_history_retention_settings() -> HistoryRetentionSettings:
    return HistoryRetentionSettings(
        max_rows=_parse_positive_int(
            HISTORY_MAX_ROWS_ENV,
            DEFAULT_HISTORY_MAX_ROWS,
            maximum=100_000,
        ),
        retention_days=_parse_positive_int(
            HISTORY_RETENTION_DAYS_ENV,
            DEFAULT_HISTORY_RETENTION_DAYS,
            maximum=3_650,
        ),
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH, timeout=5.0) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                kind TEXT NOT NULL,
                target_path TEXT NOT NULL,
                security_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                findings_count INTEGER NOT NULL,
                critical_count INTEGER NOT NULL,
                high_count INTEGER NOT NULL,
                medium_count INTEGER NOT NULL,
                low_count INTEGER NOT NULL,
                info_count INTEGER NOT NULL,
                policy_status TEXT NOT NULL,
                build_gate_status TEXT NOT NULL,
                report_count INTEGER NOT NULL,
                metadata_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_scan_history_created_at
            ON scan_history(created_at)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_scan_history_run_id
            ON scan_history(run_id)
            """
        )
        connection.commit()


def model_to_dict(value: Any) -> Any:
    if value is None:
        return None

    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")

    return value


def policy_status_from_result(policy_evaluation: Any) -> str:
    if policy_evaluation is None:
        return "NOT_EVALUATED"

    passed = getattr(policy_evaluation, "passed", None)

    if passed is True:
        return "PASSED"

    if passed is False:
        return "FAILED"

    return "UNKNOWN"


def _prune_scan_history(
    connection: sqlite3.Connection,
    *,
    settings: HistoryRetentionSettings,
    now: datetime,
) -> dict[str, int]:
    cutoff = (
        now.astimezone(timezone.utc)
        - timedelta(days=settings.retention_days)
    ).isoformat()

    age_cursor = connection.execute(
        """
        DELETE FROM scan_history
        WHERE created_at < ?
        """,
        (cutoff,),
    )

    count_cursor = connection.execute(
        """
        DELETE FROM scan_history
        WHERE id NOT IN (
            SELECT id
            FROM scan_history
            ORDER BY id DESC
            LIMIT ?
        )
        """,
        (settings.max_rows,),
    )

    return {
        "age_deleted": max(0, age_cursor.rowcount),
        "count_deleted": max(0, count_cursor.rowcount),
    }


def apply_history_retention(
    *,
    now: datetime | None = None,
) -> dict[str, int]:
    ensure_database()
    settings = get_history_retention_settings()
    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    with sqlite3.connect(DATABASE_PATH, timeout=5.0) as connection:
        result = _prune_scan_history(
            connection,
            settings=settings,
            now=current_time,
        )
        connection.commit()

    return {
        **result,
        "max_rows": settings.max_rows,
        "retention_days": settings.retention_days,
    }


def save_scan_history(
    run_id: str,
    kind: str,
    target_path: str,
    summary: Any,
    risk_profile: Any,
    policy_evaluation: Any,
    reports: list[dict[str, str]],
) -> dict[str, Any]:
    settings = get_history_retention_settings()
    ensure_database()

    policy_status = policy_status_from_result(policy_evaluation)

    metadata = {
        "summary": model_to_dict(summary),
        "risk_profile": model_to_dict(risk_profile),
        "policy_evaluation": model_to_dict(policy_evaluation),
        "reports": reports,
    }

    created_at = utc_now()
    retention_now = datetime.fromisoformat(created_at)

    if retention_now.tzinfo is None:
        retention_now = retention_now.replace(tzinfo=timezone.utc)

    with sqlite3.connect(DATABASE_PATH, timeout=5.0) as connection:
        cursor = connection.execute(
            """
            INSERT INTO scan_history (
                run_id,
                created_at,
                kind,
                target_path,
                security_score,
                risk_level,
                findings_count,
                critical_count,
                high_count,
                medium_count,
                low_count,
                info_count,
                policy_status,
                build_gate_status,
                report_count,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                created_at,
                kind,
                target_path,
                int(summary.security_score),
                str(summary.risk_level),
                int(summary.findings_count),
                int(summary.critical_count),
                int(summary.high_count),
                int(summary.medium_count),
                int(summary.low_count),
                int(summary.info_count),
                policy_status,
                str(risk_profile.build_gate_status),
                len(reports),
                json.dumps(metadata),
            ),
        )

        _prune_scan_history(
            connection,
            settings=settings,
            now=retention_now,
        )

        connection.commit()
        database_id = cursor.lastrowid

    return {
        "id": database_id,
        "run_id": run_id,
        "created_at": created_at,
        "kind": kind,
        "target_path": target_path,
        "security_score": int(summary.security_score),
        "risk_level": str(summary.risk_level),
        "findings_count": int(summary.findings_count),
        "critical_count": int(summary.critical_count),
        "high_count": int(summary.high_count),
        "medium_count": int(summary.medium_count),
        "low_count": int(summary.low_count),
        "info_count": int(summary.info_count),
        "policy_status": policy_status,
        "build_gate_status": str(risk_profile.build_gate_status),
        "report_count": len(reports),
    }


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "run_id": row["run_id"],
        "created_at": row["created_at"],
        "kind": row["kind"],
        "target_path": row["target_path"],
        "security_score": row["security_score"],
        "risk_level": row["risk_level"],
        "findings_count": row["findings_count"],
        "critical_count": row["critical_count"],
        "high_count": row["high_count"],
        "medium_count": row["medium_count"],
        "low_count": row["low_count"],
        "info_count": row["info_count"],
        "policy_status": row["policy_status"],
        "build_gate_status": row["build_gate_status"],
        "report_count": row["report_count"],
    }


def get_recent_scan_history(limit: int = 20) -> list[dict[str, Any]]:
    ensure_database()

    safe_limit = max(1, min(limit, 100))

    with sqlite3.connect(DATABASE_PATH, timeout=5.0) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT *
            FROM scan_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def get_risk_trend(limit: int = 20) -> list[dict[str, Any]]:
    ensure_database()

    safe_limit = max(1, min(limit, 100))

    with sqlite3.connect(DATABASE_PATH, timeout=5.0) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT *
            FROM (
                SELECT *
                FROM scan_history
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (safe_limit,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "run_id": row["run_id"],
            "created_at": row["created_at"],
            "target_path": row["target_path"],
            "security_score": row["security_score"],
            "findings_count": row["findings_count"],
            "critical_count": row["critical_count"],
            "high_count": row["high_count"],
            "policy_status": row["policy_status"],
            "build_gate_status": row["build_gate_status"],
        }
        for row in rows
    ]


def clear_scan_history() -> dict[str, int]:
    ensure_database()

    with sqlite3.connect(DATABASE_PATH, timeout=5.0) as connection:
        cursor = connection.execute("DELETE FROM scan_history")
        connection.commit()

    return {"deleted_rows": cursor.rowcount}


def clear_report_metadata_for_runs(
    run_ids: list[str],
) -> int:
    unique_run_ids = list(dict.fromkeys(run_ids))

    if not unique_run_ids:
        return 0

    ensure_database()
    updated_rows = 0
    chunk_size = 250

    with sqlite3.connect(DATABASE_PATH, timeout=5.0) as connection:
        connection.row_factory = sqlite3.Row

        for start in range(0, len(unique_run_ids), chunk_size):
            chunk = unique_run_ids[start : start + chunk_size]
            placeholders = ",".join("?" for _ in chunk)

            rows = connection.execute(
                f"""
                SELECT id, metadata_json
                FROM scan_history
                WHERE run_id IN ({placeholders})
                """,
                tuple(chunk),
            ).fetchall()

            for row in rows:
                try:
                    metadata = json.loads(row["metadata_json"])
                except (TypeError, ValueError):
                    metadata = {}

                if not isinstance(metadata, dict):
                    metadata = {}

                metadata["reports"] = []

                connection.execute(
                    """
                    UPDATE scan_history
                    SET report_count = 0,
                        metadata_json = ?
                    WHERE id = ?
                    """,
                    (
                        json.dumps(metadata),
                        row["id"],
                    ),
                )
                updated_rows += 1

        connection.commit()

    return updated_rows
