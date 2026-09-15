from __future__ import annotations

import os
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from supplysentinel.web.audit import audit_event
from supplysentinel.web.history import clear_report_metadata_for_runs
from supplysentinel.web.path_security import resolve_report_file


REPORT_LIST_LIMIT_ENV = "BUILDSHIELD_REPORT_LIST_LIMIT"
REPORT_MAX_DOWNLOAD_BYTES_ENV = "BUILDSHIELD_REPORT_MAX_DOWNLOAD_BYTES"
REPORT_MAX_RUNS_ENV = "BUILDSHIELD_REPORT_MAX_RUNS"
REPORT_RETENTION_DAYS_ENV = "BUILDSHIELD_REPORT_RETENTION_DAYS"

DEFAULT_REPORT_LIST_LIMIT = 500
DEFAULT_REPORT_MAX_DOWNLOAD_BYTES = 20_971_520
DEFAULT_REPORT_MAX_RUNS = 250
DEFAULT_REPORT_RETENTION_DAYS = 30

ALLOWED_REPORT_SUFFIXES = {
    ".json",
    ".md",
    ".html",
    ".sarif",
}


@dataclass(frozen=True)
class ReportSecuritySettings:
    list_limit: int
    max_download_bytes: int


@dataclass(frozen=True)
class SafeReportDownload:
    path: Path
    size_bytes: int


@dataclass(frozen=True)
class ReportRetentionSettings:
    max_runs: int
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
            detail=f"Report security configuration is invalid: {env_name}.",
        ) from error

    if value < 1 or value > maximum:
        raise HTTPException(
            status_code=503,
            detail=f"Report security configuration is invalid: {env_name}.",
        )

    return value


def get_report_security_settings() -> ReportSecuritySettings:
    return ReportSecuritySettings(
        list_limit=_parse_positive_int(
            REPORT_LIST_LIMIT_ENV,
            DEFAULT_REPORT_LIST_LIMIT,
            maximum=5_000,
        ),
        max_download_bytes=_parse_positive_int(
            REPORT_MAX_DOWNLOAD_BYTES_ENV,
            DEFAULT_REPORT_MAX_DOWNLOAD_BYTES,
            maximum=104_857_600,
        ),
    )



def get_report_retention_settings() -> ReportRetentionSettings:
    return ReportRetentionSettings(
        max_runs=_parse_positive_int(
            REPORT_MAX_RUNS_ENV,
            DEFAULT_REPORT_MAX_RUNS,
            maximum=5_000,
        ),
        retention_days=_parse_positive_int(
            REPORT_RETENTION_DAYS_ENV,
            DEFAULT_REPORT_RETENTION_DAYS,
            maximum=3_650,
        ),
    )


def _safe_remove_tree_no_follow(path: Path) -> None:
    with os.scandir(path) as entries:
        for entry in entries:
            entry_path = Path(entry.path)

            if entry.is_dir(follow_symlinks=False):
                _safe_remove_tree_no_follow(entry_path)
            else:
                entry_path.unlink()

    path.rmdir()


def _safe_remove_run_dir(
    reports_root: Path,
    run_dir: Path,
) -> None:
    try:
        root = reports_root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=503,
            detail="Report retention cleanup failed.",
        ) from error

    if run_dir.parent != reports_root:
        raise HTTPException(
            status_code=503,
            detail="Report retention cleanup refused an unsafe path.",
        )

    if run_dir.is_symlink():
        raise HTTPException(
            status_code=503,
            detail="Report retention cleanup refused an unsafe path.",
        )

    try:
        resolved_run = run_dir.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=503,
            detail="Report retention cleanup failed.",
        ) from error

    if (
        resolved_run == root
        or not resolved_run.is_relative_to(root)
        or not resolved_run.is_dir()
    ):
        raise HTTPException(
            status_code=503,
            detail="Report retention cleanup refused an unsafe path.",
        )

    try:
        _safe_remove_tree_no_follow(resolved_run)
    except OSError as error:
        raise HTTPException(
            status_code=503,
            detail="Report retention cleanup failed.",
        ) from error


