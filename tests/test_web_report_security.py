from __future__ import annotations

import pytest

import supplysentinel.web.app as web_app
from supplysentinel.web.report_security import (
    DEFAULT_REPORT_LIST_LIMIT,
    DEFAULT_REPORT_MAX_DOWNLOAD_BYTES,
    REPORT_LIST_LIMIT_ENV,
    REPORT_MAX_DOWNLOAD_BYTES_ENV,
    get_report_security_settings,
)


@pytest.fixture
def isolated_reports_root(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        web_app,
        "REPORTS_ROOT",
        tmp_path,
    )
    return tmp_path


def _write_report(
    root,
    run_id: str,
    filename: str,
    content: str = "{}",
):
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def test_default_report_security_settings_are_bounded(
    monkeypatch,
):
    monkeypatch.delenv(
        REPORT_LIST_LIMIT_ENV,
        raising=False,
    )
    monkeypatch.delenv(
        REPORT_MAX_DOWNLOAD_BYTES_ENV,
        raising=False,
    )

    settings = get_report_security_settings()

    assert settings.list_limit == DEFAULT_REPORT_LIST_LIMIT
    assert (
        settings.max_download_bytes
        == DEFAULT_REPORT_MAX_DOWNLOAD_BYTES
    )
    assert 1 <= settings.list_limit <= 5_000
    assert 1 <= settings.max_download_bytes <= 104_857_600


def test_invalid_report_security_configuration_fails_closed(
    authenticated_client,
    monkeypatch,
):
    client, _ = authenticated_client

    monkeypatch.setenv(
        REPORT_LIST_LIMIT_ENV,
        "0",
    )

    response = client.get("/api/reports")

    assert response.status_code == 503
    assert "Report security configuration is invalid" in (
        response.json()["detail"]
    )


def test_report_listing_filters_unsupported_hidden_and_caps_results(
    authenticated_client,
    isolated_reports_root,
    monkeypatch,
):
    client, _ = authenticated_client

    monkeypatch.setenv(
        REPORT_LIST_LIMIT_ENV,
        "2",
    )
    monkeypatch.setenv(
        REPORT_MAX_DOWNLOAD_BYTES_ENV,
        "1024",
    )

    _write_report(
        isolated_reports_root,
        "scan-003",
        "report.json",
    )
    _write_report(
        isolated_reports_root,
        "scan-002",
        "report.html",
    )
    _write_report(
        isolated_reports_root,
        "scan-001",
        "report.md",
    )
    _write_report(
        isolated_reports_root,
        "scan-004",
        "notes.txt",
    )
    _write_report(
        isolated_reports_root,
        "scan-005",
        ".hidden.json",
    )

    response = client.get("/api/reports")

    assert response.status_code == 200

    reports = response.json()["reports"]

    assert len(reports) == 2
    assert all(
        report["filename"].endswith(
            (".json", ".md", ".html", ".sarif")
        )
        for report in reports
    )
    assert all(
        not report["filename"].startswith(".")
        for report in reports
    )
    assert all(
        report["size_bytes"] >= 0
        for report in reports
    )


def test_report_download_is_forced_attachment_octet_stream(
    authenticated_client,
    isolated_reports_root,
    monkeypatch,
):
    client, _ = authenticated_client

    monkeypatch.setenv(
        REPORT_MAX_DOWNLOAD_BYTES_ENV,
        "1024",
    )

    _write_report(
        isolated_reports_root,
        "scan-safe",
        "security-report.html",
        "<html><script>alert('x')</script></html>",
    )

    response = client.get(
        "/api/reports/scan-safe/security-report.html"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/octet-stream"
    )
    assert response.headers["content-disposition"].startswith(
        "attachment;"
    )
    assert (
        response.headers["x-content-type-options"]
        == "nosniff"
    )
    assert response.headers["cache-control"] == "no-store"


def test_report_download_rejects_unsupported_extension(
    authenticated_client,
    isolated_reports_root,
):
    client, _ = authenticated_client

    _write_report(
        isolated_reports_root,
        "scan-safe",
        "private.txt",
        "not a supported report",
    )

    response = client.get(
        "/api/reports/scan-safe/private.txt"
    )

    assert response.status_code == 404


def test_report_download_enforces_maximum_size(
    authenticated_client,
    isolated_reports_root,
    monkeypatch,
):
    client, _ = authenticated_client

    monkeypatch.setenv(
        REPORT_MAX_DOWNLOAD_BYTES_ENV,
        "16",
    )

    _write_report(
        isolated_reports_root,
        "scan-large",
        "large.json",
        "x" * 64,
    )

    response = client.get(
        "/api/reports/scan-large/large.json"
    )

    assert response.status_code == 413
    assert (
        response.json()["detail"]
        == "Report file exceeds the configured download size limit."
    )


def test_oversized_report_is_not_advertised_in_listing(
    authenticated_client,
    isolated_reports_root,
    monkeypatch,
):
    client, _ = authenticated_client

    monkeypatch.setenv(
        REPORT_MAX_DOWNLOAD_BYTES_ENV,
        "16",
    )

    _write_report(
        isolated_reports_root,
        "scan-large",
        "large.json",
        "x" * 64,
    )
    _write_report(
        isolated_reports_root,
        "scan-small",
        "small.json",
        "{}",
    )

    response = client.get("/api/reports")

    assert response.status_code == 200

    filenames = {
        item["filename"]
        for item in response.json()["reports"]
    }

    assert "small.json" in filenames
    assert "large.json" not in filenames


def test_report_endpoints_remain_authenticated(
    isolated_reports_root,
):
    from fastapi.testclient import TestClient

    from supplysentinel.web.app import app

    client = TestClient(app)

    _write_report(
        isolated_reports_root,
        "scan-safe",
        "security-report.json",
    )

    listing = client.get("/api/reports")
    download = client.get(
        "/api/reports/scan-safe/security-report.json"
    )

    assert listing.status_code == 401
    assert download.status_code == 401
    client.close()
