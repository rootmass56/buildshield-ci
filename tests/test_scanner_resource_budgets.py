from __future__ import annotations

import pytest

from supplysentinel.core.resource_budget import (
    RepositoryResourceConfigurationError,
    RepositoryResourceLimitError,
    SCAN_MAX_ENTRIES_ENV,
    SCAN_MAX_FILES_ENV,
    SCAN_MAX_FILE_BYTES_ENV,
    SCAN_MAX_TOTAL_BYTES_ENV,
    get_repository_resource_settings,
)
from supplysentinel.core.scanner import scan_repository
from supplysentinel.web.resource_controls import reset_resource_control_state


RESOURCE_ENV_NAMES = (
    SCAN_MAX_ENTRIES_ENV,
    SCAN_MAX_FILES_ENV,
    SCAN_MAX_FILE_BYTES_ENV,
    SCAN_MAX_TOTAL_BYTES_ENV,
)


@pytest.fixture(autouse=True)
def _reset_rate_state():
    reset_resource_control_state()
    yield
    reset_resource_control_state()


def _set_generous_limits(monkeypatch) -> None:
    monkeypatch.setenv(SCAN_MAX_ENTRIES_ENV, "1000")
    monkeypatch.setenv(SCAN_MAX_FILES_ENV, "100")
    monkeypatch.setenv(SCAN_MAX_FILE_BYTES_ENV, "1048576")
    monkeypatch.setenv(SCAN_MAX_TOTAL_BYTES_ENV, "4194304")


def test_default_repository_resource_settings_are_bounded(monkeypatch):
    for env_name in RESOURCE_ENV_NAMES:
        monkeypatch.delenv(env_name, raising=False)

    settings = get_repository_resource_settings()

    assert 1 <= settings.max_entries <= 1_000_000
    assert 1 <= settings.max_files <= 50_000
    assert 1 <= settings.max_file_bytes <= 67_108_864
    assert 1 <= settings.max_total_bytes <= 536_870_912


def test_invalid_repository_resource_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv(SCAN_MAX_FILES_ENV, "0")

    with pytest.raises(RepositoryResourceConfigurationError):
        get_repository_resource_settings()


def test_scan_rejects_too_many_security_relevant_files(
    tmp_path,
    monkeypatch,
):
    _set_generous_limits(monkeypatch)
    monkeypatch.setenv(SCAN_MAX_FILES_ENV, "2")

    for index in range(3):
        (tmp_path / f"requirements-{index}.txt").write_text(
            "requests==2.32.0\n",
            encoding="utf-8",
        )

    with pytest.raises(RepositoryResourceLimitError, match="file count"):
        scan_repository(str(tmp_path))


def test_scan_rejects_oversized_security_relevant_file(
    tmp_path,
    monkeypatch,
):
    _set_generous_limits(monkeypatch)
    monkeypatch.setenv(SCAN_MAX_FILE_BYTES_ENV, "32")

    (tmp_path / "requirements.txt").write_text(
        "requests==2.32.0\n" * 10,
        encoding="utf-8",
    )

    with pytest.raises(RepositoryResourceLimitError, match="file exceeds"):
        scan_repository(str(tmp_path))


def test_scan_rejects_aggregate_security_input_budget(
    tmp_path,
    monkeypatch,
):
    _set_generous_limits(monkeypatch)
    monkeypatch.setenv(SCAN_MAX_TOTAL_BYTES_ENV, "100")

    (tmp_path / "requirements.txt").write_text(
        "a==1.0.0\n" * 8,
        encoding="utf-8",
    )
    (tmp_path / "requirements-dev.txt").write_text(
        "b==1.0.0\n" * 8,
        encoding="utf-8",
    )

    with pytest.raises(RepositoryResourceLimitError, match="aggregate"):
        scan_repository(str(tmp_path))


def test_scan_rejects_excessive_repository_entries(
    tmp_path,
    monkeypatch,
):
    _set_generous_limits(monkeypatch)
    monkeypatch.setenv(SCAN_MAX_ENTRIES_ENV, "3")

    for index in range(4):
        (tmp_path / f"irrelevant-{index}.txt").write_text(
            "data",
            encoding="utf-8",
        )

    with pytest.raises(RepositoryResourceLimitError, match="entry count"):
        scan_repository(str(tmp_path))


def test_ignored_dependency_tree_does_not_consume_recursive_budget(
    tmp_path,
    monkeypatch,
):
    _set_generous_limits(monkeypatch)
    monkeypatch.setenv(SCAN_MAX_ENTRIES_ENV, "3")

    node_modules = tmp_path / "node_modules" / "deep"
    node_modules.mkdir(parents=True)

    for index in range(50):
        (node_modules / f"package-{index}.json").write_text(
            '{"dependencies": {}}',
            encoding="utf-8",
        )

    (tmp_path / "package.json").write_text(
        '{"dependencies": {}}',
        encoding="utf-8",
    )

    result = scan_repository(str(tmp_path))

    assert result.summary.files_discovered == 1


def test_web_scan_returns_413_for_repository_budget_exhaustion(
    authenticated_client,
    monkeypatch,
):
    client, csrf_token = authenticated_client

    _set_generous_limits(monkeypatch)
    monkeypatch.setenv(SCAN_MAX_FILES_ENV, "1")

    response = client.post(
        "/api/scan",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "target_path": "samples/vulnerable-repo",
            "policy_path": None,
            "report_formats": [],
        },
    )

    assert response.status_code == 413
    assert "resource budget exceeded" in response.json()["detail"]
