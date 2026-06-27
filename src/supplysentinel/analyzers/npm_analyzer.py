import json
from pathlib import Path

from supplysentinel.analyzers.utils import (
    find_line_number,
    get_line_snippet,
    read_text_file,
)
from supplysentinel.core.constants import FindingCategory, Severity
from supplysentinel.core.models import Evidence, Finding, RepositoryFile


DANGEROUS_LIFECYCLE_SCRIPTS = {
    "preinstall",
    "install",
    "postinstall",
    "prepare",
}

RISKY_SCRIPT_PATTERNS = [
    "curl ",
    "wget ",
    "| bash",
    "| sh",
    "powershell",
    "Invoke-WebRequest",
    "bash -c",
    "sh -c",
]

PRIVATE_PACKAGE_INDICATORS = [
    "internal",
    "private",
    "company",
    "corp",
    "enterprise",
    "proprietary",
]


def is_loose_npm_version(version: str) -> bool:
    version = version.strip().lower()

    return (
        version in {"*", "latest"}
        or version.startswith("^")
        or version.startswith("~")
        or version.startswith(">=")
        or version.startswith("<=")
        or version.startswith(">")
        or version.startswith("<")
        or "x" in version
    )


def looks_private_package(package_name: str) -> bool:
    normalized = package_name.lower()

    if any(indicator in normalized for indicator in PRIVATE_PACKAGE_INDICATORS):
        return True

    if package_name.startswith("@"):
        scope = package_name.split("/")[0].lower()

        common_public_scopes = {
            "@types",
            "@babel",
            "@angular",
            "@nestjs",
            "@testing-library",
            "@eslint",
            "@vitejs",
            "@react-native",
        }

        return scope not in common_public_scopes

    return False


def npmrc_has_scoped_registry(repo_path: Path, package_name: str) -> bool:
    if not package_name.startswith("@"):
        return False

    scope = package_name.split("/")[0]
    npmrc_path = repo_path / ".npmrc"

    if not npmrc_path.exists():
        return False

    content = read_text_file(npmrc_path)
    return f"{scope}:registry=" in content


def analyze_npm(repo_path: Path, discovered_files: list[RepositoryFile]) -> list[Finding]:
    findings: list[Finding] = []

    npm_manifests = [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "npm_manifest"
    ]

    for repo_file in npm_manifests:
        package_json_path = repo_file.absolute_path
        content = read_text_file(package_json_path)

        try:
            package_data = json.loads(content)
        except json.JSONDecodeError:
            findings.append(
                Finding(
                    rule_id="DG-NPM-000",
                    title="Invalid package.json file",
                    severity=Severity.LOW,
                    category=FindingCategory.DEPENDENCY,
                    confidence="HIGH",
                    description="The package.json file could not be parsed as valid JSON.",
                    impact="Invalid dependency metadata can prevent accurate security analysis.",
                    evidence=Evidence(
                        file_path=repo_file.relative_path,
                        line_number=None,
                        snippet="Invalid JSON",
                    ),
                    remediation="Fix package.json syntax errors and rerun the scan.",
                    reference="https://docs.npmjs.com/cli/configuring-npm/package-json",
                )
            )
            continue

        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})
        all_dependencies = {**dependencies, **dev_dependencies}

        lockfile_exists = (
            (package_json_path.parent / "package-lock.json").exists()
            or (package_json_path.parent / "npm-shrinkwrap.json").exists()
        )

        if all_dependencies and not lockfile_exists:
            findings.append(
                Finding(
                    rule_id="DG-NPM-001",
                    title="Missing npm lockfile",
                    severity=Severity.MEDIUM,
                    category=FindingCategory.DEPENDENCY,
                    confidence="HIGH",
                    description="The project declares npm dependencies but does not include package-lock.json or npm-shrinkwrap.json.",
                    impact="Without a lockfile, builds may install unexpected dependency versions, reducing reproducibility and increasing supply-chain risk.",
                    evidence=Evidence(
                        file_path=repo_file.relative_path,
                        line_number=1,
                        snippet="package.json present, lockfile missing",
                    ),
                    remediation="Commit package-lock.json or npm-shrinkwrap.json to enforce deterministic dependency resolution.",
                    reference="https://docs.npmjs.com/cli/configuring-npm/package-lock-json",
                )
            )

        for package_name, version in all_dependencies.items():
            version = str(version)

            if is_loose_npm_version(version):
                line_number = find_line_number(content, package_name)
                findings.append(
                    Finding(
                        rule_id="DG-NPM-002",
                        title="Loose npm dependency version",
                        severity=Severity.MEDIUM,
                        category=FindingCategory.DEPENDENCY,
                        confidence="HIGH",
                        description=f"The npm dependency '{package_name}' uses a loose version constraint: {version}.",
                        impact="Loose dependency versions can allow unexpected package updates during builds.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=get_line_snippet(content, line_number),
                        ),
                        remediation=f"Pin '{package_name}' to an exact reviewed version and update it through controlled dependency management.",
                        reference="https://docs.npmjs.com/about-semantic-versioning",
                    )
                )

            if looks_private_package(package_name) and not npmrc_has_scoped_registry(repo_path, package_name):
                line_number = find_line_number(content, package_name)
                findings.append(
                    Finding(
                        rule_id="DG-NPM-004",
                        title="Potential npm dependency confusion risk",
                        severity=Severity.CRITICAL,
                        category=FindingCategory.REGISTRY,
                        confidence="MEDIUM",
                        description=f"The package '{package_name}' appears to be private/internal, but no scoped private registry configuration was found.",
                        impact="An attacker may publish a similarly named package to a public registry and cause the build system to install it.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=get_line_snippet(content, line_number),
                        ),
                        remediation=f"Configure a scoped private registry for the package scope in .npmrc and ensure public registry fallback is controlled.",
                        reference="https://owasp.org/www-project-top-10-ci-cd-security-risks/CICD-SEC-03-Dependency-Chain-Abuse/",
                    )
                )

        scripts = package_data.get("scripts", {})

        for script_name, command in scripts.items():
            command = str(command)

            if script_name in DANGEROUS_LIFECYCLE_SCRIPTS and any(pattern in command for pattern in RISKY_SCRIPT_PATTERNS):
                line_number = find_line_number(content, script_name)
                findings.append(
                    Finding(
                        rule_id="DG-NPM-003",
                        title="Risky npm lifecycle script",
                        severity=Severity.HIGH,
                        category=FindingCategory.BUILD_SCRIPT,
                        confidence="HIGH",
                        description=f"The npm lifecycle script '{script_name}' executes a risky command.",
                        impact="Lifecycle scripts can execute automatically during dependency installation and may compromise build environments.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=get_line_snippet(content, line_number),
                        ),
                        remediation="Avoid remote shell execution in lifecycle scripts. Replace it with reviewed, version-controlled build logic.",
                        reference="https://docs.npmjs.com/cli/using-npm/scripts",
                    )
                )

    return findings