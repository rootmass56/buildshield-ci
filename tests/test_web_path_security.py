from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import supplysentinel.web.app as web_app
from supplysentinel.web.path_security import (
    WORKSPACE_ROOT_ENV,
    resolve_workspace_directory,
    resolve_workspace_file,
)


client = TestClient(web_app.app)


def test_workspace_allows_relative_directory_inside_root(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    repository = workspace / "repo"
    repository.mkdir(parents=True)

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    resolved = resolve_workspace_directory("repo")

    assert resolved == repository.resolve()


def test_workspace_allows_absolute_directory_inside_root(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    repository = workspace / "repo"
    repository.mkdir(parents=True)

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    resolved = resolve_workspace_directory(str(repository.resolve()))

    assert resolved == repository.resolve()


def test_workspace_rejects_parent_traversal(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    with pytest.raises(HTTPException) as error:
        resolve_workspace_directory("../outside")

    assert error.value.status_code == 403


def test_workspace_rejects_absolute_external_path(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    with pytest.raises(HTTPException) as error:
        resolve_workspace_directory(str(outside.resolve()))

    assert error.value.status_code == 403


def test_workspace_rejects_sibling_prefix_path(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    sibling = tmp_path / "workspace-evil"
    workspace.mkdir()
    sibling.mkdir()

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    with pytest.raises(HTTPException) as error:
        resolve_workspace_directory(str(sibling.resolve()))

    assert error.value.status_code == 403


def test_workspace_rejects_symlink_escape(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()

    link = workspace / "linked-outside"

    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Directory symlinks are unavailable: {error}")

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    with pytest.raises(HTTPException) as error:
        resolve_workspace_directory("linked-outside")

    assert error.value.status_code == 403


def test_workspace_requires_repository_directory(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    regular_file = workspace / "not-a-repository.txt"
    regular_file.write_text("data", encoding="utf-8")

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    with pytest.raises(HTTPException) as error:
        resolve_workspace_directory("not-a-repository.txt")

    assert error.value.status_code == 400


def test_workspace_requires_policy_file(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    policy_file = workspace / "policy.yml"
    policy_file.write_text("minimum_score: 80\n", encoding="utf-8")

    policy_directory = workspace / "policy-dir"
    policy_directory.mkdir()

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    assert resolve_workspace_file("policy.yml") == policy_file.resolve()

    with pytest.raises(HTTPException) as error:
        resolve_workspace_file("policy-dir")

    assert error.value.status_code == 400


def test_scan_api_rejects_target_outside_workspace(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    response = client.post(
        "/api/scan",
        json={
            "target_path": str(outside.resolve()),
            "policy_path": None,
            "report_formats": [],
        },
    )

    assert response.status_code == 403
    assert "outside the configured workspace" in response.json()["detail"]


def test_scan_api_rejects_policy_outside_workspace(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    repository = workspace / "repo"
    repository.mkdir(parents=True)

    outside_policy = tmp_path / "outside-policy.yml"
    outside_policy.write_text("minimum_score: 80\n", encoding="utf-8")

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    response = client.post(
        "/api/scan",
        json={
            "target_path": "repo",
            "policy_path": str(outside_policy.resolve()),
            "report_formats": [],
        },
    )

    assert response.status_code == 403
    assert "outside the configured workspace" in response.json()["detail"]


def test_api_uses_canonical_workspace_path_for_relative_target(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    repository = workspace / "repo"
    repository.mkdir(parents=True)

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    response = client.post(
        "/api/scan",
        json={
            "target_path": "repo",
            "policy_path": None,
            "report_formats": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"]["security_score"] == 100


def test_compare_api_uses_workspace_paths(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    baseline = workspace / "baseline"
    target = workspace / "target"
    baseline.mkdir(parents=True)
    target.mkdir(parents=True)

    monkeypatch.setenv(WORKSPACE_ROOT_ENV, str(workspace))

    response = client.post(
        "/api/compare",
        json={
            "baseline_path": "baseline",
            "target_path": "target",
            "baseline_label": "Baseline",
            "target_label": "Target",
            "report_formats": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["comparison"]["baseline"]["summary"]["security_score"] == 100
    assert response.json()["comparison"]["target"]["summary"]["security_score"] == 100


def test_safe_report_file_accepts_valid_report(monkeypatch, tmp_path):
    reports_root = tmp_path / "reports"
    report_file = reports_root / "scan-run" / "scan.json"
    report_file.parent.mkdir(parents=True)
    report_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(web_app, "REPORTS_ROOT", reports_root)

    resolved = web_app.safe_report_file("scan-run", "scan.json")

    assert resolved == report_file.resolve()


def test_safe_report_file_rejects_path_components(monkeypatch, tmp_path):
    reports_root = tmp_path / "reports"
    reports_root.mkdir()

    monkeypatch.setattr(web_app, "REPORTS_ROOT", reports_root)

    with pytest.raises(HTTPException) as run_error:
        web_app.safe_report_file("../reports-evil", "secret.txt")

    assert run_error.value.status_code == 400

    with pytest.raises(HTTPException) as filename_error:
        web_app.safe_report_file("scan-run", "../secret.txt")

    assert filename_error.value.status_code == 400


def test_safe_report_file_rejects_symlink_escape(monkeypatch, tmp_path):
    reports_root = tmp_path / "reports"
    run_dir = reports_root / "scan-run"
    run_dir.mkdir(parents=True)

    outside = tmp_path / "outside-secret.txt"
    outside.write_text("secret", encoding="utf-8")

    link = run_dir / "scan.json"

    try:
        link.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"File symlinks are unavailable: {error}")

    monkeypatch.setattr(web_app, "REPORTS_ROOT", reports_root)

    with pytest.raises(HTTPException) as error:
        web_app.safe_report_file("scan-run", "scan.json")

    assert error.value.status_code == 400
