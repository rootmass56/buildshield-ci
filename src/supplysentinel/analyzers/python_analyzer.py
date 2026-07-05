import re
from pathlib import Path

from supplysentinel.analyzers.utils import read_text_file
from supplysentinel.core.constants import FindingCategory, Severity
from supplysentinel.core.models import Evidence, Finding, RepositoryFile


PYTHON_REQUIREMENT_OPERATORS = [
    "==",
    ">=",
    "<=",
    "~=",
    "!=",
    ">",
    "<",
]


INTERNAL_PACKAGE_KEYWORDS = [
    "internal",
    "private",
    "company",
    "corp",
    "enterprise",
    "auth-sdk",
    "payment-sdk",
    "platform-sdk",
    "internal-payment",
    "internal-auth",
]


def python_requirements_files(discovered_files: list[RepositoryFile]) -> list[RepositoryFile]:
    return [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "python_requirements"
    ]


def python_config_files(discovered_files: list[RepositoryFile]) -> list[RepositoryFile]:
    return [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "python_package_config"
    ]


def create_python_finding(
    rule_id: str,
    title: str,
    severity: Severity,
    category: FindingCategory,
    description: str,
    impact: str,
    remediation: str,
    file_path: str,
    line_number: int | None,
    snippet: str | None,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        title=title,
        severity=severity,
        category=category,
        confidence="HIGH",
        description=description,
        impact=impact,
        evidence=Evidence(
            file_path=file_path,
            line_number=line_number,
            snippet=snippet,
        ),
        remediation=remediation,
        reference="https://packaging.python.org/en/latest/specifications/dependency-specifiers/",
    )


def extract_python_requirement(line: str) -> tuple[str, str | None] | None:
    cleaned = line.strip()

    if not cleaned:
        return None

    if cleaned.startswith("#"):
        return None

    if cleaned.startswith(
        (
            "-r ",
            "--requirement",
            "--index-url",
            "--extra-index-url",
            "-i ",
            "--find-links",
            "-f ",
            "--trusted-host",
        )
    ):
        return None

    if " #" in cleaned:
        cleaned = cleaned.split(" #", maxsplit=1)[0].strip()

    match = re.match(
        r"^([A-Za-z0-9_.-]+)(?:\[.*?\])?\s*(.*)$",
        cleaned,
    )

    if not match:
        return None

    package_name = match.group(1).strip()
    version_specifier = match.group(2).strip() or None

    if not package_name:
        return None

    return package_name, version_specifier


def is_python_version_pinned(version_specifier: str | None) -> bool:
    if not version_specifier:
        return False

    version = version_specifier.strip()

    if not version.startswith("=="):
        return False

    if "*" in version:
        return False

    return bool(
        re.match(
            r"^==\s*[0-9]+(\.[0-9]+)*([a-zA-Z0-9.\-_+]+)?$",
            version,
        )
    )


def is_python_version_loose(version_specifier: str | None) -> bool:
    if not version_specifier:
        return False

    version = version_specifier.strip()

    if is_python_version_pinned(version):
        return False

    return any(operator in version for operator in PYTHON_REQUIREMENT_OPERATORS)


def is_internal_python_candidate(package_name: str) -> bool:
    normalized_name = package_name.lower()

    return any(keyword in normalized_name for keyword in INTERNAL_PACKAGE_KEYWORDS)


def requirement_has_private_registry(content: str) -> bool:
    lower_content = content.lower()

    if "--index-url" in lower_content or "--extra-index-url" in lower_content:
        if "pypi.org/simple" not in lower_content and "files.pythonhosted.org" not in lower_content:
            return True

    return False


def config_file_has_private_registry(config_file: RepositoryFile) -> bool:
    content = read_text_file(Path(config_file.absolute_path)).lower()

    if "index-url" in content and "pypi.org/simple" not in content:
        return True

    if "repository" in content and "pypi.org" not in content:
        return True

    if "extra-index-url" in content and "pypi.org/simple" not in content:
        return True

    return False


def has_python_private_registry(
    requirements_file: RepositoryFile,
    discovered_files: list[RepositoryFile],
    requirements_content: str,
) -> bool:
    if requirement_has_private_registry(requirements_content):
        return True

    requirement_dir = str(Path(requirements_file.relative_path).parent).replace("\\", "/")

    for config_file in python_config_files(discovered_files):
        config_dir = str(Path(config_file.relative_path).parent).replace("\\", "/")

        if config_dir not in {requirement_dir, "."}:
            continue

        if config_file_has_private_registry(config_file):
            return True

    return False


def analyze_python_security(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    findings: list[Finding] = []

    for requirements_file in python_requirements_files(discovered_files):
        path = Path(requirements_file.absolute_path)
        content = read_text_file(path)

        private_registry_configured = has_python_private_registry(
            requirements_file=requirements_file,
            discovered_files=discovered_files,
            requirements_content=content,
        )

        for line_number, line in enumerate(content.splitlines(), start=1):
            parsed = extract_python_requirement(line)

            if parsed is None:
                continue

            package_name, version_specifier = parsed
            snippet = line.strip()

            if not version_specifier:
                findings.append(
                    create_python_finding(
                        rule_id="DG-PY-001",
                        title="Unpinned Python dependency",
                        severity=Severity.MEDIUM,
                        category=FindingCategory.DEPENDENCY,
                        description="The Python dependency does not specify an exact version.",
                        impact=(
                            "Unpinned Python dependencies can resolve to different versions "
                            "over time, reducing build reproducibility."
                        ),
                        remediation="Pin Python dependencies using exact versions such as package==1.2.3.",
                        file_path=requirements_file.relative_path,
                        line_number=line_number,
                        snippet=snippet,
                    )
                )

            if is_python_version_loose(version_specifier):
                findings.append(
                    create_python_finding(
                        rule_id="DG-PY-002",
                        title="Loose Python dependency version",
                        severity=Severity.MEDIUM,
                        category=FindingCategory.DEPENDENCY,
                        description="The Python dependency uses a loose version specifier.",
                        impact=(
                            "Loose Python version specifiers can allow unexpected package "
                            "versions to be installed during CI/CD builds."
                        ),
                        remediation="Use exact pinned versions such as package==1.2.3.",
                        file_path=requirements_file.relative_path,
                        line_number=line_number,
                        snippet=snippet,
                    )
                )

            if is_internal_python_candidate(package_name) and not private_registry_configured:
                findings.append(
                    create_python_finding(
                        rule_id="DG-PY-003",
                        title="Potential Python dependency confusion risk",
                        severity=Severity.HIGH,
                        category=FindingCategory.REGISTRY,
                        description=(
                            "An internal-looking Python package is declared without private "
                            "package index configuration."
                        ),
                        impact=(
                            "Attackers may publish a public package with a similar internal "
                            "name and cause dependency confusion."
                        ),
                        remediation=(
                            "Configure a trusted private Python package index using pip.conf, "
                            ".pypirc, --index-url, or --extra-index-url."
                        ),
                        file_path=requirements_file.relative_path,
                        line_number=line_number,
                        snippet=snippet,
                    )
                )

    return findings


def analyze_python_repository(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    return analyze_python_security(target_path, discovered_files)


def analyze_python_files(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    return analyze_python_security(target_path, discovered_files)


def analyze_requirements_files(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    return analyze_python_security(target_path, discovered_files)


def analyze_repository(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    return analyze_python_security(target_path, discovered_files)


def analyze(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    return analyze_python_security(target_path, discovered_files)