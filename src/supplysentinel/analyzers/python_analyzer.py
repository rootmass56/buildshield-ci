import re

from supplysentinel.analyzers.utils import read_text_file
from supplysentinel.core.constants import FindingCategory, Severity
from supplysentinel.core.models import Evidence, Finding, RepositoryFile


PRIVATE_PACKAGE_INDICATORS = [
    "internal",
    "private",
    "company",
    "corp",
    "enterprise",
    "proprietary",
]

VERSION_OPERATOR_PATTERN = re.compile(r"(==|===|>=|<=|~=|>|<)")


def extract_package_name(requirement_line: str) -> str:
    clean_line = requirement_line.split("#")[0].strip()
    clean_line = clean_line.split(";")[0].strip()

    match = re.split(r"==|===|>=|<=|~=|>|<", clean_line, maxsplit=1)
    return match[0].strip()


def looks_private_package(package_name: str) -> bool:
    normalized = package_name.lower()
    return any(indicator in normalized for indicator in PRIVATE_PACKAGE_INDICATORS)


def analyze_python_requirements(discovered_files: list[RepositoryFile]) -> list[Finding]:
    findings: list[Finding] = []

    requirement_files = [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "python_requirements"
    ]

    for repo_file in requirement_files:
        content = read_text_file(repo_file.absolute_path)
        lines = content.splitlines()

        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("-"):
                continue

            package_name = extract_package_name(line)

            if not package_name:
                continue

            if not VERSION_OPERATOR_PATTERN.search(line):
                findings.append(
                    Finding(
                        rule_id="DG-PY-001",
                        title="Unpinned Python dependency",
                        severity=Severity.MEDIUM,
                        category=FindingCategory.DEPENDENCY,
                        confidence="HIGH",
                        description=f"The Python dependency '{package_name}' does not specify a version.",
                        impact="Unpinned dependencies may resolve to unexpected versions during installation.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation=f"Pin '{package_name}' to an exact reviewed version using ==.",
                        reference="https://pip.pypa.io/en/stable/reference/requirements-file-format/",
                    )
                )

            elif "==" not in line and "===" not in line:
                findings.append(
                    Finding(
                        rule_id="DG-PY-002",
                        title="Loose Python dependency version",
                        severity=Severity.MEDIUM,
                        category=FindingCategory.DEPENDENCY,
                        confidence="HIGH",
                        description=f"The Python dependency '{package_name}' uses a loose version constraint.",
                        impact="Loose version constraints can introduce unexpected dependency updates.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation=f"Use an exact pinned version for '{package_name}' where reproducible builds are required.",
                        reference="https://pip.pypa.io/en/stable/reference/requirements-file-format/",
                    )
                )

            if looks_private_package(package_name):
                findings.append(
                    Finding(
                        rule_id="DG-PY-003",
                        title="Potential Python dependency confusion risk",
                        severity=Severity.HIGH,
                        category=FindingCategory.REGISTRY,
                        confidence="MEDIUM",
                        description=f"The Python dependency '{package_name}' appears to be internal or private.",
                        impact="Private package names may be vulnerable to dependency confusion if package indexes are not isolated.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation="Use a private package index, configure index priority carefully, and avoid unsafe public registry fallback.",
                        reference="https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-03-Dependency-Chain-Abuse/",
                    )
                )

    return findings