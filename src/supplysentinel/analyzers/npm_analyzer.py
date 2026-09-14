from __future__ import annotations

import json
from pathlib import Path

from supplysentinel.analyzers.utils import (
    find_line_number,
    get_line_snippet,
    read_text_file,
)
from supplysentinel.core.constants import FindingCategory, Severity
from supplysentinel.core.models import Evidence, Finding, RepositoryFile


NPM_DEPENDENCY_GROUPS = [
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
]

NPM_INTERNAL_KEYWORDS = [
    "internal",
    "private",
    "company",
    "corp",
    "enterprise",
    "auth",
    "payment",
]

RISKY_LIFECYCLE_SCRIPT_NAMES = {
    "preinstall",
    "install",
    "postinstall",
    "prepare",
}


def create_npm_finding(
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
        reference="https://owasp.org/www-project-top-10-ci-cd-security-risks/",
    )


def package_json_files(
    discovered_files: list[RepositoryFile],
) -> list[RepositoryFile]:
    return [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "package_json"
    ]


def has_npm_lockfile(
    package_json_file: RepositoryFile,
    discovered_files: list[RepositoryFile],
) -> bool:
    package_dir = str(
        Path(package_json_file.relative_path).parent
    ).replace("\\", "/")

    for repo_file in discovered_files:
        if repo_file.file_type != "npm_lockfile":
            continue

        lockfile_dir = str(
            Path(repo_file.relative_path).parent
        ).replace("\\", "/")

        if lockfile_dir == package_dir:
            return True

    return False


def has_private_npm_registry(
    package_json_file: RepositoryFile,
    discovered_files: list[RepositoryFile],
    package_name: str,
) -> bool:
    package_dir = str(
        Path(package_json_file.relative_path).parent
    ).replace("\\", "/")

    scope: str | None = None

    if package_name.startswith("@") and "/" in package_name:
        scope = package_name.split("/", maxsplit=1)[0].lower()

    npmrc_files = [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "npm_config"
    ]

    for npmrc_file in npmrc_files:
        npmrc_dir = str(
            Path(npmrc_file.relative_path).parent
        ).replace("\\", "/")

        if npmrc_dir not in {package_dir, "."}:
            continue

        content = read_text_file(
            Path(npmrc_file.absolute_path)
        ).lower()

        if scope and f"{scope}:registry" in content:
            return True

        if (
            "registry=" in content
            and "registry.npmjs.org" not in content
        ):
            return True

        if (
            "always-auth=true" in content
            and "registry" in content
        ):
            return True

    return False


def is_loose_npm_version(version: str | None) -> bool:
    if not version:
        return True

    normalized = str(version).strip().lower()

    loose_tokens = [
        "^",
        "~",
        ">",
        "<",
        "*",
        "x",
        "latest",
        "workspace:",
        "file:",
        "git+",
        "http:",
        "https:",
    ]

    return any(token in normalized for token in loose_tokens)


def is_internal_npm_candidate(package_name: str) -> bool:
    normalized = package_name.lower()

    if normalized.startswith(
        (
            "@company/",
            "@internal/",
            "@corp/",
            "@private/",
            "@enterprise/",
        )
    ):
        return True

    return any(
        keyword in normalized
        for keyword in NPM_INTERNAL_KEYWORDS
    )


