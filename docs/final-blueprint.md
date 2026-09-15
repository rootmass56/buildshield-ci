# BuildShield-CI v1.0.0 Final Blueprint

This file is the project source of truth for the final hardening program and is updated after each verified phase/subphase.

## Release Target

- Product: BuildShield-CI
- Final target: v1.0.0
- Development branch: `upgrade/v0.13-security-hardening`
- Historical verified release: `v0.12.7`
- Deployment positioning: controlled, single-instance deployment with production-style architecture
- Package version remains `0.12.7` until H10 performs the verified `1.0.0` bump and release freeze.

## Verified Checkpoints

- H1 checkpoint: `aed539980677f871a45ac97ebf5b9edffd5cce68`
- H2 checkpoint: `d6c687244bc8b3573f111a20c4a253b43e517964`
- H3 checkpoint: `9aac2ad28e2dfb3252a1f360ef95f328011c4e56`
- H4 checkpoint: created by the successful H4D verification/commit on `upgrade/v0.13-security-hardening`

## Controlled Benchmark

- Vulnerable: 22 findings, 4 Critical, 10 High, 7 Medium, 1 Low, 0 Info, score 5/100, CRITICAL, gate FAILED, policy FAILED.
- Hardened: 0 findings, score 100/100, LOW, gate PASSED, policy PASSED.
- Comparison: +95 score, 22 findings reduced, 100% risk reduction, `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED`.

## Final Program Status

| Stage | Scope | Status |
|---|---|---|
| H1 | Filesystem / workspace trust boundary | COMPLETE |
| H2 | Authentication, sessions and API authorization | COMPLETE |
| H3 | React + TypeScript dashboard and browser security | COMPLETE |
| H4 | Request validation, rate/resource controls | COMPLETE |
| H5 | Safe errors, structured logging and auditability | NEXT |
| H6 | Report/history security and retention | PENDING |
| H7 | Docker/runtime hardening | PENDING |
| H8 | CycloneDX, reproducible build, dependency and CI quality | PENDING |
| H9 | Evaluation corpus and adversarial regression testing | PENDING |
| H10 | Final audit, cleanup, v1.0.0 freeze and release | PENDING |

# H4 — Request Validation and Resource-Abuse Controls

Status: COMPLETE.

## H4A — Strict Request + Query Validation

Status: COMPLETE.

Delivered and verified:
- centralized strict Pydantic request models;
- unknown JSON fields rejected;
- bounded target/policy path strings;
- explicit report-format enums;
- duplicate report formats rejected;
- established `report_formats=[]` no-report execution contract preserved;
- comparison labels bounded with CR/LF/NUL rejection;
- OSV timeout bounded to 1–30 seconds;
- history/trend query limit bounded to 1–100;
- API-level `422` validation regressions;
- focused H4A tests: 22 passed;
- H1/H2/H3 behavior preserved.

## H4B — Request Body, Rate + Concurrency Controls

Status: COMPLETE.

Delivered and verified:
- bounded state-changing `/api/` request bodies;
- early `Content-Length` rejection plus streamed-body byte counting;
- deterministic `413` oversized-body responses;
- per-authenticated-session sliding-window rate limiting for expensive security operations;
- deterministic `429 Too Many Requests` with `Retry-After`;
- global concurrency gate for scan, inventory, OSV intelligence and comparison;
- concurrency slots released in `finally`, including failed operations;
- hashed session material used for in-memory rate-limit keys;
- stale rate-bucket pruning;
- fail-closed environment configuration;
- deterministic tests without wall-clock sleeps;
- focused H4B tests: 7 passed.

Default H4B controls:
- request body: 65,536 bytes;
- expensive operations: 30 per 60 seconds per authenticated session;
- concurrent expensive operations: 2.

Environment controls:
- `BUILDSHIELD_MAX_REQUEST_BODY_BYTES`
- `BUILDSHIELD_API_RATE_LIMIT_REQUESTS`
- `BUILDSHIELD_API_RATE_LIMIT_WINDOW_SECONDS`
- `BUILDSHIELD_MAX_CONCURRENT_OPERATIONS`

## H4C — Scanner / Resource Budgets

Status: COMPLETE.

