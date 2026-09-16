# BuildShield-CI

**Advanced CI/CD Supply Chain Risk Analyzer and Dependency Confusion Defense Platform**

BuildShield-CI is a DevSecOps security platform that performs passive static analysis of repositories before deployment. It analyzes npm and Python dependency configuration, private registry controls, GitHub Actions workflows, Dockerfiles, policy rules, and known package vulnerabilities.

The project includes a CLI scanner, FastAPI backend, web dashboard, policy-as-code gate, SARIF/GitHub Code Scanning integration, SBOM-lite inventory, OSV vulnerability intelligence, SQLite scan history, Docker deployment support, and automated tests.

---

## Current Verified Baseline

Historical frozen release baseline: **v0.12.7**.
Current H10 release candidate package version: **1.0.0** (not yet the final tagged release).

| Metric | Vulnerable Sample | Hardened Sample |
|---|---:|---:|
| Findings | 22 | 0 |
| Critical | 4 | 0 |
| High | 10 | 0 |
| Medium | 7 | 0 |
| Low | 1 | 0 |
| Security Score | 5/100 | 100/100 |
| Risk Level | CRITICAL | LOW |
| Build Gate | FAILED | PASSED |
| Policy | FAILED | PASSED |

Representative realistic application profile:

- Repository: `samples/realistic-repo`
- Findings: **3** (0 Critical, 0 High, 2 Medium, 1 Low)
- Security score: **81/100**
- Risk level: **MEDIUM**
- Build gate: **WARNING**
- Policy: **PASSED**

Natural comparison (`samples/vulnerable-repo` -> `samples/realistic-repo`):

- Score improvement: **+76**
- Findings reduced: **19**
- Risk reduction: **80%**
- Verdict: `PARTIALLY_IMPROVED`

Controlled benchmark comparison result:

- Score improvement: **+95**
- Findings reduced: **22**
- Risk reduction: **100%**
- Verdict: `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED`
- Latest full Windows pre-release regression: **295 passed, 2 skipped**

The vulnerable sample is intentionally insecure. Findings uploaded to GitHub Code Scanning from that sample are demonstration findings, not evidence that the BuildShield-CI source code itself contains those vulnerabilities.

The active `upgrade/v0.13-security-hardening` branch has completed H1-H10 local release engineering. Checkpoint `7bc58e905789fe2990223d3cf520729c14d98e1f` was pushed and accepted by hosted CI before the final professional-UI and realistic-demo pass. The current post-checkpoint candidate has since passed the realistic-profile contract, production Docker smoke, full Windows regression at **295 passed, 2 skipped**, live browser review, and final repository sanitation. A replacement final checkpoint and hosted-CI pass are still required before PR merge, tag, and GitHub release.

---

## Project Highlights

- Dependency confusion detection for npm and Python projects
- npm and Python dependency pinning analysis
- Private registry / package index configuration checks
- GitHub Actions workflow security analysis
- Dockerfile security analysis
- YAML policy-as-code enforcement
- Risk scoring, category risk, top risk drivers, and build-gate decision
- JSON, Markdown, HTML, and SARIF reporting
- GitHub Code Scanning integration
- SBOM-lite dependency inventory
- OSV vulnerability intelligence
- FastAPI API and web dashboard
- SQLite scan history and trend data
- Docker and Docker Compose deployment
- SHA-pinned GitHub Actions workflow
- Automated regression tests
- Deterministic 100-case adversarial evaluation corpus across 20 static rules

---

## Security Rules

### npm

- `DG-NPM-001` — Missing npm lockfile
- `DG-NPM-002` — Loose npm dependency version
- `DG-NPM-003` — Risky npm lifecycle script
- `DG-NPM-004` — Potential npm dependency confusion risk

### Python

- `DG-PY-001` — Unpinned Python dependency
- `DG-PY-002` — Loose Python dependency version
- `DG-PY-003` — Potential Python dependency confusion risk

### GitHub Actions

- `DG-GHA-001` — GitHub Action not pinned to full commit SHA
- `DG-GHA-002` — Over-permissive token permissions
- `DG-GHA-003` — Remote script piped directly to shell
- `DG-GHA-004` — Secret value printed in workflow
- `DG-GHA-005` — Risky `pull_request_target` usage

### Dockerfile

- `DG-DOCKER-001` — Unpinned/latest base image
- `DG-DOCKER-002` — Missing non-root `USER`
- `DG-DOCKER-003` — Explicit root `USER`
- `DG-DOCKER-004` — Potential secret in `ENV` or `ARG`
- `DG-DOCKER-005` — Remote script piped directly to shell
- `DG-DOCKER-006` — `apt-get upgrade` during image build
- `DG-DOCKER-007` — Missing or disabled `HEALTHCHECK`
- `DG-DOCKER-008` — Remote URL used with `ADD`

---

## Architecture

```text
Repository
   |
   v
Security-Relevant File Discovery
   |
   v
Explicit Analyzer Orchestration
   |-- npm
   |-- Python
   |-- GitHub Actions
   `-- Dockerfile
   |
   v
Normalized Findings
   |
   +--> Risk Scoring
   |      |-- Overall score
   |      |-- Risk level
   |      |-- Category breakdown
   |      |-- Top drivers
   |      `-- Build gate
   |
   +--> Policy-as-Code
   |
   +--> Reporting
   |      |-- JSON
   |      |-- Markdown
   |      |-- HTML
   |      `-- SARIF
   |
   +--> Intelligence
   |      |-- SBOM-lite inventory
   |      `-- OSV lookup
   |
   +--> FastAPI + Dashboard
   |      `-- SQLite history / trends
   |
   `--> CI/CD + Docker
```

