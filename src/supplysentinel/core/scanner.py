from pathlib import Path

from supplysentinel.analyzers.github_actions_analyzer import analyze_github_actions
from supplysentinel.analyzers.npm_analyzer import analyze_npm
from supplysentinel.analyzers.python_analyzer import analyze_python_requirements
from supplysentinel.core.constants import (
    SECURITY_RELEVANT_FILENAMES,
    Severity,
)
from supplysentinel.core.exceptions import InvalidTargetError
from supplysentinel.core.models import (
    Finding,
    RepositoryFile,
    RiskProfile,
    ScanResult,
    ScanSummary,
)
from supplysentinel.core.scoring import calculate_risk_profile


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


def is_ignored_path(path: Path) -> bool:
    """
    Check whether a file path belongs to a directory that should be ignored.
    """
    return any(part in IGNORED_DIRECTORIES for part in path.parts)


def detect_file_type(path: Path) -> str:
    """
    Classify security-relevant files based on filename and path.
    """
    name = path.name

    if name == "package.json":
        return "npm_manifest"

    if name in {"package-lock.json", "npm-shrinkwrap.json"}:
        return "npm_lockfile"

    if name == "requirements.txt":
        return "python_requirements"

    if name == "pyproject.toml":
        return "python_pyproject"

    if name in {"poetry.lock", "Pipfile.lock"}:
        return "python_lockfile"

    if name == ".npmrc":
        return "npm_registry_config"

    if name in {".pypirc", "pip.conf"}:
        return "python_registry_config"

    if name in {"go.mod", "go.sum"}:
        return "go_dependency_file"

    if name in {"pom.xml", "build.gradle", "gradle.lockfile"}:
        return "java_dependency_file"

    if name in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
        return "container_config"

    if ".github" in path.parts and "workflows" in path.parts and path.suffix in {".yml", ".yaml"}:
        return "github_actions_workflow"

    if name == ".gitlab-ci.yml":
        return "gitlab_ci_workflow"

    return "unknown"


def is_security_relevant_file(path: Path) -> bool:
    """
    Identify whether a file is relevant for supply-chain or CI/CD security analysis.
    """
    if path.name in SECURITY_RELEVANT_FILENAMES:
        return True

    if ".github" in path.parts and "workflows" in path.parts:
        return path.suffix in {".yml", ".yaml"}

    return False


def discover_repository_files(target_path: Path) -> list[RepositoryFile]:
    """
    Discover all security-relevant files inside the target repository.
    """
    discovered_files: list[RepositoryFile] = []

    for path in target_path.rglob("*"):
        if not path.is_file():
            continue

        if is_ignored_path(path):
            continue

        if not is_security_relevant_file(path):
            continue

        relative_path = str(path.relative_to(target_path))

        discovered_files.append(
            RepositoryFile(
                absolute_path=path,
                relative_path=relative_path,
                file_name=path.name,
                file_type=detect_file_type(path),
                size_bytes=path.stat().st_size,
            )
        )

    return sorted(discovered_files, key=lambda item: item.relative_path)


def run_analyzers(
    repo_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    """
    Run all security analyzers against discovered files.
    """
    findings: list[Finding] = []

    findings.extend(analyze_npm(repo_path, discovered_files))
    findings.extend(analyze_python_requirements(discovered_files))
    findings.extend(analyze_github_actions(discovered_files))

    return findings


def calculate_summary(
    target_path: Path,
    discovered_files: list[RepositoryFile],
    findings: list[Finding],
    risk_profile: RiskProfile,
) -> ScanSummary:
    """
    Build high-level scan summary from findings and risk profile.
    """
    critical_count = sum(
        1 for finding in findings if finding.severity == Severity.CRITICAL
    )
    high_count = sum(
        1 for finding in findings if finding.severity == Severity.HIGH
    )
    medium_count = sum(
        1 for finding in findings if finding.severity == Severity.MEDIUM
    )
    low_count = sum(
        1 for finding in findings if finding.severity == Severity.LOW
    )
    info_count = sum(
        1 for finding in findings if finding.severity == Severity.INFO
    )

    return ScanSummary(
        target_path=str(target_path),
        files_discovered=len(discovered_files),
        files_scanned=len(discovered_files),
        findings_count=len(findings),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        info_count=info_count,
        security_score=risk_profile.overall_security_score,
        risk_level=risk_profile.overall_risk_level,
    )


def scan_repository(target: str) -> ScanResult:
    """
    Main scanner entry point.

    This function:
    1. Validates the target repository path.
    2. Discovers security-relevant files.
    3. Runs all analyzers.
    4. Builds advanced risk profile.
    5. Returns complete scan result.
    """
    target_path = Path(target).resolve()

    if not target_path.exists():
        raise InvalidTargetError(f"Target path does not exist: {target_path}")

    if not target_path.is_dir():
        raise InvalidTargetError(f"Target path is not a directory: {target_path}")

    discovered_files = discover_repository_files(target_path)
    findings = run_analyzers(target_path, discovered_files)
    risk_profile = calculate_risk_profile(findings)

    summary = calculate_summary(
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