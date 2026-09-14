from __future__ import annotations

from pathlib import Path
import tomllib


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_gitignore_covers_runtime_build_and_secret_artifacts() -> None:
    content = (project_root() / ".gitignore").read_text(
        encoding="utf-8-sig"
    )

    required_entries = {
        "__pycache__/",
        ".pytest_cache/",
        ".venv/",
        "build/",
        "dist/",
        "*.egg-info/",
        "reports/",
        "data/",
        ".env",
        "!.env.example",
    }

    for entry in required_entries:
        assert entry in content


def test_dockerignore_excludes_development_and_runtime_artifacts() -> None:
    content = (project_root() / ".dockerignore").read_text(
        encoding="utf-8-sig"
    )

    required_entries = {
        ".git",
        ".github",
        ".venv",
        "__pycache__",
        "tests",
        "reports",
        "data",
        "*.egg-info",
        ".env",
    }

    for entry in required_entries:
        assert entry in content


def test_repository_has_cross_platform_line_ending_policy() -> None:
    content = (project_root() / ".gitattributes").read_text(
        encoding="utf-8-sig"
    )

    required_rules = {
        "* text=auto",
        ".gitattributes text eol=lf",
        ".gitignore text eol=lf",
        ".dockerignore text eol=lf",
        ".env.example text eol=lf",
        "Dockerfile text eol=lf",
        "*.py text eol=lf",
        "*.yml text eol=lf",
        "*.yaml text eol=lf",
        "*.toml text eol=lf",
        "*.md text eol=lf",
    }

    for rule in required_rules:
        assert rule in content


def test_pytest_does_not_globally_suppress_all_warnings() -> None:
    content = (project_root() / "pyproject.toml").read_text(
        encoding="utf-8-sig"
    )

    assert "ignore::Warning" not in content


def test_project_metadata_contains_repository_links() -> None:
    pyproject_path = project_root() / "pyproject.toml"

    with pyproject_path.open("rb") as file_handle:
        pyproject = tomllib.load(file_handle)

    urls = pyproject["project"]["urls"]

    assert urls["Homepage"] == "https://github.com/rootmass56/buildshield-ci"
    assert urls["Repository"] == "https://github.com/rootmass56/buildshield-ci"
    assert urls["Issues"] == "https://github.com/rootmass56/buildshield-ci/issues"


def test_dev_dependencies_support_current_starlette_testclient() -> None:
    pyproject_path = project_root() / "pyproject.toml"

    with pyproject_path.open("rb") as file_handle:
        pyproject = tomllib.load(file_handle)

    dev_dependencies = pyproject["project"]["optional-dependencies"]["dev"]

    assert any(
        dependency.startswith("httpx2")
        for dependency in dev_dependencies
    )