def analyze_npm(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    """Analyze npm manifests and registry configuration."""
    _ = target_path

    findings: list[Finding] = []

    for package_json_file in package_json_files(discovered_files):
        path = Path(package_json_file.absolute_path)
        content = read_text_file(path)

        try:
            package_data = json.loads(content)
        except json.JSONDecodeError:
            # Preserve the v0.12.6 controlled benchmark behavior.
            continue

        lockfile_present = has_npm_lockfile(
            package_json_file=package_json_file,
            discovered_files=discovered_files,
        )

        if not lockfile_present:
            findings.append(
                create_npm_finding(
                    rule_id="DG-NPM-001",
                    title="Missing npm lockfile",
                    severity=Severity.HIGH,
                    category=FindingCategory.DEPENDENCY,
                    description=(
                        "The npm project does not include a lockfile."
                    ),
                    impact=(
                        "Missing lockfiles reduce dependency reproducibility "
                        "and can allow unexpected dependency resolution changes."
                    ),
                    remediation=(
                        "Commit package-lock.json, npm-shrinkwrap.json, "
                        "yarn.lock, or pnpm-lock.yaml."
                    ),
                    file_path=package_json_file.relative_path,
                    line_number=None,
                    snippet="No npm lockfile found",
                )
            )

        for group in NPM_DEPENDENCY_GROUPS:
            dependencies = package_data.get(group, {})

            if not isinstance(dependencies, dict):
                continue

            for package_name, version_specifier in dependencies.items():
                line_number = find_line_number(
                    content,
                    f'"{package_name}"',
                )
                snippet = get_line_snippet(
                    content,
                    line_number,
                )

                if is_loose_npm_version(
                    str(version_specifier)
                ):
                    findings.append(
                        create_npm_finding(
                            rule_id="DG-NPM-002",
                            title="Loose npm dependency version",
                            severity=Severity.MEDIUM,
                            category=FindingCategory.DEPENDENCY,
                            description=(
                                "The npm dependency uses a loose or "
                                "mutable version specifier."
                            ),
                            impact=(
                                "Loose dependency versions can resolve "
                                "to different package versions over time."
                            ),
                            remediation=(
                                "Pin npm dependencies to exact "
                                "reviewed versions."
                            ),
                            file_path=package_json_file.relative_path,
                            line_number=line_number,
                            snippet=snippet,
                        )
                    )

                if is_internal_npm_candidate(package_name):
                    private_registry_configured = (
                        has_private_npm_registry(
                            package_json_file=package_json_file,
                            discovered_files=discovered_files,
                            package_name=package_name,
                        )
                    )

                    if not private_registry_configured:
                        findings.append(
                            create_npm_finding(
                                rule_id="DG-NPM-004",
                                title=(
                                    "Potential npm dependency "
                                    "confusion risk"
                                ),
                                severity=Severity.CRITICAL,
                                category=FindingCategory.REGISTRY,
                                description=(
                                    "An internal-looking npm package "
                                    "is declared without matching "
                                    "private registry configuration."
                                ),
                                impact=(
                                    "Attackers may publish a public "
                                    "package with the same name and "
                                    "cause dependency confusion."
                                ),
                                remediation=(
                                    "Configure scoped private registries "
                                    "in .npmrc and ensure internal packages "
                                    "resolve only from trusted registries."
                                ),
                                file_path=package_json_file.relative_path,
                                line_number=line_number,
                                snippet=snippet,
                            )
                        )

        scripts = package_data.get("scripts", {})

        if isinstance(scripts, dict):
            for script_name, script_value in scripts.items():
                if script_name not in RISKY_LIFECYCLE_SCRIPT_NAMES:
                    continue

                line_number = find_line_number(
                    content,
                    f'"{script_name}"',
                )
                snippet = get_line_snippet(
                    content,
                    line_number,
                )

                findings.append(
                    create_npm_finding(
                        rule_id="DG-NPM-003",
                        title="Risky npm lifecycle script",
                        severity=Severity.HIGH,
                        category=FindingCategory.BUILD_SCRIPT,
                        description=(
                            "The npm project uses a lifecycle script "
                            "that can execute during dependency installation."
                        ),
                        impact=(
                            "Lifecycle scripts can execute arbitrary code "
                            "during package install or CI builds."
                        ),
                        remediation=(
                            "Avoid risky lifecycle scripts or strictly "
                            "review and sandbox their execution."
                        ),
                        file_path=package_json_file.relative_path,
                        line_number=line_number,
                        snippet=(
                            snippet
                            or f"{script_name}: {script_value}"
                        ),
                    )
                )

    return findings
