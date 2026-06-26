from pathlib import Path
from pydantic import BaseModel, Field

from supplysentinel.core.constants import Severity, RiskLevel, FindingCategory


class Evidence(BaseModel):
    file_path: str
    line_number: int | None = None
    snippet: str | None = None


class Finding(BaseModel):
    rule_id: str
    title: str
    severity: Severity
    category: FindingCategory
    confidence: str = Field(default="MEDIUM")
    description: str
    impact: str
    evidence: Evidence
    remediation: str
    reference: str | None = None


class RepositoryFile(BaseModel):
    absolute_path: Path
    relative_path: str
    file_name: str
    file_type: str
    size_bytes: int


class ScanSummary(BaseModel):
    target_path: str
    files_discovered: int
    files_scanned: int
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    security_score: int
    risk_level: RiskLevel


class ScanResult(BaseModel):
    summary: ScanSummary
    discovered_files: list[RepositoryFile]
    findings: list[Finding]