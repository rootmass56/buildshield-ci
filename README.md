# BuildShield-CI

**Advanced CI/CD Supply-Chain Risk Analyzer and Dependency Confusion Defense Platform**

BuildShield-CI is a defensive DevSecOps security platform that performs passive static analysis of repositories before deployment. It analyzes npm and Python dependency configuration, private-registry controls, GitHub Actions workflows and Dockerfiles, then combines normalized findings with risk scoring, policy-as-code, reporting, GitHub Code Scanning, dependency inventory, OSV vulnerability intelligence, API/dashboard workflows, scan history and hardened container deployment.

## Release Status

**Current released version: `v1.0.0`**

- Release commit: `dec7eea405cd474fdea73bacd8f9847782887816`
- Final pre-release checkpoint: `f397d257638f3e3bd50eaaa6b9966442e158a849`
- Historical frozen baseline: `v0.12.7`
- Final Windows regression before release: **295 passed, 2 skipped**
- Push, pull-request and post-merge `main` GitHub Actions: **PASS**
- Production Docker/API smoke, authenticated live-browser review and final repository sanitation: **PASS**

The `v1.0.0` tag and GitHub release are published. The tag remains the immutable release reference. Later post-release maintenance on `main` may improve documentation, packaging, reproducibility, or other non-release-maintenance concerns without rewriting the published `v1.0.0` tag.

## Project Highlights

- 20 static `DG-*` security rules across npm, Python, GitHub Actions and Dockerfiles
- Dependency-confusion and private-registry/package-index configuration heuristics
- Dependency pinning and risky lifecycle/build-pattern checks
- Risk scoring, category risk, top drivers and build-gate decisions
- YAML policy-as-code enforcement
- JSON, Markdown, HTML and SARIF reporting
- GitHub Code Scanning integration
- SBOM-lite dependency inventory and reproducible CycloneDX 1.6 runtime SBOM
- OSV offline planning and online vulnerability intelligence
- FastAPI backend and professional React/TypeScript dashboard
- SQLite scan history and risk trends
- Single-tenant authentication/authorization, audit logging and resource controls
- Hardened Docker / Docker Compose deployment
- Hash-locked Python dependencies and reproducible frontend quality gates
- SHA-pinned GitHub Actions with least-privilege workflow permissions
- Deterministic 100-case adversarial evaluation corpus across all 20 rules

## Verified Security Profiles

### Representative realistic application

The normal demo defaults to `samples/realistic-repo`, which intentionally represents a mixed posture instead of an artificial perfect score.

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

Natural vulnerable-to-realistic comparison:

- Score: **5 -> 81**
- Findings: **22 -> 3**
- Score delta: **+76**
- Findings reduced: **19**
- Controlled risk reduction: **80%**
- Verdict: `PARTIALLY_IMPROVED`

### Controlled vulnerable-to-hardened benchmark

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

Controlled comparison result:

- Score improvement: **+95**
- Findings reduced: **22**
- Controlled risk reduction: **100%**
- Verdict: `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED`

These figures describe checked-in controlled fixtures. They are not a universal security guarantee, and the 100/100 hardened fixture is a regression endpoint rather than an expected score for every healthy repository.

## Static Security Rules

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

## Architecture

```text
Repository
   |
   v
Security-Relevant File Discovery
   |
   v
Canonical Analyzer Layer
   |-- npm
   |-- Python
   |-- GitHub Actions
   `-- Dockerfile
   |
   v
Normalized Findings
   |
   +--> Risk Scoring + Build Gate
   +--> Policy-as-Code
   +--> JSON / Markdown / HTML / SARIF
   +--> SBOM-lite Inventory / OSV
   +--> FastAPI + React Dashboard
   +--> SQLite History / Trends
   `--> GitHub Actions + Hardened Docker
```

The scanner calls canonical analyzer interfaces directly. Legacy dynamic analyzer-name guessing and hidden fallback analyzers were removed during the maintenance/hardening program.

## Technology Stack

| Area | Technology |
|---|---|
| Language | Python 3.13 release environment; project metadata supports Python 3.11+ |
| CLI | Typer, Rich |
| Backend | FastAPI, Pydantic |
| Storage | SQLite |
| Frontend | React 19, TypeScript 7, Vite 8 |
| CI/CD | GitHub Actions |
| Reports | JSON, Markdown, HTML, SARIF |
| Vulnerability Intelligence | OSV |
| SBOM | CycloneDX 1.6 |
| Deployment | Docker, Docker Compose |
| Testing | Pytest, Vitest |

## Installation

```powershell
git clone https://github.com/rootmass56/buildshield-ci.git
cd buildshield-ci

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
buildshield version
```

Expected version:

```text
BuildShield-CI version: 1.0.0
```

## Core CLI Usage

Realistic application:

```powershell
buildshield scan samples/realistic-repo --policy buildshield-policy.yml --hide-files
```

Controlled vulnerable benchmark:

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --hide-files
```

Controlled hardened benchmark:

```powershell
buildshield scan samples/secure-repo --policy buildshield-policy.yml --hide-files
```

Natural comparison:

```powershell
buildshield compare samples/vulnerable-repo samples/realistic-repo
```

Controlled benchmark comparison:

```powershell
buildshield compare samples/vulnerable-repo samples/secure-repo
```

Inventory:

```powershell
buildshield inventory samples/realistic-repo --hide-packages
```

OSV offline plan:

```powershell
buildshield vulncheck samples/realistic-repo --offline-plan
```

OSV online lookup:

```powershell
buildshield vulncheck samples/realistic-repo --online --timeout 15
```

## Reports

```powershell
buildshield scan samples/realistic-repo --report-format json --output reports/realistic-scan.json
buildshield scan samples/realistic-repo --report-format md --output reports/realistic-scan.md
buildshield scan samples/realistic-repo --report-format html --output reports/realistic-scan.html
buildshield scan samples/realistic-repo --report-format sarif --output reports/buildshield-results.sarif
```

## Dashboard

For a source-checkout local development/demo, build the production frontend assets before starting the FastAPI dashboard server:

```powershell
cd frontend
npm ci
npm run build
cd ..

