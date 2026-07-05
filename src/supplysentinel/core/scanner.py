import json
import re
from pathlib import Path
from types import ModuleType

from supplysentinel.analyzers import (
    dockerfile_analyzer,
    github_actions_analyzer,
    npm_analyzer,
    python_analyzer,
)
from supplysentinel.core import scoring
from supplysentinel.core.constants import FindingCategory, Severity
from supplysentinel.core.exceptions import SupplySentinelError
from supplysentinel.core.models import Evidence, Finding, RepositoryFile, ScanResult, ScanSummary


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


FULL_COMMIT_SHA_PATTERN = re.compile(r"^[a-fA-F0-9]{40}$")


def should_ignore_path(path: Path) -> bool:
    return any(part in IGNORED_DIRECTORIES for part in path.parts)


def is_github_actions_workflow(path: Path) -> bool:
    normalized_parts = [part.lower() for part in path.parts]

    return (
        ".github" in normalized_parts
        and "workflows" in normalized_parts
        and path.suffix.lower() in {".yml", ".yaml"}
    )


def is_dockerfile(path: Path) -> bool:
    file_name = path.name.lower()
    return file_name == "dockerfile" or file_name.endswith(".dockerfile")


def is_security_relevant_file(path: Path) -> bool:
    if should_ignore_path(path):
        return False

    if is_github_actions_workflow(path):
        return True

    if is_dockerfile(path):
        return True

    if path.name in SECURITY_RELEVANT_FILENAMES:
        return True

    if path.name.startswith("requirements") and path.suffix.lower() == ".txt":
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

    if file_name.startswith("requirements") and path.suffix.lower() == ".txt":
        return "python_requirements"

    if file_name == ".npmrc":
        return "npm_config"

    if file_name in {"pip.conf", "pip.ini", ".pypirc"}:
        return "python_package_config"

    if is_github_actions_workflow(path):
        return "github_actions_workflow"

    if is_dockerfile(path):
        return "dockerfile"

    return "unknown"


def build_repository_file(path: Path, target_path: Path) -> RepositoryFile:
    relative_path = str(path.relative_to(target_path)).replace("\\", "/")

    return RepositoryFile(
        absolute_path=path,
        relative_path=relative_path,
        file_name=path.name,
        file_type=determine_file_type(path),
        size_bytes=path.stat().st_size,
    )


def discover_security_relevant_files(target_path: Path) -> list[RepositoryFile]:
    discovered_files: list[RepositoryFile] = []

    for path in target_path.rglob("*"):
        if not path.is_file():
            continue

        if not is_security_relevant_file(path):
            continue

        discovered_files.append(
            build_repository_file(
                path=path,
                target_path=target_path,
            )
        )

    return sorted(discovered_files, key=lambda repo_file: repo_file.relative_path)


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def find_line_number(content: str, search_text: str) -> int | None:
    for index, line in enumerate(content.splitlines(), start=1):
        if search_text in line:
            return index

    return None


def get_line_snippet(content: str, line_number: int | None) -> str | None:
    if line_number is None:
        return None

    lines = content.splitlines()

    if 1 <= line_number <= len(lines):
        return lines[line_number - 1].strip()

    return None


