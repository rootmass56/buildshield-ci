import json
from hashlib import sha256

from supplysentinel import __version__
from supplysentinel.core.constants import Severity
from supplysentinel.core.models import Finding, ScanResult


SARIF_SCHEMA_URL = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"


def normalize_artifact_uri(file_path: str) -> str:
    """
    Convert file paths into SARIF-friendly URI format.
    SARIF prefers forward slashes.
    """
    normalized = file_path.replace("\\", "/").strip()

    if normalized.startswith("./"):
        normalized = normalized[2:]

    if not normalized:
        return "unknown"

    return normalized


def sarif_level_from_severity(severity: Severity) -> str:
    """
    Convert BuildShield-CI severity into SARIF result level.
    """
    if severity in {Severity.CRITICAL, Severity.HIGH}:
        return "error"

    if severity == Severity.MEDIUM:
        return "warning"

    return "note"


def security_severity_score(severity: Severity) -> str:
    """
    Convert severity into GitHub security-severity style score.
    """
    mapping = {
        Severity.CRITICAL: "9.5",
        Severity.HIGH: "8.0",
        Severity.MEDIUM: "5.5",
        Severity.LOW: "3.0",
        Severity.INFO: "1.0",
    }

    return mapping.get(severity, "1.0")


def fingerprint_for_finding(finding: Finding) -> str:
    """
    Create deterministic fingerprint to help GitHub track duplicate alerts.
    """
    source = "|".join(
        [
            finding.rule_id,
            normalize_artifact_uri(finding.evidence.file_path),
            str(finding.evidence.line_number or 1),
            finding.evidence.snippet or "",
            finding.title,
        ]
    )

    return sha256(source.encode("utf-8")).hexdigest()


def build_sarif_rule(finding: Finding) -> dict:
    """
    Convert a BuildShield-CI finding into a SARIF rule definition.
    """
    return {
        "id": finding.rule_id,
        "name": finding.title,
        "shortDescription": {
            "text": finding.title,
        },
        "fullDescription": {
            "text": finding.description,
        },
        "help": {
            "text": (
                f"{finding.description}\n\n"
                f"Impact: {finding.impact}\n\n"
                f"Remediation: {finding.remediation}"
            ),
            "markdown": (
                f"### {finding.title}\n\n"
                f"**Description:** {finding.description}\n\n"
                f"**Impact:** {finding.impact}\n\n"
                f"**Remediation:** {finding.remediation}"
            ),
        },
        "properties": {
            "category": finding.category.value,
            "precision": finding.confidence.lower(),
            "security-severity": security_severity_score(finding.severity),
            "tags": [
                "security",
                "supply-chain",
                "ci-cd",
                finding.category.value.lower(),
            ],
        },
    }


def build_sarif_result(finding: Finding) -> dict:
    """
    Convert a BuildShield-CI finding into a SARIF result.
    """
    artifact_uri = normalize_artifact_uri(finding.evidence.file_path)
    line_number = finding.evidence.line_number or 1

    message = (
        f"{finding.title}. "
        f"{finding.description} "
        f"Impact: {finding.impact} "
        f"Remediation: {finding.remediation}"
    )

    return {
        "ruleId": finding.rule_id,
        "level": sarif_level_from_severity(finding.severity),
        "message": {
            "text": message,
        },
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": artifact_uri,
                    },
                    "region": {
                        "startLine": line_number,
                    },
                }
            }
        ],
        "partialFingerprints": {
            "primaryLocationLineHash": fingerprint_for_finding(finding),
        },
        "properties": {
            "severity": finding.severity.value,
            "category": finding.category.value,
            "confidence": finding.confidence,
            "impact": finding.impact,
            "remediation": finding.remediation,
            "reference": finding.reference or "",
            "evidence": finding.evidence.snippet or "",
        },
    }


def unique_rules_from_findings(findings: list[Finding]) -> list[dict]:
    """
    Build a unique SARIF rule list from findings.
    """
    rules_by_id: dict[str, dict] = {}

    for finding in findings:
        if finding.rule_id not in rules_by_id:
            rules_by_id[finding.rule_id] = build_sarif_rule(finding)

    return list(rules_by_id.values())


def generate_scan_sarif(result: ScanResult) -> str:
    """
    Generate SARIF 2.1.0 report from BuildShield-CI scan results.
    """
    sarif_document = {
        "$schema": SARIF_SCHEMA_URL,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "BuildShield-CI",
                        "informationUri": "https://github.com/rootmass56/buildshield-ci",
                        "semanticVersion": __version__,
                        "rules": unique_rules_from_findings(result.findings),
                    }
                },
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "properties": {
                            "targetPath": result.summary.target_path,
                            "securityScore": result.summary.security_score,
                            "riskLevel": result.summary.risk_level.value,
                            "buildGateStatus": result.risk_profile.build_gate_status,
                            "findingsCount": result.summary.findings_count,
                        },
                    }
                ],
                "results": [
                    build_sarif_result(finding)
                    for finding in result.findings
                ],
                "properties": {
                    "scanner": "BuildShield-CI",
                    "summary": {
                        "targetPath": result.summary.target_path,
                        "securityScore": result.summary.security_score,
                        "riskLevel": result.summary.risk_level.value,
                        "criticalCount": result.summary.critical_count,
                        "highCount": result.summary.high_count,
                        "mediumCount": result.summary.medium_count,
                        "lowCount": result.summary.low_count,
                        "infoCount": result.summary.info_count,
                    },
                },
            }
        ],
    }

    return json.dumps(sarif_document, indent=2)