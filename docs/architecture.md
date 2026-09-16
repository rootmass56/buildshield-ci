# BuildShield-CI Architecture

## 1. Overview

BuildShield-CI is a modular defensive DevSecOps platform for passive CI/CD and software-supply-chain analysis. It discovers security-relevant repository files, routes them to explicit analyzer interfaces, normalizes findings, calculates risk, evaluates policy, produces reports, exposes API/dashboard workflows, persists history, and integrates with GitHub Actions and hardened container deployment.

The released version is **v1.0.0**.

## 2. High-Level Flow

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
Normalized Finding Model
   |
   +--> Risk Scoring / Build Gate
   +--> Policy-as-Code
   +--> JSON / Markdown / HTML / SARIF
   +--> SBOM-lite Inventory
   +--> OSV Vulnerability Intelligence
   +--> FastAPI + React Dashboard
   +--> SQLite History / Trends
   `--> CI/CD + Hardened Docker Runtime
```

## 3. Scanner Core

Primary location:

```text
src/supplysentinel/core/scanner.py
```

Responsibilities:

- validate the target repository path
- enforce workspace/path safety
- discover supported security-relevant files
- classify files by type
- dispatch files to canonical analyzers
- deduplicate normalized findings
- build the scan summary
- invoke risk scoring and downstream policy/report workflows

The hardening program removed dynamic analyzer-name guessing and hidden npm/GitHub Actions fallback analyzers. The scanner calls canonical analyzer functions directly, making routing deterministic and easier to test.

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

Ignored development/runtime folders include `.git`, virtual environments, caches, `node_modules`, generated build output, reports/data output and similar non-source directories.

## 5. Analyzer Layer

Location:

```text
src/supplysentinel/analyzers/
```

| Analyzer | Primary responsibility |
|---|---|
| npm | Lockfiles, mutable versions, lifecycle scripts, dependency confusion / registry controls |
| Python | Pinning, loose versions, dependency confusion / package-index controls |
| GitHub Actions | Action pinning, token permissions, secret echo, pipe-to-shell, `pull_request_target` |
| Dockerfile | Base-image pinning, user hardening, secrets, remote shell execution, upgrade behavior, health checks, remote `ADD` |

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

- `DG-DOCKER-001` — Unpinned/latest base image
- `DG-DOCKER-002` — Missing non-root `USER`
- `DG-DOCKER-003` — Explicit root `USER`
- `DG-DOCKER-004` — Potential secret in `ENV` or `ARG`
- `DG-DOCKER-005` — Remote script piped directly to shell
- `DG-DOCKER-006` — `apt-get upgrade` during image build
- `DG-DOCKER-007` — Missing or disabled `HEALTHCHECK`
- `DG-DOCKER-008` — Remote URL used with `ADD`

## 7. Finding Model

Findings carry structured fields including:

- rule ID
- title
- severity
- category
- confidence
- description
- impact
- evidence
- file path
- line number
- snippet
- remediation
- reference

The normalized model allows all analyzer families to feed the same scoring, policy, report, SARIF, API and dashboard layers.

## 8. Risk Scoring and Build Gate

Location:

```text
src/supplysentinel/core/scoring.py
```

Outputs include:

- overall security score
- overall risk level
- category-wise risk
- penalty contribution
- top risk drivers
- build-gate status
- build-gate reason

Representative mixed-posture profile:

```text
samples/realistic-repo
3 findings
0 Critical / 0 High / 2 Medium / 1 Low
81/100
MEDIUM
Build Gate: WARNING
Policy: PASSED
```

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

- minimum score
- severity thresholds
- lockfile requirement
- pinned GitHub Actions
- secret-echo prevention
- pipe-to-shell prevention
- dependency-confusion prevention
- `pull_request_target` control

Policy evaluation is independent from the risk score. Both are reported so CI/CD can reason about posture and enforcement separately.

## 10. Reporting

Supported outputs include:

- terminal output
- JSON
- Markdown
- HTML
- SARIF 2.1.0
- comparison reports
- dependency inventory output
- OSV intelligence output

SARIF is consumed by GitHub Code Scanning through the project workflow.

## 11. Supply-Chain Intelligence

### SBOM-lite inventory

BuildShield-CI extracts dependency inventory information from supported npm and Python files, including package name, ecosystem, version/pinning state and security-relevant metadata.

### CycloneDX runtime SBOM

The release process generates and verifies a reproducible CycloneDX 1.6 SBOM for the BuildShield-CI runtime environment. CI regenerates it twice and compares the results before comparing the regenerated document with the checked-in SBOM.

### OSV

The OSV integration supports:

- offline query-plan generation
- online vulnerability lookup
- OSV/GHSA identifiers
- vulnerability reporting

Online OSV results are external and dynamic and are therefore kept separate from deterministic static-rule metrics.

## 12. API, Dashboard and Persistence

BuildShield-CI includes a FastAPI backend and React/TypeScript dashboard for:

- authentication/session handling
- overview
- scanning
- findings exploration
- policy results
- comparison
- reports
- dependency inventory
- vulnerability intelligence
- scan history
- risk trends

SQLite stores local scan-history/trend state.

Security controls around the web layer include workspace containment, path/symlink escape prevention, single-tenant authentication/authorization, request validation, resource/concurrency controls, safe public errors, structured logging, request correlation, audit records and report/history retention controls.

