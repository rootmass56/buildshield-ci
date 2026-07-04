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


class CategoryRisk(BaseModel):
    category: FindingCategory
    finding_count: int
    penalty_points: float
    risk_score: int
    risk_level: RiskLevel


class TopRiskDriver(BaseModel):
    rule_id: str
    title: str
    severity: Severity
    category: FindingCategory
    file_path: str
    line_number: int | None = None
    contribution_points: float


class RiskProfile(BaseModel):
    overall_security_score: int
    overall_risk_level: RiskLevel
    build_gate_status: str
    build_gate_reason: str
    category_risks: list[CategoryRisk]
    top_risk_drivers: list[TopRiskDriver]


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
    risk_profile: RiskProfile
    discovered_files: list[RepositoryFile]
    findings: list[Finding]


class ComparisonResult(BaseModel):
    baseline_label: str
    target_label: str
    baseline: ScanResult
    target: ScanResult
    score_delta: int
    findings_reduced: int
    risk_reduction_percentage: float
    verdict: str