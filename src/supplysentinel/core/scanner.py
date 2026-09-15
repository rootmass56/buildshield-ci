from __future__ import annotations

import os
from pathlib import Path

from supplysentinel.analyzers import (
    dockerfile_analyzer,
    github_actions_analyzer,
    npm_analyzer,
    python_analyzer,
)
from supplysentinel.core import scoring
from supplysentinel.core.constants import Severity
from supplysentinel.core.exceptions import SupplySentinelError
from supplysentinel.core.resource_budget import validate_repository_scan_budget
from supplysentinel.core.models import (
    Finding,
    RepositoryFile,
    ScanResult,
    ScanSummary,
)


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
}


SECURITY_RELEVANT_FILENAMES = {
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-prod.txt",
    ".npmrc",
    "pip.conf",
    "pip.ini",
    ".pypirc",
    "Dockerfile",
    "dockerfile",
}


def should_ignore_path(path: Path) -> bool:
    return any(
        part in IGNORED_DIRECTORIES
        for part in path.parts
    )


def is_github_actions_workflow(path: Path) -> bool:
    normalized_parts = [
        part.lower()
        for part in path.parts
    ]

    return (
        ".github" in normalized_parts
        and "workflows" in normalized_parts
        and path.suffix.lower() in {".yml", ".yaml"}
    )


def is_dockerfile(path: Path) -> bool:
    file_name = path.name.lower()

    return (
        file_name == "dockerfile"
        or file_name.endswith(".dockerfile")
    )


def is_security_relevant_file(path: Path) -> bool:
    if should_ignore_path(path):
        return False

    if is_github_actions_workflow(path):
        return True

    if is_dockerfile(path):
        return True

    if path.name in SECURITY_RELEVANT_FILENAMES:
        return True

    if (
        path.name.startswith("requirements")
        and path.suffix.lower() == ".txt"
    ):
        return True

    return False


def determine_file_type(path: Path) -> str:
    file_name = path.name.lower()

    if file_name == "package.json":
        return "package_json"

    if file_name in {
        "package-lock.json",
        "npm-shrinkwrap.json",
        "yarn.lock",
        "pnpm-lock.yaml",
    }:
        return "npm_lockfile"

    if (
        file_name.startswith("requirements")
        and path.suffix.lower() == ".txt"
    ):
        return "python_requirements"

    if file_name == ".npmrc":
        return "npm_config"

    if file_name in {
        "pip.conf",
        "pip.ini",
        ".pypirc",
    }:
        return "python_package_config"

    if is_github_actions_workflow(path):
        return "github_actions_workflow"

    if is_dockerfile(path):
        return "dockerfile"

    return "unknown"


def build_repository_file(
    path: Path,
    target_path: Path,
) -> RepositoryFile:
    relative_path = str(
        path.relative_to(target_path)
    ).replace("\\", "/")

    return RepositoryFile(
        absolute_path=path,
        relative_path=relative_path,
        file_name=path.name,
        file_type=determine_file_type(path),
        size_bytes=path.stat().st_size,
    )


def discover_security_relevant_files(
    target_path: Path,
) -> list[RepositoryFile]:
    discovered_files: list[RepositoryFile] = []

    for directory, dirnames, filenames in os.walk(
        target_path,
        topdown=True,
        followlinks=False,
    ):
        directory_path = Path(directory)

        dirnames[:] = [
            name
            for name in dirnames
            if (
                name not in IGNORED_DIRECTORIES
                and not (directory_path / name).is_symlink()
            )
        ]

        for filename in filenames:
            path = directory_path / filename

            if path.is_symlink() or not path.is_file():
                continue

            if not is_security_relevant_file(path):
                continue

            discovered_files.append(
                build_repository_file(
                    path=path,
                    target_path=target_path,
                )
            )

    return sorted(
        discovered_files,
        key=lambda repo_file: repo_file.relative_path,
    )


