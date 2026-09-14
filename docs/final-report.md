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
| Frontend | HTML, CSS, JavaScript |
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

### Comparison

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

Current verified test result:

```text
53 passed
```

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

## 17. Current Limitations

- Static-analysis focus
- Limited ecosystem coverage
- Heuristic dependency-confusion detection
- No enterprise authentication/RBAC
- No multi-tenant isolation
- No distributed scan-job architecture
- No Kubernetes or GitLab CI analyzer yet

## 18. Future Roadmap

Potential next-stage improvements include:

1. Authentication and RBAC
2. Repository/webhook-triggered scans
3. More package ecosystems
4. Kubernetes manifest analysis
5. GitLab CI analysis
6. Advanced vulnerability prioritization
7. AI-assisted remediation with grounding
8. Enterprise policy profiles
9. Operational observability and rate limiting
10. Hardened cloud deployment patterns

## 19. Conclusion

BuildShield-CI demonstrates end-to-end cybersecurity engineering across supply-chain security, static analysis, DevSecOps policy enforcement, CI/CD hardening, vulnerability intelligence, reporting, dashboard development, persistence, testing, and containerization.

It is suitable as a placement, internship, and portfolio project while remaining explicit about the difference between a controlled deployment-ready demonstration and a fully hardened enterprise production service.