The scanner calls the canonical analyzer interfaces directly. Legacy dynamic function-name guessing and hidden npm/GitHub Actions fallback analyzers were removed during the v0.12.7 maintenance cleanup.

---

## Technology Stack

| Area | Technology |
|---|---|
| Language | Python 3.13 |
| CLI | Typer |
| Terminal UI | Rich |
| Backend | FastAPI |
| Data Models | Pydantic |
| Storage | SQLite |
| Frontend | React 19, TypeScript 7, Vite 8 |
| Reports | JSON, Markdown, HTML, SARIF |
| CI/CD | GitHub Actions |
| Vulnerability Intelligence | OSV |
| Deployment | Docker, Docker Compose |
| Testing | Pytest |

---

## Installation

```powershell
git clone https://github.com/rootmass56/buildshield-ci.git
cd buildshield-ci

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
buildshield version
```

Current H10 release candidate:

```text
BuildShield-CI version: 1.0.0
```

The `v0.12.7` annotated tag remains the historical frozen baseline. The current package is the validated `1.0.0` release candidate. H1-H10 local acceptance, professional UI polish, the realistic application profile, live browser review, and repository sanitation are complete. The final replacement checkpoint/hosted-CI, PR merge, annotated `v1.0.0` tag, and release verification remain pending.

---

## Core CLI Usage

Realistic application sample:

```powershell
buildshield scan samples/realistic-repo --policy buildshield-policy.yml --hide-files
```

Vulnerable benchmark sample:

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --hide-files
```

Hardened sample:

```powershell
buildshield scan samples/secure-repo --policy buildshield-policy.yml --hide-files
```

Comparison:

```powershell
buildshield compare samples/vulnerable-repo samples/secure-repo
```

Inventory:

```powershell
buildshield inventory samples/vulnerable-repo --hide-packages
```

OSV offline query plan:

```powershell
buildshield vulncheck samples/secure-repo --offline-plan
```

OSV online lookup:

```powershell
buildshield vulncheck samples/secure-repo --online --timeout 15
```

---

## Reports

```powershell
buildshield scan samples/vulnerable-repo --report-format json --output reports/vulnerable-scan.json
buildshield scan samples/vulnerable-repo --report-format md --output reports/vulnerable-scan.md
buildshield scan samples/vulnerable-repo --report-format html --output reports/vulnerable-scan.html
buildshield scan samples/vulnerable-repo --report-format sarif --output reports/buildshield-results.sarif
```

---

## Dashboard

```powershell
buildshield dashboard --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

Dashboard capabilities include repository scanning, findings, policy evaluation, comparison, SBOM-lite inventory, vulnerability intelligence, reports, history, and risk trends.

---

## GitHub Actions and Code Scanning

Workflow:

```text
.github/workflows/buildshield-ci.yml
```

The workflow:

- Installs BuildShield-CI
- Runs the pytest suite
- Runs the secure policy gate
- Demonstrates expected vulnerable-sample policy failure
- Generates reports
- Generates SARIF
- Uploads SARIF to GitHub Code Scanning
- Uploads report artifacts

External GitHub Actions are pinned to immutable full commit SHAs. A regression test enforces this policy.

---

## Docker

Build:

```powershell
docker build -t buildshield-ci:latest .
```

Run:

```powershell
docker run -d --name buildshield-ci-test -p 8080:8080 buildshield-ci:latest
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

Compose:

```powershell
docker compose up --build -d
docker compose ps
docker compose down
```

The container runs as a non-root user and uses health checks. Docker Compose provides persistent volumes for reports and application data.

---

## Testing

```powershell
pytest -q
```

Current verified Windows release-candidate result:

```text
295 passed, 2 skipped
```

Coverage includes scanner orchestration, npm/Python/GitHub Actions/Dockerfile analyzers, policy, reporting, comparison, authentication/authorization, path containment, browser security, request/resource controls, safe errors/logging, report/history security and retention, dashboard APIs, SBOM-lite inventory, OSV intelligence, Docker/runtime hardening, reproducible builds, immutable workflow references, deterministic H9 evaluation, and repository hygiene.

---

## Ethical Scope

BuildShield-CI is a defensive static-analysis project. It does not exploit systems, publish malicious packages, execute malware, steal credentials, or scan unauthorized targets.

The vulnerable repository under `samples/vulnerable-repo` is intentionally insecure and exists only for controlled demonstration and regression testing.

---

## Deployment Positioning

The validated v1.0.0 release candidate is deployment-ready for controlled single-instance environments and demonstrates a production-style architecture. It includes the in-scope workspace boundary, single-tenant authentication/authorization, browser security, resource controls, safe errors/audit logging, retention controls, hardened Docker runtime, reproducible build/CI gates, and adversarial regression evaluation. It is not claimed to be an enterprise multi-tenant service.

H1-H10 local acceptance is complete. The post-checkpoint professional UI and realistic-demo candidate has passed frontend quality gates, production Docker/API smoke, a full Windows regression of **295 passed, 2 skipped**, live browser review, and final repository sanitation. Only the final replacement checkpoint/hosted-CI, PR merge, annotated `v1.0.0` tag, and GitHub release verification remain.

---

## Documentation

See `docs/` for architecture, deployment, demo, report, project summary, research log, interview preparation, screenshots, and submission verification guidance.
