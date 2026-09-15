# BuildShield-CI v1.0.0 Final Blueprint

Updated for H7A container image hardening.

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
- H6 checkpoint: `b4af531f8d86115b8ccdc23f22b49e36400b6253`
- H7 checkpoint: H7D checkpoint commit `Harden container and runtime deployment controls`; SHA is verified after push and recorded in the H7 verification receipt

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
| H7 | Docker/runtime hardening | COMPLETE |
| H8 | CycloneDX, reproducible build, dependency and CI quality | NEXT |
| H9 | Evaluation corpus and adversarial regression testing | PENDING |
| H10 | Final audit, cleanup, v1.0.0 freeze and release | PENDING |

# H7 — Docker / Runtime Hardening

Status: COMPLETE.

## H7A — Production Container Image Hardening

Status: COMPLETE.

Delivered:
- multi-stage frontend builder;
- checked-in frontend install using `npm ci --ignore-scripts`;
- exact Linux x64 native package retrieval via `npm pack` + direct extraction without a second dependency-tree install or lockfile mutation: TypeScript `7.0.2`, Rolldown `1.2.8`, and Lightning CSS `1.33.0`;
- Vite/TypeScript production frontend build inside the container build;
- separate Python wheel-builder stage;
- non-editable Python wheel installation in the final image;
- project source tree excluded from `/app/src` in the runtime image;
- final runtime includes generated React assets;
- explicit numeric unprivileged runtime identity `10001:10001`;
- no runtime home directory and non-login shell;
- writable ownership limited to `/app/reports` and `/app/data`;
- application code/assets remain root-owned/read-only under normal permissions;
- Python bytecode disabled;
- unbuffered output;
- health check retained;
- `SIGTERM` stop signal;
- smaller Docker build context through explicit frontend artifact exclusions;
- deployment documentation aligned with the controlled single-instance security posture.

H7A validation includes:
- deployment-file regression tests;
- real Docker image build;
- runtime image user inspection;
- running-container health verification;
- runtime frontend artifact verification;
- verification that `/app/src` is absent;
- write checks for `/app/reports` and `/app/data`;
- full Python regression;
- exact controlled benchmark.

Important:
- H7A hardens image construction.
- H7B will harden Docker Compose runtime privileges and filesystem behavior.
- The current Windows-generated frontend lockfile omits multiple Linux x64 optional native packages. TypeScript was repaired first; the next real Docker build then exposed the missing Rolldown native binding. H7A now repairs the full currently known Linux x64 native set (TypeScript 7.0.2, Rolldown 1.2.8, Lightning CSS 1.33.0) with exact pinned `npm pack` + direct extraction while avoiding npm 10.9.2's second-install `edgesOut` path.
- H8 will normalize the frontend lockfile for cross-platform optional dependencies and perform the final reproducibility/locking/pinning quality work; H7A does not claim fully reproducible base-image resolution.

## H7B — Compose Least Privilege + Read-Only Runtime

Status: COMPLETE.

Delivered:
- explicit Compose runtime identity `10001:10001`;
- read-only container root filesystem;
- all Linux capabilities dropped;
- `no-new-privileges:true`;
- Docker init process handling;
- PID limit of 256;
- 15-second graceful-stop window;
- localhost-only host publication with default `127.0.0.1:8080` and `BUILDSHIELD_HOST_PORT` override for local port conflicts;
- writable named volumes restricted to `/app/reports` and `/app/data`;
- 64 MiB `/tmp` tmpfs with `noexec`, `nosuid`, and `nodev`;
- explicit `TMPDIR=/tmp`;
- real Compose runtime inspection for rootfs/user/capabilities/security options/PID limit/port binding;
- negative root-filesystem write test;
- positive report/data/tmp write tests;
- health verification under the hardened Compose runtime.

Scope note:
- CPU and memory limits are intentionally deployment-specific rather than hard-coded in the default Compose file.
- H4 application-level request, concurrency, and scanner budgets remain active.
- H7C will finalize production configuration/auth/secret behavior and shutdown/failure semantics.

## H7C — Runtime Configuration + Health/Failure Behavior

Status: COMPLETE.

Delivered:
- explicit runtime environments: development, test, production;
- fail-closed production startup;
- production requires explicit admin username/password hash, cookie-security setting, and workspace root;
- existing H2 PBKDF2 validation reused;
- fixed production workspace root `/app`;
- `/health` retained as liveness;
- `/ready` added as deployment readiness;
- production readiness validates React assets and writable report/data state;
- Dockerfile and Compose health checks use `/ready`;
- Compose requires administrator username and password-hash interpolation;
- no real credentials or password hashes are checked in;
- negative container validation proves missing production auth fails closed;
- real production login validation with ephemeral test-only credentials;
- restart/readiness recovery validation;
- bounded graceful shutdown validation;
- deployment documentation synchronized.

### H7C port-preservation correction

H7C explicitly preserves H7B's configurable localhost host-port mapping:
`127.0.0.1:${BUILDSHIELD_HOST_PORT:-8080}:8080`.

This prevents validation/deployment from disturbing an unrelated service already using localhost port 8080 while retaining localhost-only exposure.

## H7D — Final H7 Verification + Checkpoint

Status: NEXT.

H7D will:
- run frontend tests/build;
- run complete H7 regression;
- run H1-H6 security regressions;
- run complete Python regression;
- rebuild and exercise the final container/Compose configuration;
- verify exact controlled benchmark;
- update blueprint to H7 COMPLETE / H8 NEXT;
- create/push H7 checkpoint;
- verify local/remote equality;
- verify clean working tree.

## H7 Completion Receipt

H7 closes the container/runtime attack-surface work for the v1.0.0 roadmap:

- H7A: multi-stage production image, non-editable wheel install, React production assets, numeric non-root runtime, limited writable ownership, and real image validation.
- H7B: read-only root filesystem, drop-all capabilities, `no-new-privileges`, init/PID controls, localhost-only publishing, persistent state volumes, and restricted tmpfs.
- H7C: fail-closed production configuration, explicit `/app` workspace boundary, liveness/readiness separation, required runtime auth configuration, production login verification, restart recovery, and graceful shutdown.
- H7D: final cumulative regression, fresh image/runtime validation, checkpoint push verification, and clean-tree freeze.

Known H7 build compatibility note:
the current Windows-generated frontend lockfile omits Linux native optional packages required by TypeScript/Rolldown/Lightning CSS. H7 uses exact pinned builder-only package extraction so the Linux image is testable now. H8 is responsible for replacing that compatibility measure with the final cross-platform reproducibility/locking strategy.

# H8 — CycloneDX + Reproducible Build + CI Quality

Status: NEXT.

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
