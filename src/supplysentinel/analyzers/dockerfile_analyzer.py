from pathlib import Path

from supplysentinel.analyzers.utils import (
    find_line_number,
    get_line_snippet,
    read_text_file,
)
from supplysentinel.core.constants import FindingCategory, Severity
from supplysentinel.core.models import Evidence, Finding, RepositoryFile


SENSITIVE_ENV_KEYWORDS = [
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PASSWD",
    "PRIVATE_KEY",
    "API_KEY",
    "ACCESS_KEY",
    "AWS_SECRET",
    "GITHUB_TOKEN",
]


def is_dockerfile(repo_file: RepositoryFile) -> bool:
    file_name = repo_file.file_name.lower()

    return (
        file_name == "dockerfile"
        or file_name.endswith(".dockerfile")
        or repo_file.file_type == "dockerfile"
    )


def dockerfile_files(discovered_files: list[RepositoryFile]) -> list[RepositoryFile]:
    return [repo_file for repo_file in discovered_files if is_dockerfile(repo_file)]


def create_finding(
    rule_id: str,
    title: str,
    severity: Severity,
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
        category=FindingCategory.CONTAINER,
        confidence="HIGH",
        description=description,
        impact=impact,
        evidence=Evidence(
            file_path=file_path,
            line_number=line_number,
            snippet=snippet,
        ),
        remediation=remediation,
        reference=reference,
    )


