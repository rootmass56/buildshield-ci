import re

from supplysentinel.analyzers.utils import read_text_file
from supplysentinel.core.constants import FindingCategory, Severity
from supplysentinel.core.models import Evidence, Finding, RepositoryFile


FULL_COMMIT_SHA_PATTERN = re.compile(r"@[a-fA-F0-9]{40}$")
USES_PATTERN = re.compile(r"uses:\s*([^\s#]+)")
CURL_PIPE_SHELL_PATTERN = re.compile(r"(curl|wget).*\|.*(bash|sh)", re.IGNORECASE)
SECRET_ECHO_PATTERN = re.compile(r"(echo|Write-Host).*\$\{\{\s*secrets\.", re.IGNORECASE)


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

            uses_match = USES_PATTERN.search(line)
            if uses_match:
                action_ref = uses_match.group(1)

                if "@" in action_ref and not FULL_COMMIT_SHA_PATTERN.search(action_ref):
                    findings.append(
                        Finding(
                            rule_id="DG-GHA-001",
                            title="GitHub Action not pinned to full commit SHA",
                            severity=Severity.HIGH,
                            category=FindingCategory.CICD,
                            confidence="HIGH",
                            description=f"The workflow uses '{action_ref}' without pinning it to a full commit SHA.",
                            impact="A mutable tag or branch can change over time, allowing unexpected third-party action code to run in CI/CD.",
                            evidence=Evidence(
                                file_path=repo_file.relative_path,
                                line_number=line_number,
                                snippet=line,
                            ),
                            remediation="Pin third-party GitHub Actions to a full-length commit SHA after reviewing the action source.",
                            reference="https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions",
                        )
                    )

            if "permissions: write-all" in line:
                findings.append(
                    Finding(
                        rule_id="DG-GHA-002",
                        title="Over-permissive GitHub Actions token permissions",
                        severity=Severity.HIGH,
                        category=FindingCategory.CICD,
                        confidence="HIGH",
                        description="The workflow grants write-all permissions to the GITHUB_TOKEN.",
                        impact="If the workflow is compromised, the attacker may gain broad write access to repository resources.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation="Use least-privilege permissions such as contents: read and grant write permissions only when required.",
                        reference="https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions",
                    )
                )

            if CURL_PIPE_SHELL_PATTERN.search(line):
                findings.append(
                    Finding(
                        rule_id="DG-GHA-003",
                        title="Remote script piped directly to shell",
                        severity=Severity.HIGH,
                        category=FindingCategory.BUILD_SCRIPT,
                        confidence="HIGH",
                        description="The workflow downloads a remote script and pipes it directly into a shell.",
                        impact="Remote script execution can compromise the CI/CD runner if the downloaded content is malicious or tampered with.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation="Download scripts from trusted sources, verify checksums/signatures, and avoid direct curl/wget pipe-to-shell execution.",
                        reference="https://owasp.org/www-project-top-10-ci-cd-security-risks/",
                    )
                )

            if SECRET_ECHO_PATTERN.search(line):
                findings.append(
                    Finding(
                        rule_id="DG-GHA-004",
                        title="Secret value printed in workflow",
                        severity=Severity.CRITICAL,
                        category=FindingCategory.SECRETS,
                        confidence="HIGH",
                        description="The workflow appears to print a secret value to logs.",
                        impact="Secrets printed to CI/CD logs may be exposed to unauthorized users or retained in build history.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation="Never echo secrets. Pass secrets only to trusted tools through environment variables or secure secret handling mechanisms.",
                        reference="https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions",
                    )
                )

            if "pull_request_target:" in line:
                findings.append(
                    Finding(
                        rule_id="DG-GHA-005",
                        title="Use of pull_request_target trigger",
                        severity=Severity.HIGH,
                        category=FindingCategory.CICD,
                        confidence="MEDIUM",
                        description="The workflow uses pull_request_target, which runs with elevated context compared to pull_request.",
                        impact="Unsafe use of pull_request_target with untrusted code can expose secrets or write permissions.",
                        evidence=Evidence(
                            file_path=repo_file.relative_path,
                            line_number=line_number,
                            snippet=line,
                        ),
                        remediation="Use pull_request where possible. If pull_request_target is required, avoid checking out or executing untrusted pull request code.",
                        reference="https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions",
                    )
                )

    return findings