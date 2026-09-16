import re
import shlex
from pathlib import PurePosixPath

from supplysentinel.analyzers.utils import read_text_file
from supplysentinel.core.constants import FindingCategory, Severity
from supplysentinel.core.models import Evidence, Finding, RepositoryFile


FULL_COMMIT_SHA_PATTERN = re.compile(r"@[a-fA-F0-9]{40}$")
USES_PATTERN = re.compile(r"uses:\s*([^\s#]+)")
WRITE_ALL_PATTERN = re.compile(
    r"^permissions:\s*['\"]?write-all['\"]?\s*(?:#.*)?$",
    re.IGNORECASE,
)
PULL_REQUEST_TARGET_PATTERN = re.compile(
    r"^pull_request_target\s*:",
    re.IGNORECASE,
)
SECRET_EXPRESSION_PATTERN = re.compile(
    r"\$\{\{\s*secrets\.",
    re.IGNORECASE,
)
OUTPUT_COMMANDS = {
    "echo",
    "printf",
    "write-host",
    "write-output",
}


def extract_run_command(line: str) -> str | None:
    match = re.match(
        r"^(?:-\s*)?run:\s*(.+)$",
        line,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def shell_tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(
            command,
            posix=True,
            punctuation_chars="|&;",
        )
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return []


def command_name(token: str) -> str:
    normalized = token.replace("\\", "/")
    return PurePosixPath(normalized).name.lower()


def has_remote_pipe_to_shell(command: str) -> bool:
    tokens = shell_tokens(command)

    for index, token in enumerate(tokens):
        if command_name(token) not in {"curl", "wget"}:
            continue

        for pipe_index in range(index + 1, len(tokens)):
            if tokens[pipe_index] != "|":
                continue

            if pipe_index + 1 >= len(tokens):
                break

            return command_name(tokens[pipe_index + 1]) in {
                "bash",
                "sh",
            }

    return False


def prints_secret_expression(command: str) -> bool:
    if not SECRET_EXPRESSION_PATTERN.search(command):
        return False

    tokens = shell_tokens(command)
    if not tokens:
        return False

    return command_name(tokens[0]) in OUTPUT_COMMANDS


def analyze_github_actions(discovered_files: list[RepositoryFile]) -> list[Finding]:
    findings: list[Finding] = []

    workflow_files = [
        repo_file
        for repo_file in discovered_files
        if repo_file.file_type == "github_actions_workflow"
    ]

    for repo_file in workflow_files:
        content = read_text_file(repo_file.absolute_path)
        lines = content.splitlines()

        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            uses_match = USES_PATTERN.search(line)
            if uses_match:
                action_ref = uses_match.group(1)

                if (
                    "@" in action_ref
                    and not FULL_COMMIT_SHA_PATTERN.search(
                        action_ref
                    )
                ):
                    findings.append(
                        Finding(
                            rule_id="DG-GHA-001",
                            title="GitHub Action not pinned to full commit SHA",
                            severity=Severity.HIGH,
                            category=FindingCategory.CICD,
                            confidence="HIGH",
                            description=(
                                f"The workflow uses '{action_ref}' "
                                "without pinning it to a full commit SHA."
                            ),
                            impact=(
                                "A mutable tag or branch can change over time, "
                                "allowing unexpected third-party action code "
                                "to run in CI/CD."
                            ),
                            evidence=Evidence(
                                file_path=repo_file.relative_path,
                                line_number=line_number,
                                snippet=line,
                            ),
                            remediation=(
                                "Pin third-party GitHub Actions to a "
                                "full-length commit SHA after reviewing "
                                "the action source."
                            ),
                            reference=(
                                "https://docs.github.com/en/actions/"
                                "security-for-github-actions/security-guides/"
                                "security-hardening-for-github-actions"
                            ),
                        )
                    )

            if WRITE_ALL_PATTERN.match(line):
                findings.append(
                    Finding(
                        rule_id="DG-GHA-002",
                        title=(
                            "Over-permissive GitHub Actions "
                            "token permissions"
                        ),
                        severity=Severity.HIGH,
                        category=FindingCategory.CICD,
                        confidence="HIGH",
                        description=(
                            "The workflow grants write-all permissions "
                            "to the GITHUB_TOKEN."
                        ),
                        impact=(
                            "If the workflow is compromised, the attacker "
                            "may gain broad write access to repository "
                            "resources."
                        ),
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation=(
                            "Use least-privilege permissions such as "
                            "contents: read and grant write permissions "
                            "only when required."
                        ),
                        reference=(
                            "https://docs.github.com/en/actions/"
                            "security-for-github-actions/security-guides/"
                            "security-hardening-for-github-actions"
                        ),
                    )
                )

            run_command = extract_run_command(line)

            if (
                run_command is not None
                and has_remote_pipe_to_shell(run_command)
            ):
                findings.append(
                    Finding(
                        rule_id="DG-GHA-003",
                        title="Remote script piped directly to shell",
                        severity=Severity.HIGH,
                        category=FindingCategory.BUILD_SCRIPT,
                        confidence="HIGH",
                        description=(
                            "The workflow downloads a remote script and "
                            "pipes it directly into a shell."
                        ),
                        impact=(
                            "Remote script execution can compromise the "
                            "CI/CD runner if the downloaded content is "
                            "malicious or tampered with."
                        ),
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation=(
                            "Download scripts from trusted sources, verify "
                            "checksums/signatures, and avoid direct "
                            "curl/wget pipe-to-shell execution."
                        ),
                        reference=(
                            "https://owasp.org/www-project-top-10-ci-cd-"
                            "security-risks/"
                        ),
                    )
                )

            if (
                run_command is not None
                and prints_secret_expression(run_command)
            ):
                findings.append(
                    Finding(
                        rule_id="DG-GHA-004",
                        title="Secret value printed in workflow",
                        severity=Severity.CRITICAL,
                        category=FindingCategory.SECRETS,
                        confidence="HIGH",
                        description=(
                            "The workflow appears to print a secret "
                            "value to logs."
                        ),
                        impact=(
                            "Secrets printed to CI/CD logs may be exposed "
                            "to unauthorized users or retained in build "
                            "history."
                        ),
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation=(
                            "Never print secrets. Pass secrets only to "
                            "trusted tools through environment variables "
                            "or secure secret handling mechanisms."
                        ),
                        reference=(
                            "https://docs.github.com/en/actions/"
                            "security-for-github-actions/security-guides/"
                            "using-secrets-in-github-actions"
                        ),
                    )
                )

            if PULL_REQUEST_TARGET_PATTERN.match(line):
                findings.append(
                    Finding(
                        rule_id="DG-GHA-005",
                        title="Use of pull_request_target trigger",
                        severity=Severity.HIGH,
                        category=FindingCategory.CICD,
                        confidence="MEDIUM",
                        description=(
                            "The workflow uses pull_request_target, which "
                            "runs with elevated context compared to "
                            "pull_request."
                        ),
                        impact=(
                            "Unsafe use of pull_request_target with "
                            "untrusted code can expose secrets or write "
                            "permissions."
                        ),
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation=(
                            "Use pull_request where possible. If "
                            "pull_request_target is required, avoid "
                            "checking out or executing untrusted pull "
                            "request code."
                        ),
                        reference=(
                            "https://docs.github.com/en/actions/"
                            "security-for-github-actions/security-guides/"
                            "security-hardening-for-github-actions"
                        ),
                    )
                )

    return findings
