from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import supplysentinel.web.history as history
import supplysentinel.web.report_security as report_security


class SerializableNamespace(SimpleNamespace):
    def model_dump(self, mode: str = "json"):
        assert mode == "json"
        return vars(self).copy()


@pytest.fixture
def isolated_report_retention(
    tmp_path,
    monkeypatch,
):
    reports_root = tmp_path / "reports" / "dashboard"
    reports_root.mkdir(parents=True)

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
    monkeypatch.setattr(
        report_security,
        "clear_report_metadata_for_runs",
        history.clear_report_metadata_for_runs,
    )
    monkeypatch.setenv(
        report_security.REPORT_MAX_RUNS_ENV,
        "250",
    )
    monkeypatch.setenv(
        report_security.REPORT_RETENTION_DAYS_ENV,
        "30",
    )
    monkeypatch.setenv(
        history.HISTORY_MAX_ROWS_ENV,
        "1000",
    )
    monkeypatch.setenv(
        history.HISTORY_RETENTION_DAYS_ENV,
        "90",
    )

    return reports_root, database_path


def _make_run(
    reports_root: Path,
    run_id: str,
    *,
    modified: datetime,
) -> Path:
    run_dir = reports_root / run_id
    nested = run_dir / "nested"
    nested.mkdir(parents=True)

    (run_dir / "report.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (nested / "detail.md").write_text(
        "# detail",
        encoding="utf-8",
    )

    timestamp = modified.timestamp()
    os.utime(nested / "detail.md", (timestamp, timestamp))
    os.utime(nested, (timestamp, timestamp))
    os.utime(run_dir / "report.json", (timestamp, timestamp))
    os.utime(run_dir, (timestamp, timestamp))

    return run_dir


def _save_history(run_id: str) -> None:
    summary = SerializableNamespace(
        security_score=100,
        risk_level="LOW",
        findings_count=0,
        critical_count=0,
        high_count=0,
        medium_count=0,
        low_count=0,
        info_count=0,
    )
    risk_profile = SerializableNamespace(
        build_gate_status="PASSED",
    )

    history.save_scan_history(
        run_id=run_id,
        kind="scan",
        target_path="samples/secure-repo",
        summary=summary,
        risk_profile=risk_profile,
        policy_evaluation=None,
        reports=[
            {
                "run_id": run_id,
                "filename": "report.json",
                "download_url": (
                    f"/api/reports/{run_id}/report.json"
                ),
            }
        ],
    )


def test_default_report_retention_settings_are_bounded(
    monkeypatch,
):
    monkeypatch.delenv(
        report_security.REPORT_MAX_RUNS_ENV,
        raising=False,
    )
    monkeypatch.delenv(
        report_security.REPORT_RETENTION_DAYS_ENV,
        raising=False,
    )

    settings = report_security.get_report_retention_settings()

    assert (
        settings.max_runs
        == report_security.DEFAULT_REPORT_MAX_RUNS
    )
    assert (
        settings.retention_days
        == report_security.DEFAULT_REPORT_RETENTION_DAYS
    )
    assert 1 <= settings.max_runs <= 5_000
    assert 1 <= settings.retention_days <= 3_650


def test_invalid_report_retention_configuration_fails_closed(
    isolated_report_retention,
    monkeypatch,
):
    reports_root, _database = isolated_report_retention

    monkeypatch.setenv(
        report_security.REPORT_MAX_RUNS_ENV,
        "0",
    )

    with pytest.raises(HTTPException) as error:
        report_security.enforce_report_retention(
            reports_root
        )

    assert error.value.status_code == 503
    assert "Report security configuration is invalid" in str(
        error.value.detail
    )


def test_report_count_retention_keeps_newest_runs(
    isolated_report_retention,
    monkeypatch,
):
    reports_root, _database = isolated_report_retention
    now = datetime.now(timezone.utc)

    monkeypatch.setenv(
        report_security.REPORT_MAX_RUNS_ENV,
        "2",
    )
    monkeypatch.setenv(
        report_security.REPORT_RETENTION_DAYS_ENV,
        "3650",
    )

    for index in range(4):
        _make_run(
            reports_root,
            f"run-{index}",
            modified=now - timedelta(minutes=10 - index),
        )

    events: list[dict[str, object]] = []

    monkeypatch.setattr(
        report_security,
        "audit_event",
        lambda event, **kwargs: events.append(
            {"event": event, **kwargs}
        ),
    )

    result = report_security.enforce_report_retention(
        reports_root,
        actor="admin",
        now=now,
    )

    remaining = {
        path.name
        for path in reports_root.iterdir()
        if path.is_dir()
    }

    assert remaining == {"run-2", "run-3"}
    assert result["count_deleted"] == 2
    assert result["age_deleted"] == 0
    assert any(
        event["event"] == "report.retention"
        and event["outcome"] == "success"
        for event in events
    )


def test_report_age_retention_prunes_expired_run(
    isolated_report_retention,
):
    reports_root, _database = isolated_report_retention
    now = datetime.now(timezone.utc)

    old_run = _make_run(
        reports_root,
        "old-run",
        modified=now - timedelta(days=45),
    )
    current_run = _make_run(
        reports_root,
        "current-run",
        modified=now - timedelta(days=1),
    )

    result = report_security.enforce_report_retention(
        reports_root,
        now=now,
    )

    assert not old_run.exists()
    assert current_run.exists()
    assert result["age_deleted"] == 1


def test_safe_cleanup_refuses_path_outside_report_root(
    isolated_report_retention,
    tmp_path,
):
    reports_root, _database = isolated_report_retention

    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "do-not-delete.txt"
    marker.write_text("safe", encoding="utf-8")

    with pytest.raises(HTTPException) as error:
        report_security._safe_remove_run_dir(
            reports_root,
            outside,
        )

    assert error.value.status_code == 503
    assert marker.exists()


def test_report_cleanup_reconciles_history_metadata(
    isolated_report_retention,
    monkeypatch,
):
    reports_root, database_path = isolated_report_retention
    now = datetime.now(timezone.utc)

    monkeypatch.setenv(
        report_security.REPORT_MAX_RUNS_ENV,
        "1",
    )
    monkeypatch.setenv(
        report_security.REPORT_RETENTION_DAYS_ENV,
        "3650",
    )

    old_run = _make_run(
        reports_root,
        "old-run",
        modified=now - timedelta(hours=2),
    )
    _make_run(
        reports_root,
        "new-run",
        modified=now - timedelta(hours=1),
    )

    _save_history("old-run")

    result = report_security.enforce_report_retention(
        reports_root,
        now=now,
    )

    assert not old_run.exists()
    assert result["history_rows_updated"] == 1

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT report_count, metadata_json
            FROM scan_history
            WHERE run_id = ?
            """,
            ("old-run",),
        ).fetchone()

    assert row is not None
    assert row[0] == 0

    metadata = json.loads(row[1])

    assert metadata["reports"] == []


def test_recursive_cleanup_removes_nested_files_without_escape(
    isolated_report_retention,
):
    reports_root, _database = isolated_report_retention
    now = datetime.now(timezone.utc)

    run_dir = _make_run(
        reports_root,
        "remove-me",
        modified=now,
    )
    sibling = reports_root.parent / "keep-me.txt"
    sibling.write_text("outside run", encoding="utf-8")

    report_security._safe_remove_run_dir(
        reports_root,
        run_dir,
    )

    assert not run_dir.exists()
    assert sibling.exists()