def deduplicate_findings(
    findings: list[Finding],
) -> list[Finding]:
    seen: set[tuple] = set()
    unique_findings: list[Finding] = []

    for finding in findings:
        key = (
            finding.rule_id,
            finding.evidence.file_path,
            finding.evidence.line_number,
            finding.evidence.snippet,
            finding.title,
        )

        if key in seen:
            continue

        seen.add(key)
        unique_findings.append(finding)

    return unique_findings


def run_all_analyzers(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    """Run every analyzer through an explicit, stable interface."""
    findings: list[Finding] = []

    findings.extend(
        npm_analyzer.analyze_npm(
            target_path=target_path,
            discovered_files=discovered_files,
        )
    )

    findings.extend(
        python_analyzer.analyze_python_security(
            target_path=target_path,
            discovered_files=discovered_files,
        )
    )

    findings.extend(
        github_actions_analyzer.analyze_github_actions(
            discovered_files=discovered_files,
        )
    )

    findings.extend(
        dockerfile_analyzer.analyze_dockerfile_security(
            target_path=target_path,
            discovered_files=discovered_files,
        )
    )

    return deduplicate_findings(findings)


def build_risk_profile_from_existing_scoring_engine(
    findings: list[Finding],
):
    candidate_function_names = [
        "build_risk_profile",
        "calculate_risk_profile",
        "build_advanced_risk_profile",
        "calculate_advanced_risk_profile",
        "generate_risk_profile",
        "calculate_security_score",
    ]

    for function_name in candidate_function_names:
        scoring_function = getattr(
            scoring,
            function_name,
            None,
        )

        if scoring_function is None:
            continue

        return scoring_function(findings)

    available_functions = [
        name
        for name in dir(scoring)
        if (
            callable(getattr(scoring, name))
            and not name.startswith("_")
        )
    ]

    raise SupplySentinelError(
        "No compatible risk scoring function found in scoring.py. "
        f"Available functions: {available_functions}"
    )


def count_findings_by_severity(
    findings: list[Finding],
    severity: Severity,
) -> int:
    return sum(
        1
        for finding in findings
        if finding.severity == severity
    )


def build_scan_summary(
    target_path: Path,
    discovered_files: list[RepositoryFile],
    findings: list[Finding],
    risk_profile,
) -> ScanSummary:
    return ScanSummary(
        target_path=str(target_path),
        files_discovered=len(discovered_files),
        files_scanned=len(discovered_files),
        findings_count=len(findings),
        critical_count=count_findings_by_severity(
            findings,
            Severity.CRITICAL,
        ),
        high_count=count_findings_by_severity(
            findings,
            Severity.HIGH,
        ),
        medium_count=count_findings_by_severity(
            findings,
            Severity.MEDIUM,
        ),
        low_count=count_findings_by_severity(
            findings,
            Severity.LOW,
        ),
        info_count=count_findings_by_severity(
            findings,
            Severity.INFO,
        ),
        security_score=risk_profile.overall_security_score,
        risk_level=risk_profile.overall_risk_level,
    )


def scan_repository(target: str) -> ScanResult:
    target_path = Path(target).resolve()

    if not target_path.exists():
        raise SupplySentinelError(
            f"Target path does not exist: {target}"
        )

    if not target_path.is_dir():
        raise SupplySentinelError(
            f"Target path is not a directory: {target}"
        )

    validate_repository_scan_budget(
        target_path,
        is_relevant_file=is_security_relevant_file,
        ignored_directories=IGNORED_DIRECTORIES,
    )

    discovered_files = discover_security_relevant_files(
        target_path
    )

    findings = run_all_analyzers(
        target_path=target_path,
        discovered_files=discovered_files,
    )

    risk_profile = (
        build_risk_profile_from_existing_scoring_engine(
            findings
        )
    )

    summary = build_scan_summary(
        target_path=target_path,
        discovered_files=discovered_files,
        findings=findings,
        risk_profile=risk_profile,
    )

    return ScanResult(
        summary=summary,
        risk_profile=risk_profile,
        discovered_files=discovered_files,
        findings=findings,
    )
