# BuildShield-CI

**Advanced CI/CD Supply Chain Risk Analyzer and Dependency Confusion Defense Platform**

BuildShield-CI is a DevSecOps security platform that performs passive static analysis of repositories before deployment. It analyzes npm and Python dependency configuration, private registry controls, GitHub Actions workflows, Dockerfiles, policy rules, and known package vulnerabilities.

The project includes a CLI scanner, FastAPI backend, web dashboard, policy-as-code gate, SARIF/GitHub Code Scanning integration, SBOM-lite inventory, OSV vulnerability intelligence, SQLite scan history, Docker deployment support, and automated tests.

---

## Current Verified Baseline

Frozen verified release baseline: **v0.12.7**.

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

Comparison result:

- Score improvement: **+95**
- Findings reduced: **22**
- Risk reduction: **100%**
- Verdict: `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED`
- Automated tests: **57 passing**

The vulnerable sample is intentionally insecure. Findings uploaded to GitHub Code Scanning from that sample are demonstration findings, not evidence that the BuildShield-CI source code itself contains those vulnerabilities.

The active `upgrade/v0.13-security-hardening` branch is the isolated workspace for the H1-H10 final hardening program targeting **BuildShield-CI v1.0.0 Final**. The v0.12.7 release remains the frozen functional baseline.

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
- `DG-DOCKER-004` — Potential secret in `ENV` or `ARG`
- `DG-DOCKER-005` — Remote script piped directly to shell
- `DG-DOCKER-006` — `apt-get upgrade` during image build
- `DG-DOCKER-007` — Missing `HEALTHCHECK`

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
| Frontend | HTML, CSS, JavaScript |
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

Current frozen release baseline:

```text
BuildShield-CI version: 0.12.7
```

The `v0.12.7` annotated tag, merged `main` baseline, and associated CI verification are complete. Final web/API hardening is being developed separately on `upgrade/v0.13-security-hardening` toward v1.0.0.

---

## Core CLI Usage

Vulnerable sample:

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

Current verified result:

```text
57 passed
```

Coverage includes scanner orchestration, npm/Python/GitHub Actions/Dockerfile analyzers, policy, reporting, comparison, dashboard APIs, history, SBOM-lite inventory, OSV intelligence, deployment files, immutable workflow references, and repository hygiene.

---

## Ethical Scope

BuildShield-CI is a defensive static-analysis project. It does not exploit systems, publish malicious packages, execute malware, steal credentials, or scan unauthorized targets.

The vulnerable repository under `samples/vulnerable-repo` is intentionally insecure and exists only for controlled demonstration and regression testing.

---

## Deployment Positioning

BuildShield-CI v0.12.7 is deployment-ready for controlled environments and demonstrates a production-style architecture. It is not claimed to be a fully hardened enterprise or multi-tenant service.

The final H1-H10 hardening program addresses the remaining in-scope web/API security boundaries, including workspace containment, authentication/authorization, browser security, request/resource controls, safe errors/logging, report/history security, Docker/runtime hardening, CI/dependency hardening, adversarial tests, and final repository cleanup.

---

## Documentation

See `docs/` for architecture, deployment, demo, report, project summary, research log, interview preparation, screenshots, and submission verification guidance.