def call_known_analyzer(
    module: ModuleType,
    function_names: list[str],
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    for function_name in function_names:
        analyzer_function = getattr(module, function_name, None)

        if analyzer_function is None or not callable(analyzer_function):
            continue

        call_patterns = [
            lambda: analyzer_function(target_path, discovered_files),
            lambda: analyzer_function(discovered_files),
            lambda: analyzer_function(target_path),
        ]

        for call_pattern in call_patterns:
            try:
                result = call_pattern()
            except TypeError:
                continue

            if not result:
                continue

            return [
                finding
                for finding in result
                if hasattr(finding, "rule_id") and hasattr(finding, "severity")
            ]

    return []


def create_finding(
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
    reference: str | None = None,
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
        reference=reference or "https://owasp.org/www-project-top-10-ci-cd-security-risks/",
    )


def package_json_files(discovered_files: list[RepositoryFile]) -> list[RepositoryFile]:
    return [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "package_json"
    ]


def workflow_files(discovered_files: list[RepositoryFile]) -> list[RepositoryFile]:
    return [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "github_actions_workflow"
    ]


def has_npm_lockfile(package_json_file: RepositoryFile, discovered_files: list[RepositoryFile]) -> bool:
    package_dir = str(Path(package_json_file.relative_path).parent).replace("\\", "/")

    for repo_file in discovered_files:
        if repo_file.file_type != "npm_lockfile":
            continue

        lockfile_dir = str(Path(repo_file.relative_path).parent).replace("\\", "/")

        if lockfile_dir == package_dir:
            return True

    return False


def has_private_npm_registry(
    package_json_file: RepositoryFile,
    discovered_files: list[RepositoryFile],
    package_name: str,
) -> bool:
    package_dir = str(Path(package_json_file.relative_path).parent).replace("\\", "/")

    scope = None

    if package_name.startswith("@") and "/" in package_name:
        scope = package_name.split("/", maxsplit=1)[0].lower()

    npmrc_files = [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "npm_config"
    ]

    for npmrc_file in npmrc_files:
        npmrc_dir = str(Path(npmrc_file.relative_path).parent).replace("\\", "/")

        if npmrc_dir not in {package_dir, "."}:
            continue

        content = read_text_file(Path(npmrc_file.absolute_path)).lower()

        if scope and f"{scope}:registry" in content:
            return True

        if "registry=" in content and "registry.npmjs.org" not in content:
            return True

        if "always-auth=true" in content and "registry" in content:
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

    if normalized.startswith(("@company/", "@internal/", "@corp/", "@private/", "@enterprise/")):
        return True

    return any(keyword in normalized for keyword in NPM_INTERNAL_KEYWORDS)


def fallback_npm_analyzer(
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    findings: list[Finding] = []

    for package_json_file in package_json_files(discovered_files):
        path = Path(package_json_file.absolute_path)
        content = read_text_file(path)

        try:
            package_data = json.loads(content)
        except json.JSONDecodeError:
            continue

        lockfile_present = has_npm_lockfile(package_json_file, discovered_files)

        if not lockfile_present:
            findings.append(
                create_finding(
                    rule_id="DG-NPM-001",
                    title="Missing npm lockfile",
                    severity=Severity.HIGH,
                    category=FindingCategory.DEPENDENCY,
                    description="The npm project does not include a lockfile.",
                    impact="Missing lockfiles reduce dependency reproducibility and can allow unexpected dependency resolution changes.",
                    remediation="Commit package-lock.json, npm-shrinkwrap.json, yarn.lock, or pnpm-lock.yaml.",
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
                line_number = find_line_number(content, f'"{package_name}"')
                snippet = get_line_snippet(content, line_number)

                if is_loose_npm_version(str(version_specifier)):
                    findings.append(
                        create_finding(
                            rule_id="DG-NPM-002",
                            title="Loose npm dependency version",
                            severity=Severity.MEDIUM,
                            category=FindingCategory.DEPENDENCY,
                            description="The npm dependency uses a loose or mutable version specifier.",
                            impact="Loose dependency versions can resolve to different package versions over time.",
                            remediation="Pin npm dependencies to exact reviewed versions.",
                            file_path=package_json_file.relative_path,
                            line_number=line_number,
                            snippet=snippet,
                        )
                    )

                if is_internal_npm_candidate(package_name):
                    private_registry_configured = has_private_npm_registry(
                        package_json_file=package_json_file,
                        discovered_files=discovered_files,
                        package_name=package_name,
                    )

                    if not private_registry_configured:
                        findings.append(
                            create_finding(
                                rule_id="DG-NPM-004",
                                title="Potential npm dependency confusion risk",
                                severity=Severity.CRITICAL,
                                category=FindingCategory.REGISTRY,
                                description="An internal-looking npm package is declared without matching private registry configuration.",
                                impact="Attackers may publish a public package with the same name and cause dependency confusion.",
                                remediation="Configure scoped private registries in .npmrc and ensure internal packages resolve only from trusted registries.",
                                file_path=package_json_file.relative_path,
                                line_number=line_number,
                                snippet=snippet,
                            )
                        )

        scripts = package_data.get("scripts", {})

        if isinstance(scripts, dict):
            risky_script_names = {"preinstall", "install", "postinstall", "prepare"}

            for script_name, script_value in scripts.items():
                if script_name not in risky_script_names:
                    continue

                line_number = find_line_number(content, f'"{script_name}"')
                snippet = get_line_snippet(content, line_number)

                findings.append(
                    create_finding(
                        rule_id="DG-NPM-003",
                        title="Risky npm lifecycle script",
                        severity=Severity.HIGH,
                        category=FindingCategory.BUILD_SCRIPT,
                        description="The npm project uses a lifecycle script that can execute during dependency installation.",
                        impact="Lifecycle scripts can execute arbitrary code during package install or CI builds.",
                        remediation="Avoid risky lifecycle scripts or strictly review and sandbox their execution.",
                        file_path=package_json_file.relative_path,
                        line_number=line_number,
                        snippet=snippet or f"{script_name}: {script_value}",
                    )
                )

    return findings


def action_ref_is_pinned_to_sha(ref: str) -> bool:
    return bool(FULL_COMMIT_SHA_PATTERN.match(ref.strip()))


def fallback_github_actions_analyzer(
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    findings: list[Finding] = []

    for workflow_file in workflow_files(discovered_files):
        path = Path(workflow_file.absolute_path)
        content = read_text_file(path)
        lines = content.splitlines()

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            lower_line = stripped.lower()

            if "pull_request_target" in lower_line:
                findings.append(
                    create_finding(
                        rule_id="DG-GHA-005",
                        title="Use of pull_request_target trigger",
                        severity=Severity.HIGH,
                        category=FindingCategory.CICD,
                        description="The workflow uses pull_request_target, which runs with elevated context compared to pull_request.",
                        impact="Unsafe use of pull_request_target with untrusted code can expose secrets or write permissions.",
                        remediation="Use pull_request where possible. If pull_request_target is required, avoid checking out or executing untrusted code.",
                        file_path=workflow_file.relative_path,
                        line_number=line_number,
                        snippet=stripped,
                    )
                )

            if lower_line.startswith("permissions:") and "write-all" in lower_line:
                findings.append(
                    create_finding(
                        rule_id="DG-GHA-002",
                        title="Over-permissive GitHub Actions token permissions",
                        severity=Severity.HIGH,
                        category=FindingCategory.CICD,
                        description="The workflow grants write-all permission to the GITHUB_TOKEN.",
                        impact="If the workflow is compromised, the attacker may gain broad write access to repository resources.",
                        remediation="Use least-privilege permissions such as contents: read and grant write permissions only when required.",
                        file_path=workflow_file.relative_path,
                        line_number=line_number,
                        snippet=stripped,
                    )
                )

            if "uses:" in lower_line and "@" in stripped:
                match = re.search(r"uses:\s*([^@\s]+)@([^\s#]+)", stripped)

                if match:
                    action_name = match.group(1)
                    action_ref = match.group(2)

                    if not action_ref_is_pinned_to_sha(action_ref):
                        findings.append(
                            create_finding(
                                rule_id="DG-GHA-001",
                                title="GitHub Action not pinned to full commit SHA",
                                severity=Severity.HIGH,
                                category=FindingCategory.CICD,
                                description=f"The workflow uses '{action_name}@{action_ref}' without pinning it to a full commit SHA.",
                                impact="A mutable tag or branch can change over time, allowing unexpected third-party action code to run in CI/CD.",
                                remediation="Pin third-party GitHub Actions to a full-length commit SHA after reviewing the action source.",
                                file_path=workflow_file.relative_path,
                                line_number=line_number,
                                snippet=stripped,
                            )
                        )

            if (
                ("curl " in lower_line or "wget " in lower_line)
                and ("| bash" in lower_line or "| sh" in lower_line)
            ):
                findings.append(
                    create_finding(
                        rule_id="DG-GHA-003",
                        title="Remote script piped directly to shell",
                        severity=Severity.HIGH,
                        category=FindingCategory.BUILD_SCRIPT,
                        description="The workflow downloads a remote script and pipes it directly into a shell.",
                        impact="Remote script execution can compromise the CI/CD runner if the downloaded content is malicious or tampered with.",
                        remediation="Download scripts from trusted sources, verify checksums/signatures, and avoid direct curl/wget pipe-to-shell execution.",
                        file_path=workflow_file.relative_path,
                        line_number=line_number,
                        snippet=stripped,
                    )
                )

            if "echo" in lower_line and "secrets." in lower_line:
                findings.append(
                    create_finding(
                        rule_id="DG-GHA-004",
                        title="Secret value printed in workflow",
                        severity=Severity.CRITICAL,
                        category=FindingCategory.SECRETS,
                        description="The workflow appears to print a secret value to logs.",
                        impact="Secrets printed to CI/CD logs may be exposed to unauthorized users or retained in build history.",
                        remediation="Never echo secrets. Pass secrets only to trusted tools through environment variables or secure secret mechanisms.",
                        file_path=workflow_file.relative_path,
                        line_number=line_number,
                        snippet=stripped,
                    )
                )

    return findings


def deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    seen = set()
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
    findings: list[Finding] = []

    npm_findings = call_known_analyzer(
        module=npm_analyzer,
        function_names=[
            "analyze_npm_security",
            "analyze_npm_repository",
            "analyze_npm_files",
            "analyze_package_json_files",
            "analyze_repository",
            "analyze",
        ],
        target_path=target_path,
        discovered_files=discovered_files,
    )

    if not any(finding.rule_id.startswith("DG-NPM") for finding in npm_findings):
        npm_findings.extend(fallback_npm_analyzer(discovered_files))

    findings.extend(npm_findings)

    findings.extend(
        call_known_analyzer(
            module=python_analyzer,
            function_names=[
                "analyze_python_security",
                "analyze_python_repository",
                "analyze_python_files",
                "analyze_requirements_files",
                "analyze_repository",
                "analyze",
            ],
            target_path=target_path,
            discovered_files=discovered_files,
        )
    )

    github_findings = call_known_analyzer(
        module=github_actions_analyzer,
        function_names=[
            "analyze_github_actions_security",
            "analyze_github_actions_repository",
            "analyze_github_actions_files",
            "analyze_workflows",
            "analyze_workflow_files",
            "analyze_repository",
            "analyze",
        ],
        target_path=target_path,
        discovered_files=discovered_files,
    )

    if not any(finding.rule_id.startswith("DG-GHA") for finding in github_findings):
        github_findings.extend(fallback_github_actions_analyzer(discovered_files))

    findings.extend(github_findings)

    findings.extend(
        dockerfile_analyzer.analyze_dockerfile_security(
            target_path=target_path,
            discovered_files=discovered_files,
        )
    )

    return deduplicate_findings(findings)


def build_risk_profile_from_existing_scoring_engine(findings: list[Finding]):
    candidate_function_names = [
        "build_risk_profile",
        "calculate_risk_profile",
        "build_advanced_risk_profile",
        "calculate_advanced_risk_profile",
        "generate_risk_profile",
        "calculate_security_score",
    ]

    for function_name in candidate_function_names:
        scoring_function = getattr(scoring, function_name, None)

        if scoring_function is None:
            continue

        return scoring_function(findings)

    available_functions = [
        name
        for name in dir(scoring)
        if callable(getattr(scoring, name)) and not name.startswith("_")
    ]

    raise SupplySentinelError(
        "No compatible risk scoring function found in scoring.py. "
        f"Available functions: {available_functions}"
    )


def count_findings_by_severity(findings: list[Finding], severity: Severity) -> int:
    return sum(1 for finding in findings if finding.severity == severity)


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
        critical_count=count_findings_by_severity(findings, Severity.CRITICAL),
        high_count=count_findings_by_severity(findings, Severity.HIGH),
        medium_count=count_findings_by_severity(findings, Severity.MEDIUM),
        low_count=count_findings_by_severity(findings, Severity.LOW),
        info_count=count_findings_by_severity(findings, Severity.INFO),
        security_score=risk_profile.overall_security_score,
        risk_level=risk_profile.overall_risk_level,
    )


def scan_repository(target: str) -> ScanResult:
    target_path = Path(target).resolve()

    if not target_path.exists():
        raise SupplySentinelError(f"Target path does not exist: {target}")

    if not target_path.is_dir():
        raise SupplySentinelError(f"Target path is not a directory: {target}")

    discovered_files = discover_security_relevant_files(target_path)

    findings = run_all_analyzers(
        target_path=target_path,
        discovered_files=discovered_files,
    )

    risk_profile = build_risk_profile_from_existing_scoring_engine(findings)

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
