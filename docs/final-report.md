# BuildShield-CI Final Project Report

## 1. Executive Overview

BuildShield-CI is an advanced CI/CD supply-chain risk analyzer and dependency confusion defense platform. It performs passive static analysis of repository configuration and automation files, converts results into structured security findings, calculates risk, enforces policy-as-code, generates multiple report formats, integrates with GitHub Code Scanning, and provides dashboard/API visibility.

The project covers npm, Python dependencies, GitHub Actions, Dockerfiles, private registry controls, SBOM-lite dependency inventory, OSV vulnerability intelligence, SQLite history, Docker deployment, and automated regression testing.

## 2. Problem Statement

Modern software delivery depends on package registries, third-party actions, build scripts, containers, secrets, and automated pipelines. Misconfiguration can create risks such as dependency confusion, mutable dependency resolution, excessive workflow privileges, secret leakage, unsafe remote script execution, and insecure container builds.

BuildShield-CI addresses these risks before deployment through static analysis and policy enforcement.

## 3. Objectives

The project objectives are to:

1. Detect dependency confusion indicators.
2. Detect insecure npm and Python dependency configuration.
3. Detect GitHub Actions workflow risks.
4. Detect Dockerfile hardening issues.
5. Produce evidence-backed findings with remediation.
6. Calculate security score, risk level, and top drivers.
7. Enforce YAML policy-as-code.
8. Generate JSON, Markdown, HTML, and SARIF reports.
9. Integrate with GitHub Actions and Code Scanning.
10. Build SBOM-lite dependency inventory.
11. Add OSV vulnerability intelligence.
12. Provide FastAPI/dashboard visibility.
13. Persist history and risk trends with SQLite.
14. Support Docker and Docker Compose deployment.
15. Validate behavior through automated tests and controlled vulnerable/hardened samples.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.13 |
| CLI | Typer |
| Terminal UI | Rich |
| Models | Pydantic |
| Backend | FastAPI |
| Storage | SQLite |
| Frontend | React 19, TypeScript 7, Vite 8 |
| Policy | YAML |
| CI/CD | GitHub Actions |
| Reports | JSON, Markdown, HTML, SARIF |
| Vulnerability Intelligence | OSV |
| Deployment | Docker, Docker Compose |
| Testing | Pytest |

## 5. System Architecture

```text
Repository
   |
   v
File Discovery
   |
   v
Explicit Analyzer Layer
   |-- npm
   |-- Python
   |-- GitHub Actions
   `-- Dockerfile
   |
   v
Normalized Findings
   |
   +--> Risk Scoring
   +--> Policy-as-Code
   +--> Reports / SARIF
   +--> SBOM-lite / OSV
   +--> FastAPI / Dashboard
   `--> SQLite History
```

A maintenance refactor removed dynamic analyzer-name guessing and hidden fallback analyzers. Canonical analyzer functions are now invoked explicitly and protected by regression tests.

## 6. Implemented Security Analysis

### npm

- Missing lockfile
- Loose/mutable versions
- Risky lifecycle scripts
- Potential dependency confusion
- Missing trusted private registry handling

### Python

- Unpinned dependencies
- Loose version ranges
- Potential dependency confusion
- Missing trusted package index handling

### GitHub Actions

- Mutable action refs
- Excessive token permissions
- Pipe-to-shell
- Secret echo
- Risky `pull_request_target`

### Dockerfile

- Unpinned/latest base image
- Missing non-root user
- Potential secret in `ENV`/`ARG`
- Remote script execution
- `apt-get upgrade`
- Missing health check

## 7. Risk and Policy

The scoring engine produces:

- Overall security score
- Risk level
- Category risk breakdown
- Top risk drivers
- Build gate status/reason

The policy engine enforces:

- Minimum score
- Maximum severity counts
- Required lockfiles
- Pinned GitHub Actions
- Secret handling
- Pipe-to-shell restrictions
- Dependency confusion controls
- `pull_request_target` restrictions

