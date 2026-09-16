# BuildShield-CI Final Project Report

## 1. Executive Overview

BuildShield-CI is an advanced CI/CD supply-chain risk analyzer and dependency confusion defense platform. It performs passive static analysis of repository configuration and automation files, converts results into structured security findings, calculates risk, enforces policy-as-code, generates multiple report formats, integrates with GitHub Code Scanning, and provides dashboard/API visibility.

The project covers npm, Python dependencies, GitHub Actions, Dockerfiles, private-registry controls, SBOM-lite dependency inventory, OSV vulnerability intelligence, SQLite history, reproducible build controls, hardened Docker deployment and automated regression testing.

**BuildShield-CI v1.0.0 is released and verified.**

## 2. Problem Statement

Modern software delivery depends on package registries, third-party actions, build scripts, containers, secrets and automated pipelines. Misconfiguration can create risks such as dependency confusion, mutable dependency resolution, excessive workflow privileges, secret leakage, unsafe remote script execution and insecure container builds.

BuildShield-CI addresses these risks before deployment through static analysis, risk scoring and policy enforcement.

## 3. Objectives

The project objectives are to:

1. detect dependency confusion indicators;
2. detect insecure npm and Python dependency configuration;
3. detect GitHub Actions workflow risks;
4. detect Dockerfile hardening issues;
5. produce evidence-backed findings with remediation;
6. calculate security score, risk level and top drivers;
7. enforce YAML policy-as-code;
8. generate JSON, Markdown, HTML and SARIF reports;
9. integrate with GitHub Actions and Code Scanning;
10. build SBOM-lite dependency inventory;
11. add OSV vulnerability intelligence;
12. provide FastAPI/dashboard visibility;
13. persist history and risk trends with SQLite;
14. support hardened Docker and Docker Compose deployment;
15. validate behavior through automated tests, controlled fixtures and deterministic adversarial evaluation.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Release Python environment | Python 3.13 |
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
| Runtime SBOM | CycloneDX 1.6 |
| Deployment | Docker, Docker Compose |
| Testing | Pytest, Vitest |

## 5. System Architecture

```text
Repository
   |
   v
Security-Relevant File Discovery
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
   +--> Risk Scoring / Build Gate
   +--> Policy-as-Code
   +--> Reports / SARIF
   +--> SBOM-lite / OSV
   +--> FastAPI / React Dashboard
   `--> SQLite History / Trends