buildshield dashboard --port 8080
```

Open `http://127.0.0.1:8080`.

If port `8080` is already in use, choose another local port, for example:

```powershell
buildshield dashboard --port 18081
```

Then open `http://127.0.0.1:18081`.

The canonical validated frontend toolchain is Node `22.23.2` with npm `12.0.2`; CI and the production Docker build enforce those versions. The dashboard provides authentication, overview, repository scanning, findings, policy evaluation, comparison, SBOM-lite inventory, vulnerability intelligence, reports, history and trends.

### External repository workspace

Dashboard repository operations are contained within the configured workspace root. By default, the workspace root is the directory from which the dashboard process starts. To analyze repositories stored in a separate controlled directory, set `BUILDSHIELD_WORKSPACE_ROOT` before starting the dashboard:

```powershell
$env:BUILDSHIELD_WORKSPACE_ROOT = "D:\Security-Lab"
buildshield dashboard --port 18081
```

If that workspace contains two repository states such as:

```text
D:\Security-Lab\repository-before
D:\Security-Lab\repository-after
```

enter the workspace-relative paths `repository-before` and `repository-after` in Scanner, Inventory, OSV Intelligence, or Compare as appropriate. Sample repositories remain available as suggestions when they exist inside the configured workspace. Resolved dashboard paths must remain inside `BUILDSHIELD_WORKSPACE_ROOT`; paths outside that boundary are rejected.

The dashboard does not clone or upload arbitrary repositories. Place repositories under the approved workspace root first. CLI commands are separate from this dashboard containment workflow and may be given direct filesystem repository paths.

## Production-Style Docker Compose

Production mode fails closed unless administrator authentication is configured. Generate an ephemeral password hash locally; never commit it.

```powershell
$env:BUILDSHIELD_ADMIN_USERNAME = "admin"
$env:BUILDSHIELD_ADMIN_PASSWORD_HASH = python -c "from supplysentinel.web.auth import hash_password; import getpass; print(hash_password(getpass.getpass('Admin password: ')))"
$env:BUILDSHIELD_COOKIE_SECURE = "false"
$env:BUILDSHIELD_HOST_PORT = "18080"

docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:18080/health
Invoke-RestMethod http://127.0.0.1:18080/ready
docker compose down
```

The production container uses a numeric non-root identity, read-only root filesystem, dropped Linux capabilities, `no-new-privileges`, bounded PID/tmpfs controls, localhost-only publication, persistent report/data volumes and separate liveness/readiness checks.

## CI/CD and Supply-Chain Controls

`.github/workflows/buildshield-ci.yml` enforces:

- hash-locked Linux CI dependencies
- `pip check`
- Ruff
- mypy typed-boundary checks
- pytest with branch coverage
- preserved coverage baseline
- wheel/sdist build
- fresh non-editable wheel installation
- reproducible CycloneDX 1.6 SBOM verification
- exact Node 22.23.2 / npm 12.0.2 frontend gates
- ESLint, TypeScript, Vitest, npm audit and production build
- controlled security-gate assertions
- SARIF upload to GitHub Code Scanning
- immutable full-SHA third-party Action references
- least-privilege job permissions

## Deterministic Evaluation Boundary

H9 uses a fixed 100-case deterministic corpus covering all 20 static rules.

Before detector hardening:

```text
41 TP / 45 TN / 4 FP / 10 FN
micro F1: 0.854167
```

After bounded hardening on the same unchanged corpus:

```text
51 TP / 49 TN / 0 FP / 0 FN
precision / recall / F1: 1.000000
```

The 1.000000 result is regression performance on that fixed curated corpus only. It is **not** a claim of 100% real-world security-detection accuracy.

## Testing

```powershell
pytest -q
```

Verified pre-release Windows regression:

```text
295 passed, 2 skipped
```

The released state also passed frontend quality gates, reproducibility checks, Docker/runtime validation, authentication/session smoke testing, controlled benchmark checks and repository sanitation.

## Security and Deployment Positioning

BuildShield-CI is defensive and passive. It does not exploit systems, publish malicious packages, steal credentials, attack registries, or authorize testing of third-party targets.

The released v1.0.0 architecture is intended for controlled single-instance deployment and production-style demonstrations. It is not claimed as enterprise multi-tenant SaaS. Organization-wide production use would require environment-specific identity/RBAC, tenant isolation where applicable, centralized secret management, TLS/network controls, shared observability, backup/recovery and operational governance.

See `SECURITY.md` for vulnerability-reporting guidance and security limitations.

## Documentation

Key project documentation includes:

- `docs/architecture.md`
- `docs/deployment.md`
- `docs/final-blueprint.md`
- `docs/final-project-summary.md`
- `docs/final-report.md`
- `docs/demo-script.md`
- `docs/interview-explanation.md`
- `docs/screenshots-checklist.md`
- `docs/final-submission-checklist.md`
- `CHANGELOG.md` — release history

Historical H9/H10 stage documents are intentionally retained as engineering evidence. Current release status is defined by this README, the final blueprint, the `v1.0.0` tag and the published GitHub release.

## License

BuildShield-CI is licensed under the Apache License 2.0. See [`LICENSE`](LICENSE) for the full license text.
