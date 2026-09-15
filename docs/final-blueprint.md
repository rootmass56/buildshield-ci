# BuildShield-CI v1.0.0 Final Blueprint

Updated after successful H6D final verification.

## Release Target

- Product: BuildShield-CI
- Final target: v1.0.0
- Development branch: `upgrade/v0.13-security-hardening`
- Historical verified release: `v0.12.7`
- Deployment positioning: controlled, single-instance deployment with production-style architecture
- Package version remains `0.12.7` until H10 performs the verified `1.0.0` version bump and release freeze.

## Verified Checkpoints

- H1 checkpoint: `aed539980677f871a45ac97ebf5b9edffd5cce68`
- H2 checkpoint: `d6c687244bc8b3573f111a20c4a253b43e517964`
- H3 checkpoint: `9aac2ad28e2dfb3252a1f360ef95f328011c4e56`
- H4 checkpoint: `3c68510a376f5f9662a76043586498c2f5e01d3e`
- H5 checkpoint: `1ba53f5528c939b02cf29c6d14b5da354212d638`
- H6 checkpoint: created by the successful H6D verification/commit on `upgrade/v0.13-security-hardening`

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
| H5 | Safe errors, structured logging and auditability | COMPLETE |
| H6 | Report/history security and retention | COMPLETE |
| H7 | Docker/runtime hardening | NEXT |
| H8 | CycloneDX, reproducible build, dependency and CI quality | PENDING |
| H9 | Evaluation corpus and adversarial regression testing | PENDING |
| H10 | Final audit, cleanup, v1.0.0 freeze and release | PENDING |

# H6 — Report / History Security and Retention

Status: COMPLETE.

## H6A — Report Listing + Download Exposure Hardening

Status: COMPLETE.

Delivered:
- bounded authenticated report listing;
- report extension allowlist: `.json`, `.md`, `.html`, `.sarif`;
- hidden and unsupported report files excluded;
- report-directory/report-file symlinks excluded from exposure;
- canonical H1 report containment retained;
- maximum downloadable report size enforced;
- oversized reports omitted from listing and rejected with `413`;
- unsupported extensions rejected with `404`;
- forced `application/octet-stream`;
- attachment disposition;
- `Cache-Control: no-store`;
- existing `nosniff` protection retained;
- successful downloads audited;
- listing includes bounded `size_bytes`;
- invalid report-security configuration fails closed.

Defaults:
- maximum listed reports: 500;
- maximum download size: 20 MiB.

Verified:
- focused H6A: 8 passed;
- full Python after H6A: 167 passed, 2 skipped;
- exact benchmark preserved.

## H6B — History Growth + Retention Policy

Status: COMPLETE.

Delivered:
- maximum retained SQLite history row count;
- UTC age-based history retention;
- deterministic pruning immediately after history writes;
- explicit retention helper for existing rows;
- `created_at` and `run_id` indexes;
- bounded SQLite connection timeout;
- recent-history descending order preserved;
- trend chronological order preserved;
- existing API query limits preserved;
- invalid retention config fails closed before write.

Defaults:
- maximum stored history rows: 1,000;
- history retention age: 90 days.

Verified:
- focused H6B: 7 passed;
- existing history + H6A contracts: 12 passed;
- compatibility fix aligned test doubles with production `model_dump(mode="json")`;
- full Python after H6B: 174 passed, 2 skipped;
- exact benchmark preserved.

## H6C — Report Retention + Cleanup Consistency

Status: COMPLETE.

Delivered:
- bounded report run-directory count;
- UTC age-based report retention;
- deterministic cleanup after scan/inventory/OSV/comparison report generation;
- safe recursive deletion without following nested symlinks;
- deletion restricted to direct run-directory children of the canonical report root;
- outside/root/unsafe deletion targets refused;
- report-run symlinks ignored by automated retention;
- SQLite history reconciliation clears stale report metadata and sets `report_count=0` for pruned runs;
- cleanup audit events record counts only;
- retention failures fail closed with safe `503`;
- nested run content removed without escaping report root.

Defaults:
- maximum retained report runs: 250;
- report retention age: 30 days.

Verified:
- focused H6C: 7 passed;
- H6B/history contracts: 11 passed;
- H6A: 8 passed;
- H5: 20 passed;
- H4: 42 passed;
- prior security: 46 passed, 2 skipped;
- full Python after H6C: 181 passed, 2 skipped;
- exact controlled benchmark preserved;
- exact H6 changed-file set: 8.

## H6D — Final H6 Verification + Checkpoint

Status: COMPLETE when the H6D checkpoint script succeeds.

H6D performs:
- frontend dependency install;
- React tests;
- Vite production build;
- complete H6A/H6B/H6C regression;
- H5 regression;
- H4 regression;
- H1/H2/H3 security regression;
- complete Python regression;
- exact controlled benchmark verification;
- exact H6 changed-file validation;
- H6 commit creation and push;
- local/remote equality verification;
- clean working-tree verification.

# H7 — Docker / Runtime Hardening

Status: NEXT.

Planned:
- non-root container runtime;
- minimal runtime permissions;
- immutable/minimal runtime filesystem where practical;
- controlled writable data/report paths;
- environment/config hardening;
- production health behavior;
- Docker/Compose least-privilege configuration;
- container user/capability/security-option checks;
- runtime regression coverage.

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
- fresh-wheel installation verification;
- least-privilege CI permissions;
- immutable GitHub Actions SHA pins.

# H9 — Evaluation Corpus + Adversarial Regression Testing

Status: PENDING.

Mandatory:
- positive fixtures per rule;
- negative fixtures per rule;
- edge/adversarial fixtures;
- TP/TN/FP/FN;
- precision;
- recall;
- F1;
- aggregate metrics;
- per-rule metrics;
- claims limited to curated deterministic corpus performance.

# H10 — Final Audit, Cleanup and v1.0.0 Release

Status: PENDING.

Will:
- remove dead code;
- synchronize final documentation;
- final README / SECURITY / architecture review;
- confirm legacy frontend remains removed;
- final dependency/build audit;
- bump package version from `0.12.7` to `1.0.0`;
- fresh clean build;
- complete frontend/backend regressions;
- exact controlled benchmark;
- final branch/PR review;
- CI verification;
- merge;
- tag `v1.0.0`;
- release verification;
- stop feature development after verified v1.0.0 except critical patches.

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