## 8. Controlled Demonstration Results

### Vulnerable sample

| Metric | Result |
|---|---:|
| Files discovered/scanned | 5 / 5 |
| Findings | 22 |
| Critical | 4 |
| High | 10 |
| Medium | 7 |
| Low | 1 |
| Security Score | 5/100 |
| Risk Level | CRITICAL |
| Build Gate | FAILED |
| Policy | FAILED |

### Hardened sample

| Metric | Result |
|---|---:|
| Files discovered/scanned | 7 / 7 |
| Findings | 0 |
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Security Score | 100/100 |
| Risk Level | LOW |
| Build Gate | PASSED |
| Policy | PASSED |

### Representative realistic application

| Metric | Result |
|---|---:|
| Findings | 3 |
| Critical | 0 |
| High | 0 |
| Medium | 2 |
| Low | 1 |
| Security Score | 81/100 |
| Risk Level | MEDIUM |
| Build Gate | WARNING |
| Policy | PASSED |

Natural comparison from the intentionally vulnerable benchmark to the realistic application improves the score from 5 to 81, reduces findings from 22 to 3, and reports an 80% controlled risk reduction with `PARTIALLY_IMPROVED`.

The realistic profile is the default routine demo. The 100/100 hardened fixture remains a controlled regression endpoint rather than an implied requirement for every real application.

### Controlled benchmark comparison

| Metric | Result |
|---|---:|
| Score improvement | +95 |
| Findings reduced | 22 |
| Risk reduction | 100% |
| Verdict | `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED` |

These figures are from controlled repository fixtures and should not be interpreted as a universal security measurement for arbitrary production systems.

## 9. Reporting and GitHub Integration

BuildShield-CI generates:

- JSON
- Markdown
- HTML
- SARIF 2.1.0
- Comparison reports
- Inventory output
- OSV intelligence output

SARIF is uploaded by GitHub Actions to GitHub Code Scanning. Alerts produced from `samples/vulnerable-repo` are intentionally generated demonstration alerts.

The workflow also uploads generated reports as artifacts.

## 10. SBOM-lite and OSV Intelligence

The dependency inventory extracts package metadata from supported npm and Python inputs. The OSV integration can create an offline query plan or perform online lookups for pinned dependencies.

OSV results are dynamic; documentation does not hard-code a CVE/vulnerability count.

## 11. API, Dashboard, and History

The FastAPI backend and web dashboard provide:

- Scan execution
- Comparison
- Findings exploration
- Policy result visibility
- Reports
- SBOM-lite inventory
- OSV intelligence
- Scan history
- Risk trend data

SQLite stores local scan-history/trend information.

## 12. CI/CD Self-Hardening

BuildShield-CI's own workflow uses immutable full commit SHAs for third-party GitHub Actions.

A regression test prevents accidental reintroduction of mutable refs such as `@main`, `@v6`, or `@v7`.

The project also self-scans `.github` and currently reports:

```text
0 findings
100/100
LOW
PASSED
```

## 13. Deployment

BuildShield-CI supports local execution, Docker, and Docker Compose.

Container controls include:

- Non-root execution
- Health check
- Port 8080
- Persistent report/data volumes in Compose

The project is deployment-ready for controlled environments and demonstrates a production-style architecture. Enterprise production deployment would require additional identity, authorization, isolation, secret-management, rate-limiting, network, logging, monitoring, backup, and governance controls.

## 14. Testing and Reliability

Current verified Windows Python regression:

```text
295 passed, 2 skipped
```

The final pre-release validation also verifies the realistic application at 81/100 with 3 findings, MEDIUM risk, a WARNING build gate and passing policy, while preserving the original 22 -> 0 vulnerable/hardened controlled benchmark.

H9 also adds a fixed 100-case deterministic adversarial corpus across 20 static rules. The pre-hardening baseline was 41 TP / 45 TN / 4 FP / 10 FN (micro F1 0.854167). After bounded H9D hardening, the unchanged corpus evaluates at 51 TP / 49 TN / 0 FP / 0 FN. These corpus metrics are regression evidence only and are not real-world accuracy estimates.

