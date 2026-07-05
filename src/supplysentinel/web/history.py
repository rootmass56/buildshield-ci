import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path.cwd() / "data"
DATABASE_PATH = DATA_DIR / "buildshield_history.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:
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


def save_scan_history(
    run_id: str,
    kind: str,
    target_path: str,
    summary: Any,
    risk_profile: Any,
    policy_evaluation: Any,
    reports: list[dict[str, str]],
) -> dict[str, Any]:
    ensure_database()

    policy_status = policy_status_from_result(policy_evaluation)

    metadata = {
        "summary": model_to_dict(summary),
        "risk_profile": model_to_dict(risk_profile),
        "policy_evaluation": model_to_dict(policy_evaluation),
        "reports": reports,
    }

    created_at = utc_now()

    with sqlite3.connect(DATABASE_PATH) as connection:
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

    with sqlite3.connect(DATABASE_PATH) as connection:
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

    with sqlite3.connect(DATABASE_PATH) as connection:
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

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute("DELETE FROM scan_history")
        connection.commit()

    return {"deleted_rows": cursor.rowcount}