```

A maintenance refactor removed dynamic analyzer-name guessing and hidden fallback analyzers. Canonical analyzer functions are invoked explicitly and protected by regression tests.

## 6. Implemented Security Analysis

### npm

- missing lockfile
- loose/mutable versions
- risky lifecycle scripts
- potential dependency confusion
- missing trusted private-registry handling

### Python

- unpinned dependencies
- loose version ranges
- potential dependency confusion
- missing trusted package-index handling

### GitHub Actions

- mutable action refs
- excessive token permissions
- pipe-to-shell
- secret echo
- risky `pull_request_target`

### Dockerfile

- unpinned/latest base image
- missing non-root user
- explicit root user
- potential secret in `ENV`/`ARG`
- remote script execution
- `apt-get upgrade`
- missing/disabled health check
- remote URL used with `ADD`

## 7. Risk and Policy

The scoring engine produces:

- overall security score
- risk level
- category risk breakdown
- top risk drivers
- build-gate status/reason

The policy engine enforces controls such as:

- minimum score
- maximum severity counts
- required lockfiles
- pinned GitHub Actions
- secret handling
- pipe-to-shell restrictions
- dependency confusion controls
- `pull_request_target` restrictions

Risk scoring and policy evaluation are deliberately separate so a pipeline can reason about both posture and explicit policy.

## 8. Demonstration Results

### Vulnerable controlled sample

| Metric | Result |
|---|---:|
| Findings | 22 |
| Critical | 4 |
| High | 10 |
| Medium | 7 |
| Low | 1 |
| Security Score | 5/100 |
| Risk Level | CRITICAL |
| Build Gate | FAILED |
| Policy | FAILED |

### Hardened controlled sample

| Metric | Result |
|---|---:|
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

The realistic profile is the normal routine demo. It avoids representing a perfect score as the expected state of every production repository.

Natural comparison from the intentionally vulnerable benchmark to the realistic application:

- score: 5 -> 81
- findings: 22 -> 3
- score improvement: +76
- findings reduced: 19
- controlled risk reduction: 80%
- verdict: `PARTIALLY_IMPROVED`

Controlled vulnerable-to-hardened comparison:

- score improvement: +95
- findings reduced: 22
- controlled risk reduction: 100%
- verdict: `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED`

These figures are from checked-in controlled repository fixtures and are not universal security measurements for arbitrary systems.

## 9. Reporting and GitHub Integration

BuildShield-CI generates:

- JSON
- Markdown
- HTML
- SARIF 2.1.0
- comparison reports
- inventory output
- OSV intelligence output

SARIF is uploaded by GitHub Actions to GitHub Code Scanning. Alerts produced from `samples/vulnerable-repo` are intentionally generated demonstration findings.

## 10. SBOM-lite, CycloneDX and OSV Intelligence

The dependency inventory extracts package metadata from supported npm and Python inputs.

The project also maintains a reproducible CycloneDX 1.6 runtime SBOM for the BuildShield-CI release environment. Hosted CI regenerates the SBOM repeatedly and verifies both deterministic equality and equality with the checked-in SBOM.

The OSV integration can create an offline query plan or perform online lookups for pinned dependencies. OSV results are dynamic; deterministic project claims do not hard-code an external vulnerability count.

## 11. API, Dashboard and History

The FastAPI backend and React/TypeScript dashboard provide:

- authentication/session workflow
- overview
- scan execution
- findings exploration
- policy result visibility
- comparison
- reports
- SBOM-lite inventory
- OSV intelligence
- scan history
- risk-trend data

SQLite stores local history/trend information.

## 12. Security Hardening

The H1-H10 program delivered:

- workspace-root containment and path/symlink escape prevention
- single-tenant authentication and API authorization
- browser-facing security hardening
- request/body/resource/concurrency controls
- safe public errors
- structured logging and request correlation
- audit records
- report/history security and retention
- deterministic SQLite connection lifecycle handling
- non-root/read-only container runtime
- drop-all capabilities and `no-new-privileges`
- fail-closed production configuration
- liveness/readiness separation
- reproducible dependency/build controls
- immutable GitHub Actions pins
- deterministic adversarial evaluation

## 13. CI/CD Self-Hardening

BuildShield-CI's workflow uses immutable full commit SHAs for third-party GitHub Actions.

The CI system verifies:

- hash-locked Python dependencies
- `pip check`
- Ruff
- mypy typed-boundary checks
- pytest with branch coverage
- preserved coverage baseline
- wheel/sdist build
- fresh non-editable wheel installation
- CycloneDX regeneration
- exact Node 22.23.2 / npm 12.0.2
- frontend dependency tree
- ESLint
- TypeScript
- Vitest
- npm audit
- Vite production build
- controlled security gates
- SARIF/report artifacts

A regression test prevents accidental reintroduction of mutable Action refs such as `@main` or version tags.

## 14. Deployment

BuildShield-CI supports local execution, Docker and Docker Compose.

Production-style container controls include:

- multi-stage build
- non-root UID/GID `10001:10001`
- read-only root filesystem in Compose
- dropped Linux capabilities
- `no-new-privileges`
- PID limit
- restricted tmpfs
- localhost-only port publication
- persistent report/data volumes
- `/health` liveness
- `/ready` readiness
- fail-closed administrator authentication configuration
- graceful stop/restart validation

The project is suitable for controlled single-instance deployment and production-style demonstrations. Enterprise production deployment would require additional organization-specific identity/RBAC, isolation, secret-management, TLS/network, observability, backup/recovery and governance controls.

## 15. Testing and Reliability

Final pre-release Windows Python regression:

```text
295 passed, 2 skipped
```

The accepted release state also passed:

- realistic dashboard/API contract
- realistic 81/100 profile contract
- natural 5 -> 81 comparison
- exact controlled 22 -> 0 benchmark
- Ruff
- mypy
- `pip check`
- exact frontend reproducibility/quality gates
- production Docker/API smoke
- authenticated live-browser review
- final repository sanitation
- hosted CI on the final checkpoint
- pull-request CI
- post-merge `main` CI

H9 adds a fixed 100-case deterministic adversarial corpus across 20 static rules.

Pre-hardening baseline:

```text
41 TP / 45 TN / 4 FP / 10 FN
micro F1 0.854167
```

After bounded H9D hardening on the unchanged corpus:

```text
51 TP / 49 TN / 0 FP / 0 FN
precision / recall / F1 1.000000
```

These corpus metrics are regression evidence only and are not real-world accuracy estimates.

## 16. Repository Hygiene

Repository controls include:

- deterministic line-ending rules with `.gitattributes`
- `.gitignore` for caches, environments, generated runtime/build output, secret-like local files, logs and editor/OS artifacts
- reduced Docker build context through `.dockerignore`
- explicit dev dependencies
- generated reports and SQLite runtime data excluded from source control
- release-hygiene regression tests

Final sanitation verified:

- zero tracked generated trash
- zero tracked secret-like filenames
- no tracked files at or above 5 MiB
- `git diff --check`: PASS
- `git fsck`: PASS
- zero merge-conflict markers

## 17. Ethical and Safety Scope

BuildShield-CI is defensive and passive.

It does not:

- exploit systems
- publish malicious packages
- execute malware
- exfiltrate credentials
- attack package registries
- scan unauthorized systems
- perform destructive actions

All intentionally vulnerable content is confined to controlled fixtures.

## 18. Final Scope Boundaries

The v1.0.0 scope intentionally remains focused.

Not included:

- Maven, Go, NuGet, Rust or additional package-ecosystem analyzers
- Kubernetes manifest analysis
- GitLab CI or Jenkins analyzers
- AI/LLM remediation assistants
- multi-tenant SaaS architecture
- distributed worker infrastructure
- cloud-provider-specific production deployment stacks

Dependency-confusion detection remains a static heuristic control rather than an active registry attack.

## 19. Release Closure

H1-H10 local engineering and release acceptance are complete.

Final pre-release checkpoint:

```text
f397d257638f3e3bd50eaaa6b9966442e158a849
```

Verified release/merge commit:

```text
dec7eea405cd474fdea73bacd8f9847782887816
```

The accepted release sequence completed:

1. final replacement checkpoint created;
2. hosted CI passed on that exact state;
3. final pull request was reviewed and merged;
4. post-merge `main` CI passed;
5. annotated tag `v1.0.0` was created;
6. GitHub release **BuildShield-CI v1.0.0** was published.

The v1.0.0 tag is frozen release history and must not be moved for later documentation cleanup.

## 20. Conclusion

BuildShield-CI demonstrates end-to-end cybersecurity engineering across supply-chain security, static analysis, DevSecOps policy enforcement, CI/CD hardening, vulnerability intelligence, reporting, React/FastAPI application development, persistence, reproducible builds, testing and container hardening.

**v0.12.7 remains the historical frozen baseline. v1.0.0 is the current verified release.** Future behavior-changing corrections should be made through a new versioned release instead of rewriting v1.0.0 history.