Coverage includes:

- Scanner engine
- Analyzer routing
- npm analyzer
- Python analyzer
- GitHub Actions analyzer
- Dockerfile analyzer
- Policy engine
- Comparison engine
- Report generation
- SARIF
- CLI behavior
- Dashboard APIs
- Scan history
- SBOM-lite inventory
- OSV intelligence
- Deployment files
- Workflow SHA pinning
- Repository hygiene

## 15. Repository Hygiene

The maintenance baseline includes:

- Deterministic line-ending rules with `.gitattributes`
- Clean `.gitignore`
- Reduced Docker build context via `.dockerignore`
- No blanket pytest warning suppression
- Explicit dev dependencies
- GitHub project metadata URLs
- Generated reports and SQLite runtime data excluded from source control

## 16. Ethical and Safety Scope

BuildShield-CI is defensive and passive.

It does not:

- Exploit systems
- Publish malicious packages
- Execute malware
- Exfiltrate credentials
- Attack package registries
- Scan unauthorized systems
- Perform destructive actions

All intentionally vulnerable content is confined to controlled sample files.

## 17. H1-H9 Hardening Closure and Final Scope Boundaries

The v0.12.7 tag remains the historical frozen baseline. On the active hardening branch, H1-H9 are complete and the H9 checkpoint has passed hosted CI.

The final candidate now includes the in-scope workspace boundary, single-tenant authentication/authorization, browser security, request/resource controls, safe public errors and audit logging, report/history retention controls, hardened container/runtime behavior, reproducible build/CI controls, and deterministic adversarial regression evaluation.

The following are intentional final scope boundaries, not missing future features:

- analysis remains focused on npm, Python, GitHub Actions and Dockerfiles;
- dependency-confusion detection remains a static heuristic security control rather than an active registry attack;
- no Maven, Go, NuGet, Rust or other new package-ecosystem analyzers are planned;
- no Kubernetes manifest analyzer is planned;
- no GitLab CI or Jenkins analyzer is planned;
- no AI/LLM remediation assistant is planned;
- no multi-tenant SaaS, distributed worker architecture or cloud-provider-specific deployment stack is planned.

Enterprise deployment would require organization-specific controls beyond the current single-instance scope, including external identity/RBAC integration, multi-tenant isolation where applicable, centralized secret management, production TLS/network controls, shared observability, backup/recovery and operational governance.

## 18. Final v1.0.0 Release Roadmap

H1-H10 local engineering and release acceptance are complete. The earlier H10 checkpoint `7bc58e905789fe2990223d3cf520729c14d98e1f` passed hosted CI. After that checkpoint, the product received its final professional UI polish and representative realistic application profile; those changes passed frontend quality gates, backend/API contracts, production Docker smoke, a 295 passed / 2 skipped Windows regression, live browser review and repository sanitation.

No broad feature roadmap follows H10. The only remaining actions are release engineering: create the replacement final checkpoint commit, require hosted CI on that exact state, review/merge the PR, verify `main`, create the annotated `v1.0.0` tag and GitHub release, and then freeze normal feature development except critical corrective patches.

## 19. Conclusion

BuildShield-CI demonstrates end-to-end cybersecurity engineering across supply-chain security, static analysis, DevSecOps policy enforcement, CI/CD hardening, vulnerability intelligence, reporting, dashboard development, persistence, testing, and containerization.

**v0.12.7 remains the completed historical baseline.** The current `1.0.0` candidate has completed H1-H10 local acceptance, final UI/realistic-profile validation, live browser review and repository sanitation. It must not be described as the final tagged v1.0.0 release until the replacement final checkpoint passes hosted CI, the PR is merged, `main` is verified, and the annotated tag/GitHub release are created and verified. After that verified release, planned feature development ends except for corrective security or release-breaking patches.