## 13. CI/CD Architecture

Workflow:

```text
.github/workflows/buildshield-ci.yml
```

The release-quality workflow enforces:

- Python 3.13 release environment
- hash-locked Linux CI dependencies
- `pip check`
- Ruff
- mypy typed-boundary checks
- pytest with branch coverage
- preserved coverage baseline
- wheel and source-distribution builds
- fresh non-editable wheel installation
- reproducible CycloneDX 1.6 SBOM verification
- exact Node 22.23.2 / npm 12.0.2 frontend environment
- frontend dependency-tree verification
- ESLint, TypeScript typecheck, Vitest, npm audit and production build
- controlled vulnerable/secure security-gate assertions
- SARIF upload to GitHub Code Scanning
- report artifacts

All third-party GitHub Actions are pinned to reviewed full commit SHAs. `tests/test_workflow_security.py` guards against regression to mutable tags or branches. Workflow permissions are denied by default and granted per job only as needed.

## 14. Deployment Layer

The production container uses a multi-stage build:

1. exact Node/npm frontend builder
2. Python wheel builder
3. slim Python runtime image

Runtime controls include:

- numeric non-root UID/GID `10001:10001`
- no runtime home directory / non-login shell
- read-only root filesystem in Compose
- all Linux capabilities dropped
- `no-new-privileges`
- PID limit
- restricted tmpfs
- localhost-only port publication
- persistent report/data volumes
- `SIGTERM` handling
- `/health` liveness
- `/ready` readiness
- fail-closed production authentication configuration

The design is intentionally scoped to controlled single-instance deployment rather than enterprise multi-tenant SaaS.

## 15. Repository Hygiene

Repository controls include:

- `.gitignore` for Python/frontend caches, local environments, generated build/runtime data, secret-like local files, logs and editor/OS artifacts
- `.dockerignore` to reduce Docker build context
- `.gitattributes` for deterministic line endings and fixture semantics
- explicit development dependencies
- no blanket pytest warning suppression
- repository metadata URLs
- reproducible lockfiles
- regression tests that guard release hygiene

The released repository passed final sanitation with no tracked generated trash, no tracked secret-like filenames, no tracked files at or above 5 MiB, `git diff --check` passing, `git fsck` passing and zero merge-conflict markers.

## 16. Testing and Evaluation

Final pre-release Windows Python regression:

```text
295 passed, 2 skipped
```

The release also passed frontend quality/reproducibility gates, fresh wheel installation, SBOM regeneration, Docker/runtime validation, authentication/session smoke, controlled benchmark checks and hosted CI.

The H9 deterministic evaluation framework covers all 20 static rules across a fixed 100-case adversarial corpus.

Pre-hardening baseline:

```text
41 TP / 45 TN / 4 FP / 10 FN
micro precision: 0.911111
micro recall:    0.803922
micro F1:        0.854167
```

After bounded hardening on the same unchanged corpus:

```text
51 TP / 49 TN / 0 FP / 0 FN
precision / recall / F1: 1.000000
```

Those figures describe only the curated deterministic regression corpus and are not estimates of real-world detection accuracy.

## 17. Hardening Program

The completed H1-H10 program covered:

| Stage | Scope | Final state |
|---|---|---|
| H1 | Workspace/filesystem trust boundary | Complete |
| H2 | Authentication, sessions and API authorization | Complete |
| H3 | React/TypeScript dashboard and browser security | Complete |
| H4 | Request validation and resource controls | Complete |
| H5 | Safe errors, structured logging and auditability | Complete |
| H6 | Report/history security and retention | Complete |
| H7 | Docker/runtime hardening | Complete |
| H8 | Reproducibility, SBOM and CI quality gates | Complete |
| H9 | Deterministic evaluation and adversarial hardening | Complete |
| H10 | Final audit, release freeze, documentation and release acceptance | Complete |

## 18. v1.0.0 Release Closure

The final pre-release checkpoint was:

```text
f397d257638f3e3bd50eaaa6b9966442e158a849
```

The verified merge/release commit on `main` was:

```text
dec7eea405cd474fdea73bacd8f9847782887816
```

The annotated `v1.0.0` tag and GitHub release were published after:

- final checkpoint hosted CI passed
- pull-request CI passed
- the accepted PR was merged
- post-merge `main` CI passed
- release evidence and claim boundaries were verified

Historical H7-H10 stage documents remain in `docs/` as engineering evidence. They may describe the state that existed at that specific stage; this architecture document and the final blueprint describe the current released state.

## 19. Explicit Scope Boundaries

The v1.0.0 scope intentionally remains focused. It does not include:

- Maven, Go, NuGet, Rust or other additional package-ecosystem analyzers
- Kubernetes manifest analysis
- GitLab CI or Jenkins analyzers
- AI/LLM remediation assistants
- multi-tenant SaaS architecture
- distributed worker infrastructure
- cloud-provider-specific production deployment stacks

Dependency-confusion detection remains a passive static heuristic security control; BuildShield-CI does not perform live package-registry attacks.

After the verified `v1.0.0` release, normal feature development is frozen. Future changes should be limited to documentation/repository maintenance or clearly versioned corrective/security releases.
