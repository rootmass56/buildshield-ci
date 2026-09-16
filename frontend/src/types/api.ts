export interface ReportLink { run_id: string; filename: string; download_url: string; }
export interface SampleRepository { label: string; path: string; description: string; }
export interface SampleRepositoriesResponse { repositories: SampleRepository[]; default_policy: string; }
export interface ScanSummary { target_path: string; files_discovered: number; files_scanned: number; findings_count: number; critical_count: number; high_count: number; medium_count: number; low_count: number; info_count: number; security_score: number; risk_level: string; }
export interface Evidence { file_path: string; line_number: number | null; snippet: string | null; }
export interface Finding { rule_id: string; title: string; severity: string; category: string; confidence: string; description: string; impact: string; evidence: Evidence; remediation: string; reference: string | null; }
export interface CategoryRisk { category: string; finding_count: number; penalty_points: number; risk_score: number; risk_level: string; }
export interface TopRiskDriver { rule_id: string; title: string; severity: string; category: string; file_path: string; line_number: number | null; contribution_points: number; }
export interface RiskProfile { overall_security_score: number; overall_risk_level: string; build_gate_status: string; build_gate_reason: string; category_risks: CategoryRisk[]; top_risk_drivers: TopRiskDriver[]; }
export interface PolicyViolation { policy_id: string; severity: string; message: string; }
export interface PolicyEvaluation { policy_file: string; passed: boolean; minimum_score: number; actual_score: number; fail_on_severities: string[]; violations: PolicyViolation[]; }
export interface HistoryRecord { id: number; run_id: string; created_at: string; kind: string; target_path: string; security_score: number; risk_level: string; findings_count: number; critical_count: number; high_count: number; medium_count: number; low_count: number; info_count: number; policy_status: string; build_gate_status: string; report_count: number; }
export interface ScanResultView { run_id: string; kind: 'scan'; target_path: string; summary: ScanSummary; risk_profile: RiskProfile; policy_evaluation: PolicyEvaluation | null; findings: Finding[]; reports: ReportLink[]; history_record: HistoryRecord; }
export interface DependencyRecord { ecosystem: 'npm' | 'python'; name: string; declared_version: string | null; dependency_group: string; file_path: string; line_number: number | null; is_pinned: boolean; is_loose: boolean; is_internal_candidate: boolean; private_registry_configured: boolean; lockfile_present: boolean | null; risk_indicators: string[]; }
export interface DependencyInventorySummary { total_dependencies: number; npm_dependencies: number; python_dependencies: number; pinned_dependencies: number; loose_dependencies: number; unpinned_dependencies: number; internal_candidate_dependencies: number; dependencies_missing_private_registry: number; npm_dependencies_without_lockfile: number; ecosystems_detected: string[]; }
export interface DependencyInventory { target_path: string; generated_at: string; summary: DependencyInventorySummary; dependencies: DependencyRecord[]; }
export interface InventoryResponse { run_id: string; kind: 'inventory'; target_path: string; inventory: DependencyInventory; reports: ReportLink[]; }
export interface OsvVulnerabilityRecord { vulnerability_id: string; modified: string | null; detail_url: string; }
export interface OsvPackageResult { ecosystem: string; osv_ecosystem: string | null; package_name: string; version: string | null; file_path: string; line_number: number | null; vulnerability_count: number; vulnerabilities: OsvVulnerabilityRecord[]; skipped_reason: string | null; }
export interface OsvSummary { target_path: string; generated_at: string; total_dependencies_seen: number; queryable_dependencies: number; skipped_dependencies: number; vulnerable_dependencies: number; total_vulnerabilities: number; online_lookup_status: string; error_message: string | null; }
export interface OsvReport { summary: OsvSummary; package_results: OsvPackageResult[]; }
export interface VulnerabilityIntelligenceResponse { run_id: string; kind: 'vulnerability_intelligence'; target_path: string; vulnerability_report: OsvReport; reports: ReportLink[]; }
export interface EmbeddedScanResult { summary: ScanSummary; risk_profile: RiskProfile; findings: Finding[]; policy_evaluation: PolicyEvaluation | null; }
export interface ComparisonResult { baseline_label: string; target_label: string; baseline: EmbeddedScanResult; target: EmbeddedScanResult; score_delta: number; findings_reduced: number; risk_reduction_percentage: number; verdict: string; }
export interface ComparisonResponse { run_id: string; kind: 'comparison'; comparison: ComparisonResult; reports: ReportLink[]; }
export interface HistoryResponse { history: HistoryRecord[]; }
export interface TrendResponse { trend: HistoryRecord[]; }
export interface ReportsResponse { reports: ReportLink[]; }
export interface HealthResponse { status: string; product: string; version: string; }
