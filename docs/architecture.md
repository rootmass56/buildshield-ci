# BuildShield-CI Architecture

## 1. Overview

BuildShield-CI is a modular DevSecOps security platform for passive CI/CD supply-chain analysis. It discovers security-relevant repository files, dispatches them to explicit analyzer interfaces, normalizes findings, calculates risk, evaluates policy, produces reports, exposes dashboard/API functionality, and integrates with CI/CD and container deployment.

## 2. High-Level Flow

```text
Repository
   |
   v
File Discovery
   |
   v
Canonical Analyzer Layer
   |-- npm Analyzer
   |-- Python Analyzer
   |-- GitHub Actions Analyzer
   `-- Dockerfile Analyzer
   |
   v
Finding Model
   |
   +--> Risk Scoring Engine
   +--> Policy-as-Code Engine
   +--> Reporters
   +--> SARIF / GitHub Code Scanning
   +--> SBOM-lite Inventory
   +--> OSV Vulnerability Intelligence
   +--> FastAPI / Dashboard
   `--> SQLite History / Trends
```

## 3. Scanner Core

Primary location:

```text
src/supplysentinel/core/scanner.py
```

Responsibilities:

- Validate target repository path
- Discover security-relevant files
- Classify files by type
- Dispatch files to analyzers
- Deduplicate normalized findings
- Build scan summary
- Invoke the scoring engine

The maintenance refactor removed dynamic analyzer-name guessing and hidden npm/GitHub Actions fallback implementations. The scanner now invokes the canonical analyzer functions directly.

## 4. File Discovery

Relevant inputs include:

- `package.json`
- npm lockfiles
- `.npmrc`
- `requirements*.txt`
- `pip.conf`
- `pip.ini`
- `.pypirc`
- `.github/workflows/*.yml`
- `.github/workflows/*.yaml`
- `Dockerfile`
- `*.dockerfile`

Ignored development/runtime folders include `.git`, virtual environments, caches, `node_modules`, build output, and similar non-source directories.

## 5. Analyzer Layer

Location:

```text
src/supplysentinel/analyzers/
```

| Analyzer | Primary responsibility |
|---|---|
| npm | Lockfiles, mutable versions, lifecycle scripts, dependency confusion / registry controls |
| Python | Pinning, loose versions, dependency confusion / package index controls |
| GitHub Actions | Action pinning, token permissions, secret echo, pipe-to-shell, `pull_request_target` |
| Dockerfile | Base image pinning, user hardening, secrets, remote shell execution, upgrade behavior, health checks |

## 6. Detection Rules

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

- `DG-GHA-001` — Action not pinned to full commit SHA
- `DG-GHA-002` — Over-permissive token permissions
- `DG-GHA-003` — Remote script piped directly to shell
- `DG-GHA-004` — Secret printed in workflow
- `DG-GHA-005` — Risky `pull_request_target`

### Dockerfile

Current controlled benchmark exercises:

- `DG-DOCKER-001`
- `DG-DOCKER-002`
- `DG-DOCKER-004`
- `DG-DOCKER-005`
- `DG-DOCKER-006`
- `DG-DOCKER-007`

## 7. Finding Model

Findings carry structured fields including:

- Rule ID
- Title
- Severity
- Category
- Confidence
- Description
- Impact
- Evidence
- File path
- Line number
- Snippet
- Remediation
- Reference

This normalized model allows all analyzers to feed the same scoring, policy, report, SARIF, API, and dashboard layers.

## 8. Risk Scoring

Location:

```text
src/supplysentinel/core/scoring.py
```

Outputs include:

- Overall security score
- Overall risk level
- Category-wise risk
- Penalty contribution
- Top risk drivers
- Build gate status
- Build gate reason

Controlled benchmark:

```text
Vulnerable sample
22 findings
4 Critical / 10 High / 7 Medium / 1 Low
5/100
CRITICAL
FAILED

Hardened sample
0 findings
100/100
LOW
PASSED
```

## 9. Policy-as-Code

Policy file:

```text
buildshield-policy.yml
```

Controls include:

- Minimum score
- Severity thresholds
- Lockfile requirement
- Pinned GitHub Actions
- Secret-echo prevention
- Pipe-to-shell prevention
- Dependency confusion prevention
- `pull_request_target` control

Policy evaluation is independent from the risk score: both are reported so CI/CD can reason about posture and enforcement.

## 10. Reporting

Supported output includes:

- Terminal
- JSON
- Markdown
- HTML
- SARIF 2.1.0
- Comparison reports
- Dependency inventory output
- OSV intelligence output

SARIF is consumed by GitHub Code Scanning through the project workflow.

## 11. Intelligence Layer

### SBOM-lite

BuildShield-CI extracts dependency inventory information from supported npm and Python files, including package name, ecosystem, version/pinning state, and security-relevant metadata.

### OSV

The OSV integration supports:

- Offline query-plan generation
- Online vulnerability lookup
- OSV/GHSA identifiers
- Vulnerability reporting

The number of known vulnerabilities is dynamic and must not be hard-coded into documentation.

## 12. API, Dashboard, and Persistence

BuildShield-CI includes a FastAPI backend and browser dashboard for:

- Scanning
- Comparison
- Findings
- Policy results
- Reports
- Dependency inventory
- Vulnerability intelligence
- Scan history
- Risk trends

SQLite is used for local history and trend persistence.

## 13. CI/CD Architecture

Workflow:

```text
.github/workflows/buildshield-ci.yml
```

The workflow installs the project, runs tests, validates the hardened sample, demonstrates controlled vulnerable-sample failure, generates reports, uploads SARIF, and uploads artifacts.

All third-party GitHub Actions in the workflow are pinned to reviewed full commit SHAs. `tests/test_workflow_security.py` guards against regression to mutable tags or branches.

## 14. Deployment Layer

BuildShield-CI supports:

- Local CLI/API/dashboard execution
- Docker image build
- Non-root container execution
- Health endpoint
- Docker Compose
- Persistent report/data volumes

This is suitable for controlled deployment demonstrations. Enterprise production use would require additional authentication, authorization, isolation, secret management, rate limiting, observability, network controls, and operational governance.

## 15. Repository Hygiene

The maintenance baseline includes:

- `.gitignore` for runtime, build, cache, secret, and local artifacts
- `.dockerignore` to reduce Docker build context
- `.gitattributes` for deterministic line endings
- Explicit development dependencies
- No global pytest warning suppression
- Repository metadata URLs

## 16. Testing

Current verified result:

```text
57 passed
```

Coverage includes analyzer routing, analyzer behavior, benchmark preservation, policy, reports, comparison, CLI, dashboard APIs, scan history, OSV, inventory, deployment files, workflow SHA pinning, and repository hygiene.

## 17. Limitations and Next Expansion Areas

Current limitations include:

- Static analysis focus
- Limited ecosystem coverage
- Heuristic dependency-confusion detection
- No enterprise identity/access-control layer
- No multi-tenant isolation
- No production-grade distributed job system
- No Kubernetes or GitLab CI analyzer yet

Possible future expansion:

- Additional ecosystems such as Maven, Go, and NuGet
- Kubernetes manifest analysis
- GitLab CI analysis
- Authentication/RBAC
- Webhook-driven repository scanning
- Advanced prioritization and remediation assistance
- Enterprise policy profiles
