from pathlib import Path
from typing import Any

import yaml

from supplysentinel.core.constants import Severity
from supplysentinel.core.models import (
    Finding,
    PolicyEvaluation,
    PolicyViolation,
    ScanResult,
)


CONTROL_RULE_MAP = {
    "require_lockfiles": ["DG-NPM-001"],
    "require_pinned_actions": ["DG-GHA-001"],
    "block_write_all_permissions": ["DG-GHA-002"],
    "block_curl_pipe_shell": ["DG-GHA-003"],
    "block_secret_echo": ["DG-GHA-004"],
    "block_dependency_confusion": ["DG-NPM-004", "DG-PY-003"],
    "block_pull_request_target": ["DG-GHA-005"],
}


def load_policy_file(policy_path: str) -> dict[str, Any]:
    """
    Load a YAML policy file from disk.
    """
    path = Path(policy_path)

    if not path.exists():
        raise FileNotFoundError(f"Policy file does not exist: {policy_path}")

    content = path.read_text(encoding="utf-8-sig")

    policy = yaml.safe_load(content)

    if policy is None:
        return {}

    if not isinstance(policy, dict):
        raise ValueError("Policy file must contain a YAML object at the root level.")

    return policy


def normalize_severity_list(values: list[Any]) -> list[str]:
    """
    Normalize severity strings into uppercase values.
    """
    normalized: list[str] = []

    for value in values:
        severity = str(value).upper().strip()

        if severity:
            normalized.append(severity)

    return normalized


def count_findings_by_severity(findings: list[Finding], severity: str) -> int:
    """
    Count findings matching a given severity.
    """
    return sum(1 for finding in findings if finding.severity.value == severity)


def get_findings_by_rule_ids(
    findings: list[Finding],
    rule_ids: list[str],
) -> list[Finding]:
    """
    Return findings that match selected rule IDs.
    """
    rule_id_set = set(rule_ids)
    return [finding for finding in findings if finding.rule_id in rule_id_set]


def evaluate_minimum_score(
    result: ScanResult,
    minimum_score: int,
) -> list[PolicyViolation]:
    """
    Check whether scan score satisfies minimum required score.
    """
    violations: list[PolicyViolation] = []

    if result.summary.security_score < minimum_score:
        violations.append(
            PolicyViolation(
                policy_id="POLICY-MIN-SCORE",
                severity="HIGH",
                message=(
                    f"Security score {result.summary.security_score}/100 is below "
                    f"the required minimum score of {minimum_score}/100."
                ),
            )
        )

    return violations


def evaluate_fail_on_severities(
    result: ScanResult,
    fail_on: list[str],
) -> list[PolicyViolation]:
    """
    Fail policy if selected severities are present.
    """
    violations: list[PolicyViolation] = []

    for severity in fail_on:
        count = count_findings_by_severity(result.findings, severity)

        if count > 0:
            violations.append(
                PolicyViolation(
                    policy_id=f"POLICY-FAIL-ON-{severity}",
                    severity=severity,
                    message=f"Policy blocks {severity} findings. Detected {count}.",
                )
            )

    return violations


def evaluate_max_allowed(
    result: ScanResult,
    max_allowed: dict[str, Any],
) -> list[PolicyViolation]:
    """
    Enforce maximum allowed finding counts by severity.
    """
    violations: list[PolicyViolation] = []

    severity_mapping = {
        "critical": Severity.CRITICAL.value,
        "high": Severity.HIGH.value,
        "medium": Severity.MEDIUM.value,
        "low": Severity.LOW.value,
        "info": Severity.INFO.value,
    }

    for policy_key, severity_value in severity_mapping.items():
        if policy_key not in max_allowed:
            continue

        allowed_count = int(max_allowed.get(policy_key, 0))
        actual_count = count_findings_by_severity(result.findings, severity_value)

        if actual_count > allowed_count:
            violations.append(
                PolicyViolation(
                    policy_id=f"POLICY-MAX-{severity_value}",
                    severity=severity_value,
                    message=(
                        f"Policy allows maximum {allowed_count} {severity_value} "
                        f"findings, but detected {actual_count}."
                    ),
                )
            )

    return violations


def evaluate_blocked_rules(
    result: ScanResult,
    blocked_rules: list[str],
) -> list[PolicyViolation]:
    """
    Fail policy when specific blocked rule IDs are detected.
    """
    violations: list[PolicyViolation] = []

    blocked_findings = get_findings_by_rule_ids(result.findings, blocked_rules)

    for finding in blocked_findings:
        violations.append(
            PolicyViolation(
                policy_id=f"POLICY-BLOCK-RULE-{finding.rule_id}",
                severity=finding.severity.value,
                message=(
                    f"Blocked rule detected: {finding.rule_id} - {finding.title} "
                    f"in {finding.evidence.file_path}."
                ),
            )
        )

    return violations


def evaluate_named_controls(
    result: ScanResult,
    rules: dict[str, Any],
) -> list[PolicyViolation]:
    """
    Evaluate named policy controls such as require_pinned_actions
    or block_dependency_confusion.
    """
    violations: list[PolicyViolation] = []

    for control_name, enabled in rules.items():
        if not enabled:
            continue

        mapped_rule_ids = CONTROL_RULE_MAP.get(control_name, [])

        if not mapped_rule_ids:
            continue

        matching_findings = get_findings_by_rule_ids(
            findings=result.findings,
            rule_ids=mapped_rule_ids,
        )

        for finding in matching_findings:
            violations.append(
                PolicyViolation(
                    policy_id=f"POLICY-CONTROL-{control_name.upper()}",
                    severity=finding.severity.value,
                    message=(
                        f"Control '{control_name}' failed because "
                        f"{finding.rule_id} was detected in {finding.evidence.file_path}."
                    ),
                )
            )

    return violations


def evaluate_policy(
    result: ScanResult,
    policy_path: str,
) -> PolicyEvaluation:
    """
    Evaluate a scan result against a policy-as-code YAML file.
    """
    policy = load_policy_file(policy_path)

    minimum_score = int(policy.get("minimum_score", 80))
    fail_on = normalize_severity_list(policy.get("fail_on", []))
    max_allowed = policy.get("max_allowed", {})
    blocked_rules = [str(rule_id) for rule_id in policy.get("blocked_rules", [])]
    rules = policy.get("rules", {})

    violations: list[PolicyViolation] = []

    violations.extend(
        evaluate_minimum_score(
            result=result,
            minimum_score=minimum_score,
        )
    )

    violations.extend(
        evaluate_fail_on_severities(
            result=result,
            fail_on=fail_on,
        )
    )

    violations.extend(
        evaluate_max_allowed(
            result=result,
            max_allowed=max_allowed,
        )
    )

    violations.extend(
        evaluate_blocked_rules(
            result=result,
            blocked_rules=blocked_rules,
        )
    )

    violations.extend(
        evaluate_named_controls(
            result=result,
            rules=rules,
        )
    )

    return PolicyEvaluation(
        policy_file=str(Path(policy_path).resolve()),
        passed=len(violations) == 0,
        minimum_score=minimum_score,
        actual_score=result.summary.security_score,
        fail_on_severities=fail_on,
        violations=violations,
    )