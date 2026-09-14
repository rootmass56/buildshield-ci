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
57 passed
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

## 17. Current v0.12.7 Limitations and Final Scope Boundaries

The frozen v0.12.7 baseline is complete and verified, but it is not yet the final hardened web-enabled product. The following are current limitations that the finalization program will address where they are in scope:

- API filesystem access is not yet constrained to explicit approved workspace roots.
- API authentication/authorization is not yet implemented.
- Dashboard rendering still requires final XSS/browser-security hardening.
- Request/resource controls and safe public error handling require hardening.
- Report/history storage and retention require final security review.
- Docker/runtime controls can be tightened beyond the already verified non-root baseline.
- CI/dependency reproducibility and least-privilege controls can be improved.
- The final adversarial-security and dead-code audit has not yet been performed.

The following are intentional final scope boundaries, not missing future features:

- Analysis remains focused on npm, Python, GitHub Actions, and Dockerfiles.
- Dependency-confusion detection remains a static heuristic security control rather than an active registry attack.
- No Maven, Go, NuGet, Rust, or other new package-ecosystem analyzers are planned.
- No Kubernetes manifest analyzer is planned.
- No GitLab CI or Jenkins analyzer is planned.
- No AI/LLM remediation assistant is planned.
- No multi-tenant SaaS, distributed worker architecture, or cloud-provider-specific deployment stack is planned.

## 18. Final v1.0.0 Hardening Roadmap

The active `upgrade/v0.13-security-hardening` branch is the final development workspace. It was created from the exact frozen v0.12.7 commit. The final release target is **BuildShield-CI v1.0.0 Final**.

The remaining program is:

1. **H1 - Workspace / filesystem trust boundary**
   Constrain caller-controlled scan and policy paths to approved roots, use canonical containment, prevent traversal/absolute/sibling-prefix/symlink escape, and harden report path validation.

2. **H2 - Authentication and API authorization**
   Add a focused single-tenant authentication/authorization layer suitable for the project scope and protect sensitive API operations.

3. **H3 - Frontend XSS elimination and browser security**
   Remove unsafe rendering of untrusted scanner-controlled values and add appropriate browser security headers/CSP.

4. **H4 - Request validation and resource controls**
   Bound request sizes, path/input values, OSV timeouts, history/report limits, and repeated expensive operations.

5. **H5 - Safe errors, auditability, and logging**
   Replace raw internal exception leakage with stable public errors, structured server-side logs, and useful request/run identifiers.

6. **H6 - Report/history security and retention**
   Strengthen report naming/containment, history access, retention/cleanup, and predictable storage behavior.

7. **H7 - Docker/runtime hardening**
   Preserve non-root execution and add practical no-new-privileges, capability, filesystem, and resource restrictions.

8. **H8 - Dependency and CI/CD hardening**
   Improve dependency reproducibility, refine GitHub Actions permissions, and add focused security/quality checks without tool bloat.

9. **H9 - Adversarial and regression test expansion**
   Add traversal, symlink, XSS, authentication, validation, report, resource-abuse, and safe-error tests while preserving the controlled benchmark.

10. **H10 - Final v1.0.0 freeze and repository audit**
    Perform dead-code/reference cleanup, remove obsolete residues only after confirming they are unused, synchronize every document/version, run full local/API/Docker/Compose/CI regression, merge through a green PR, verify post-merge `main`, and create the annotated `v1.0.0` tag.

No broad feature roadmap follows H10. After v1.0.0 is verified and tagged, planned feature development ends. Only an exceptional corrective patch for a critical security defect or release-breaking bug would justify modifying the final release.

## 19. Conclusion

BuildShield-CI demonstrates end-to-end cybersecurity engineering across supply-chain security, static analysis, DevSecOps policy enforcement, CI/CD hardening, vulnerability intelligence, reporting, dashboard development, persistence, testing, and containerization.

**v0.12.7 is the completed and frozen verified baseline.** The current hardening branch is the isolated workspace for the H1-H10 finalization program. The project should not be described as v1.0.0-complete until those hardening stages and the final acceptance gate pass.

The intended endpoint is a focused, clean, fully verified **BuildShield-CI v1.0.0 Final** release for controlled single-instance environments, with no planned feature upgrades after finalization.