def detect_latest_base_image(content: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        if not stripped.upper().startswith("FROM "):
            continue

        lower_line = stripped.lower()

        if ":latest" in lower_line or (
            ":" not in stripped.split()[1] and "scratch" not in lower_line
        ):
            findings.append(
                create_finding(
                    rule_id="DG-DOCKER-001",
                    title="Docker base image uses latest or unpinned tag",
                    severity=Severity.HIGH,
                    description="The Dockerfile uses an unpinned or latest base image tag.",
                    impact=(
                        "Unpinned base images can change over time and introduce "
                        "unexpected vulnerabilities or behavior into the build."
                    ),
                    remediation=(
                        "Pin base images to a specific trusted version such as "
                        "python:3.11.9-slim instead of latest."
                    ),
                    file_path=relative_path,
                    line_number=line_number,
                    snippet=stripped,
                )
            )

    return findings


def detect_missing_user_instruction(content: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []
    has_user_instruction = False
    root_user_line: tuple[int, str] | None = None

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped.upper().startswith("USER "):
            has_user_instruction = True

            user_value = stripped.split(maxsplit=1)[1].strip().lower()

            if user_value in {"root", "0"}:
                root_user_line = (line_number, stripped)

    if not has_user_instruction:
        findings.append(
            create_finding(
                rule_id="DG-DOCKER-002",
                title="Dockerfile does not define a non-root USER",
                severity=Severity.HIGH,
                description="The Dockerfile does not specify a non-root USER instruction.",
                impact=(
                    "Containers running as root increase the impact of container escape, "
                    "filesystem abuse, and privilege-related misconfigurations."
                ),
                remediation=(
                    "Create a dedicated low-privilege user and add a USER instruction "
                    "before the final runtime command."
                ),
                file_path=relative_path,
                line_number=None,
                snippet="No USER instruction found",
            )
        )

    if root_user_line:
        line_number, snippet = root_user_line
        findings.append(
            create_finding(
                rule_id="DG-DOCKER-003",
                title="Dockerfile explicitly runs container as root",
                severity=Severity.HIGH,
                description="The Dockerfile explicitly sets USER to root or UID 0.",
                impact=(
                    "Running application containers as root weakens container isolation "
                    "and increases privilege escalation impact."
                ),
                remediation="Run the application as a dedicated non-root user.",
                file_path=relative_path,
                line_number=line_number,
                snippet=snippet,
            )
        )

    return findings


def detect_sensitive_env_or_arg(content: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        upper_line = stripped.upper()

        if not (upper_line.startswith("ENV ") or upper_line.startswith("ARG ")):
            continue

        if any(keyword in upper_line for keyword in SENSITIVE_ENV_KEYWORDS):
            findings.append(
                create_finding(
                    rule_id="DG-DOCKER-004",
                    title="Potential secret stored in Dockerfile ENV or ARG",
                    severity=Severity.CRITICAL,
                    description=(
                        "The Dockerfile appears to define a sensitive value using "
                        "ENV or ARG."
                    ),
                    impact=(
                        "Secrets placed in Dockerfile instructions may be stored in "
                        "image layers, build logs, or image history."
                    ),
                    remediation=(
                        "Do not store secrets in Dockerfiles. Use runtime secret "
                        "management, CI/CD secrets, or orchestrator secret stores."
                    ),
                    file_path=relative_path,
                    line_number=line_number,
                    snippet=stripped,
                )
            )

    return findings


def detect_remote_script_pipe_shell(content: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []

    dangerous_patterns = [
        "curl ",
        "wget ",
    ]

    shell_patterns = [
        "| bash",
        "| sh",
        "bash -c",
        "sh -c",
    ]

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        lower_line = stripped.lower()

        if not stripped.upper().startswith("RUN "):
            continue

        has_download = any(pattern in lower_line for pattern in dangerous_patterns)
        has_shell_pipe = any(pattern in lower_line for pattern in shell_patterns)

        if has_download and has_shell_pipe:
            findings.append(
                create_finding(
                    rule_id="DG-DOCKER-005",
                    title="Remote script piped directly to shell in Dockerfile",
                    severity=Severity.HIGH,
                    description=(
                        "The Dockerfile downloads a remote script and executes it "
                        "directly through a shell."
                    ),
                    impact=(
                        "If the remote script is compromised or tampered with, malicious "
                        "code can execute during image build."
                    ),
                    remediation=(
                        "Download scripts from trusted sources, verify checksums or "
                        "signatures, and avoid direct pipe-to-shell execution."
                    ),
                    file_path=relative_path,
                    line_number=line_number,
                    snippet=stripped,
                )
            )

    return findings


def detect_apt_get_upgrade(content: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        lower_line = stripped.lower()

        if not stripped.upper().startswith("RUN "):
            continue

        if "apt-get upgrade" in lower_line or "apt upgrade" in lower_line:
            findings.append(
                create_finding(
                    rule_id="DG-DOCKER-006",
                    title="Dockerfile runs apt-get upgrade during image build",
                    severity=Severity.MEDIUM,
                    description=(
                        "The Dockerfile performs package upgrades during image build."
                    ),
                    impact=(
                        "Uncontrolled package upgrades can reduce build reproducibility "
                        "and introduce unexpected package versions."
                    ),
                    remediation=(
                        "Use a trusted updated base image and install only required "
                        "packages with explicit package names."
                    ),
                    file_path=relative_path,
                    line_number=line_number,
                    snippet=stripped,
                )
            )

    return findings


def detect_missing_healthcheck(content: str, relative_path: str) -> list[Finding]:
    has_healthcheck = any(
        line.strip().upper().startswith("HEALTHCHECK")
        for line in content.splitlines()
    )

    if has_healthcheck:
        return []

    return [
        create_finding(
            rule_id="DG-DOCKER-007",
            title="Dockerfile does not define HEALTHCHECK",
            severity=Severity.LOW,
            description="The Dockerfile does not define a HEALTHCHECK instruction.",
            impact=(
                "Without a health check, container platforms may have reduced visibility "
                "into application readiness or runtime failure."
            ),
            remediation=(
                "Add an appropriate HEALTHCHECK instruction for the application or "
                "service running in the container."
            ),
            file_path=relative_path,
            line_number=None,
            snippet="No HEALTHCHECK instruction found",
        )
    ]


def detect_remote_add_instruction(content: str, relative_path: str) -> list[Finding]:
    findings: list[Finding] = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        lower_line = stripped.lower()

        if not lower_line.startswith("add "):
            continue

        if "http://" in lower_line or "https://" in lower_line:
            findings.append(
                create_finding(
                    rule_id="DG-DOCKER-008",
                    title="Dockerfile uses ADD with remote URL",
                    severity=Severity.MEDIUM,
                    description="The Dockerfile uses ADD to download remote content.",
                    impact=(
                        "Remote downloads during image build can introduce supply-chain "
                        "risk if content changes or is tampered with."
                    ),
                    remediation=(
                        "Avoid ADD with remote URLs. Download verified artifacts in a "
                        "controlled step or vendor trusted artifacts."
                    ),
                    file_path=relative_path,
                    line_number=line_number,
                    snippet=stripped,
                )
            )

    return findings


def analyze_single_dockerfile(repo_file: RepositoryFile) -> list[Finding]:
    path = Path(repo_file.absolute_path)
    content = read_text_file(path)
    relative_path = repo_file.relative_path

    findings: list[Finding] = []

    findings.extend(detect_latest_base_image(content, relative_path))
    findings.extend(detect_missing_user_instruction(content, relative_path))
    findings.extend(detect_sensitive_env_or_arg(content, relative_path))
    findings.extend(detect_remote_script_pipe_shell(content, relative_path))
    findings.extend(detect_apt_get_upgrade(content, relative_path))
    findings.extend(detect_missing_healthcheck(content, relative_path))
    findings.extend(detect_remote_add_instruction(content, relative_path))

    return findings


def analyze_dockerfile_security(
    target_path: Path,
    discovered_files: list[RepositoryFile],
) -> list[Finding]:
    findings: list[Finding] = []

    for repo_file in dockerfile_files(discovered_files):
        findings.extend(analyze_single_dockerfile(repo_file))

    return findings