Delivered and verified:
- repository entry traversal budget;
- security-relevant file-count budget;
- per-security-file byte budget;
- aggregate security-relevant input byte budget;
- ignored dependency/build/cache directories pruned before recursive traversal;
- symlink directories/files not followed by scanner discovery;
- deterministic resource-limit failures before analyzer execution;
- web scan/comparison map scanner budget exhaustion to `413`;
- fail-closed scanner-budget environment validation;
- adversarial tests for entry, file-count, per-file and aggregate limits;
- focused H4C tests: 8 passed;
- analyzer-routing / scanner benchmark tests: 5 passed;
- H4A + H4B regression: 29 passed;
- H1/H2/H3 security regression: 46 passed, 2 skipped;
- complete Python regression after H4C: 139 passed, 2 skipped;
- exact controlled benchmark preserved.

Default H4C controls:
- repository entries inspected: 20,000;
- security-relevant files: 500;
- single security-relevant file: 2 MiB;
- aggregate security-relevant input: 10 MiB.

Environment controls:
- `BUILDSHIELD_SCAN_MAX_ENTRIES`
- `BUILDSHIELD_SCAN_MAX_FILES`
- `BUILDSHIELD_SCAN_MAX_FILE_BYTES`
- `BUILDSHIELD_SCAN_MAX_TOTAL_BYTES`

## H4D — Final H4 Verification + Checkpoint

Status: COMPLETE when the H4D checkpoint script succeeds.

H4D performs:
- final frontend tests and Vite production build;
- final focused H1–H4 security regression;
- final complete Python regression;
- final exact controlled benchmark verification;
- exact H4 changed-file validation;
- H4 commit creation and push;
- local/remote commit equality verification;
- clean working-tree verification.

# H5 — Safe Errors, Structured Logging and Auditability

Status: NEXT.

Planned:
- remove raw internal exception details from API responses;
- introduce safe public error envelopes;
- structured server-side logging;
- request/correlation identifiers;
- security-relevant audit events;
- authentication/action audit coverage;
- sensitive-data redaction;
- deterministic error and logging regressions.

# H6 — Report / History Security and Retention

Status: PENDING.

Planned:
- report access hardening;
- report metadata validation;
- retention policy;
- bounded report/history growth;
- cleanup behavior;
- download/content-type hardening;
- regression coverage.

# H7 — Docker / Runtime Hardening

Status: PENDING.

Planned:
- non-root runtime;
- minimal runtime permissions;
- filesystem/runtime constraints;
- environment/config handling;
- health behavior;
- final Docker/Compose hardening.

# H8 — CycloneDX + Reproducible Build + CI Quality

Status: PENDING.

Mandatory:
- CycloneDX JSON SBOM;
- Ruff;
- mypy;
- pytest + pytest-cov;
- `python -m build`;
- `pip check`;
- frontend `npm ci`;
- ESLint;
- TypeScript typecheck;
- Vitest;
- Vite production build;
- Python locking/reproducibility strategy;
- fresh-environment wheel installation test;
- least-privilege CI permissions;
- immutable GitHub Actions SHA pins.

# H9 — Evaluation Corpus + Adversarial Regression Testing

Status: PENDING.

Mandatory:
- positive fixtures per rule;
- negative fixtures per rule;
- edge/adversarial fixtures;
- TP / TN / FP / FN;
- precision;
- recall;
- F1;
- aggregate metrics;
- per-rule metrics;
- claims limited to the curated deterministic corpus.

# H10 — Final Audit, Cleanup and v1.0.0 Release

Status: PENDING.

Will:
- remove dead code;
- final documentation synchronization;
- final README / SECURITY / architecture review;
- confirm no stale legacy frontend remains;
- final dependency/build audit;
- version bump from `0.12.7` to `1.0.0`;
- fresh clean build;
- complete backend/frontend regressions;
- exact controlled benchmark;
- final branch/PR review;
- CI verification;
- merge;
- tag `v1.0.0`;
- release verification;
- feature development ends after verified v1.0.0 except critical patches.

# Permanent Scope Boundaries

Out of scope for v1.0.0:
- Maven
- Go
- NuGet
- Rust
- Kubernetes scanner
- GitLab CI
- Jenkins
- AI/LLM remediation
- multi-tenant SaaS
- Redis/Kafka/Celery
- distributed workers
- cloud-provider stacks
- enterprise SSO/SCIM
- extra databases
- package-wide rename

The internal Python package remains `supplysentinel`.

The product and CLI brand remains BuildShield-CI.

Async/background scan jobs are not part of v1.0.0.
