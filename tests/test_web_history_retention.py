from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import supplysentinel.web.history as history


class SerializableNamespace(SimpleNamespace):
    """Small Pydantic-like test double for history metadata serialization."""

    def model_dump(self, mode: str = "json"):
        assert mode == "json"
        return vars(self).copy()


@pytest.fixture
def isolated_history(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    database_path = data_dir / "history.db"

    monkeypatch.setattr(
        history,
        "DATA_DIR",
        data_dir,
    )
    monkeypatch.setattr(
        history,
        "DATABASE_PATH",
        database_path,
    )
    monkeypatch.setenv(
        history.HISTORY_MAX_ROWS_ENV,
        "1000",
    )
    monkeypatch.setenv(
        history.HISTORY_RETENTION_DAYS_ENV,
        "90",
    )

    return database_path


def _summary(score: int = 100):
    return SerializableNamespace(
        security_score=score,
        risk_level="LOW",
        findings_count=0,
        critical_count=0,
        high_count=0,
        medium_count=0,
        low_count=0,
        info_count=0,
    )


def _risk_profile():
    return SerializableNamespace(
        build_gate_status="PASSED",
    )


def _save(run_id: str):
    return history.save_scan_history(
        run_id=run_id,
        kind="scan",
        target_path="samples/secure-repo",
        summary=_summary(),
        risk_profile=_risk_profile(),
        policy_evaluation=None,
        reports=[],
    )


def test_default_history_retention_settings_are_bounded(
    monkeypatch,
):
    monkeypatch.delenv(
        history.HISTORY_MAX_ROWS_ENV,
        raising=False,
    )
    monkeypatch.delenv(
        history.HISTORY_RETENTION_DAYS_ENV,
        raising=False,
    )

    settings = history.get_history_retention_settings()

    assert settings.max_rows == history.DEFAULT_HISTORY_MAX_ROWS
    assert (
        settings.retention_days
        == history.DEFAULT_HISTORY_RETENTION_DAYS
    )
    assert 1 <= settings.max_rows <= 100_000
    assert 1 <= settings.retention_days <= 3_650


def test_invalid_history_retention_configuration_fails_closed(
    isolated_history,
    monkeypatch,
):
    monkeypatch.setenv(
        history.HISTORY_MAX_ROWS_ENV,
        "0",
    )

    with pytest.raises(HTTPException) as error:
        _save("invalid-config")

    assert error.value.status_code == 503
    assert "History retention configuration is invalid" in str(
        error.value.detail
    )
    assert not isolated_history.exists()


def test_history_count_retention_keeps_only_newest_rows(
    isolated_history,
    monkeypatch,
):
    monkeypatch.setenv(
        history.HISTORY_MAX_ROWS_ENV,
        "3",
    )
    monkeypatch.setenv(
        history.HISTORY_RETENTION_DAYS_ENV,
        "3650",
    )

    for index in range(5):
        _save(f"run-{index}")

    recent = history.get_recent_scan_history(limit=100)

    assert [row["run_id"] for row in recent] == [
        "run-4",
        "run-3",
        "run-2",
    ]

    with sqlite3.connect(isolated_history) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM scan_history"
        ).fetchone()[0]

    assert count == 3


def test_history_age_retention_prunes_expired_rows_after_write(
    isolated_history,
    monkeypatch,
):
    monkeypatch.setenv(
        history.HISTORY_MAX_ROWS_ENV,
        "100",
    )
    monkeypatch.setenv(
        history.HISTORY_RETENTION_DAYS_ENV,
        "30",
    )

    _save("old-run")

    with sqlite3.connect(isolated_history) as connection:
        connection.execute(
            """
            UPDATE scan_history
            SET created_at = ?
            WHERE run_id = ?
            """,
            (
                "2000-01-01T00:00:00+00:00",
                "old-run",
            ),
        )
        connection.commit()

    _save("current-run")

    recent = history.get_recent_scan_history(limit=100)
    run_ids = [row["run_id"] for row in recent]

    assert "current-run" in run_ids
    assert "old-run" not in run_ids


def test_manual_retention_reports_deleted_counts(
    isolated_history,
    monkeypatch,
):
    monkeypatch.setenv(
        history.HISTORY_MAX_ROWS_ENV,
        "2",
    )
    monkeypatch.setenv(
        history.HISTORY_RETENTION_DAYS_ENV,
        "3650",
    )

    for index in range(4):
        _save(f"run-{index}")

    result = history.apply_history_retention(
        now=datetime.now(timezone.utc),
    )

    assert result["max_rows"] == 2
    assert result["retention_days"] == 3650
    assert result["age_deleted"] >= 0
    assert result["count_deleted"] >= 0

    rows = history.get_recent_scan_history(limit=100)

    assert len(rows) == 2


def test_history_indexes_are_created(
    isolated_history,
):
    history.ensure_database()

    with sqlite3.connect(isolated_history) as connection:
        names = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                """
            ).fetchall()
        }

    assert "idx_scan_history_created_at" in names
    assert "idx_scan_history_run_id" in names


def test_existing_history_read_order_and_limits_are_preserved(
    isolated_history,
    monkeypatch,
):
    monkeypatch.setenv(
        history.HISTORY_MAX_ROWS_ENV,
        "100",
    )
    monkeypatch.setenv(
        history.HISTORY_RETENTION_DAYS_ENV,
        "3650",
    )

    for index in range(4):
        _save(f"run-{index}")

    recent = history.get_recent_scan_history(limit=2)
    trend = history.get_risk_trend(limit=2)

    assert [row["run_id"] for row in recent] == [
        "run-3",
        "run-2",
    ]
    assert [row["run_id"] for row in trend] == [
        "run-2",
        "run-3",
    ]