def enforce_report_retention(
    reports_root: Path,
    *,
    actor: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    settings = get_report_retention_settings()
    reports_root.mkdir(parents=True, exist_ok=True)

    current_time = now or datetime.now(timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    current_timestamp = current_time.astimezone(timezone.utc).timestamp()
    retention_seconds = settings.retention_days * 86_400

    candidates: list[tuple[Path, float]] = []

    for child in reports_root.iterdir():
        if child.is_symlink() or not child.is_dir():
            continue

        try:
            modified = child.stat().st_mtime
        except OSError:
            continue

        candidates.append((child, modified))

    deleted_run_ids: list[str] = []
    age_deleted = 0
    count_deleted = 0
    retained: list[tuple[Path, float]] = []

    for run_dir, modified in candidates:
        if current_timestamp - modified > retention_seconds:
            _safe_remove_run_dir(reports_root, run_dir)
            deleted_run_ids.append(run_dir.name)
            age_deleted += 1
        else:
            retained.append((run_dir, modified))

    retained.sort(
        key=lambda item: (item[1], item[0].name),
        reverse=True,
    )

    for run_dir, _modified in retained[settings.max_runs:]:
        _safe_remove_run_dir(reports_root, run_dir)
        deleted_run_ids.append(run_dir.name)
        count_deleted += 1

    history_rows_updated = clear_report_metadata_for_runs(
        deleted_run_ids
    )

    if deleted_run_ids:
        audit_event(
            "report.retention",
            outcome="success",
            actor=actor,
            operation="report_cleanup",
            details={
                "age_deleted": age_deleted,
                "count_deleted": count_deleted,
                "history_rows_updated": history_rows_updated,
            },
        )

    return {
        "age_deleted": age_deleted,
        "count_deleted": count_deleted,
        "history_rows_updated": history_rows_updated,
        "deleted_run_ids": deleted_run_ids,
        "max_runs": settings.max_runs,
        "retention_days": settings.retention_days,
    }

def _has_allowed_report_suffix(filename: str) -> bool:
    if (
        not filename
        or filename.startswith(".")
        or "\x00" in filename
    ):
        return False

    return Path(filename).suffix.lower() in ALLOWED_REPORT_SUFFIXES


def _candidate_is_symlink(
    reports_root: Path,
    run_id: str,
    filename: str | None = None,
) -> bool:
    run_candidate = reports_root / run_id

    if run_candidate.is_symlink():
        return True

    if filename is None:
        return False

    return (run_candidate / filename).is_symlink()


def resolve_safe_report_download(
    *,
    reports_root: Path,
    run_id: str,
    filename: str,
) -> SafeReportDownload:
    if not _has_allowed_report_suffix(filename):
        raise HTTPException(
            status_code=404,
            detail="Report file not found.",
        )

    if _candidate_is_symlink(
        reports_root,
        run_id,
        filename,
    ):
        raise HTTPException(
            status_code=404,
            detail="Report file not found.",
        )

    report_file = resolve_report_file(
        reports_root=reports_root,
        run_id=run_id,
        filename=filename,
    )

    settings = get_report_security_settings()

    try:
        size_bytes = report_file.stat().st_size
    except OSError as error:
        raise HTTPException(
            status_code=404,
            detail="Report file not found.",
        ) from error

    if size_bytes > settings.max_download_bytes:
        raise HTTPException(
            status_code=413,
            detail="Report file exceeds the configured download size limit.",
        )

    return SafeReportDownload(
        path=report_file,
        size_bytes=size_bytes,
    )


def list_safe_reports(
    reports_root: Path,
) -> list[dict[str, Any]]:
    settings = get_report_security_settings()

    reports_root.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, Any]] = []

    for run_dir in sorted(
        reports_root.iterdir(),
        key=lambda path: path.name,
        reverse=True,
    ):
        if len(reports) >= settings.list_limit:
            break

        if run_dir.is_symlink() or not run_dir.is_dir():
            continue

        for report_file in sorted(
            run_dir.iterdir(),
            key=lambda path: path.name,
        ):
            if len(reports) >= settings.list_limit:
                break

            if (
                report_file.is_symlink()
                or not report_file.is_file()
                or not _has_allowed_report_suffix(report_file.name)
            ):
                continue

            try:
                safe_file = resolve_report_file(
                    reports_root=reports_root,
                    run_id=run_dir.name,
                    filename=report_file.name,
                )
                size_bytes = safe_file.stat().st_size
            except (HTTPException, OSError):
                continue

            if size_bytes > settings.max_download_bytes:
                continue

            reports.append(
                {
                    "run_id": run_dir.name,
                    "filename": safe_file.name,
                    "download_url": (
                        f"/api/reports/{run_dir.name}/{safe_file.name}"
                    ),
                    "size_bytes": size_bytes,
                }
            )

    return reports
