# BuildShield-CI v1.0.0 Final Blueprint

Updated through H8D3 final local validation and the single H8 checkpoint.

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
- H7 checkpoint: `f84839c8e46f3b092349381070bc290f21ab5cbe` — `Harden container and runtime deployment controls`

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
| H8 | CycloneDX, reproducible build, dependency and CI quality | COMPLETE |
| H9 | Evaluation corpus and adversarial regression testing | NEXT |
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

Status: COMPLETE.

Verified checkpoint receipt:
- frontend install/test/audit/build: PASS;
- focused H7 regression: PASS;
- Python regression: 194 passed, 2 skipped;
- fresh container image: PASS;
- fail-closed production runtime: PASS;
- runtime UID/GID: `10001:10001`;
- read-only root filesystem: PASS;
- all Linux capabilities dropped;
- `no-new-privileges`: PASS;
- localhost-only validation binding: `127.0.0.1:18080`;
- liveness/readiness: PASS;
- production authentication: PASS;
- restart/readiness recovery: PASS;
- graceful shutdown: PASS;
- controlled benchmark: PRESERVED;
- pushed checkpoint: `f84839c8e46f3b092349381070bc290f21ab5cbe`;
- remote equality: YES;
- working tree: CLEAN.

## H7 Completion Receipt

H7 closes the container/runtime attack-surface work for the v1.0.0 roadmap:

- H7A: multi-stage production image, non-editable wheel install, React production assets, numeric non-root runtime, limited writable ownership, and real image validation.
- H7B: read-only root filesystem, drop-all capabilities, `no-new-privileges`, init/PID controls, localhost-only publishing, persistent state volumes, and restricted tmpfs.
- H7C: fail-closed production configuration, explicit `/app` workspace boundary, liveness/readiness separation, required runtime auth configuration, production login verification, restart recovery, and graceful shutdown.
- H7D: final cumulative regression, fresh image/runtime validation, checkpoint push verification, and clean-tree freeze.

Known H7 build compatibility note:
the current Windows-generated frontend lockfile omits Linux native optional packages required by TypeScript/Rolldown/Lightning CSS. H7 uses exact pinned builder-only package extraction so the Linux image is testable now. H8 is responsible for replacing that compatibility measure with the final cross-platform reproducibility/locking strategy.

# H8 — CycloneDX + Reproducible Build + CI Quality

Status: IN PROGRESS.

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

## H8A — Python Quality / Build Foundation

Status: COMPLETE.

Delivered:
- Python dev-tool dependencies for Ruff, mypy, pytest-cov, build, and CycloneDX tooling;
- Ruff configuration with an initial correctness-focused error gate;
- mypy configuration and typed-boundary baseline;
- typed Pydantic report-format default factories so mypy preserves the `Literal` element types without changing runtime defaults;
- branch-aware coverage configuration;
- package-build verification with `python -m build`;
- installed-environment verification with `pip check`;
- package version explicitly preserved at `0.12.7`;
- H7 checkpoint/receipt synchronized with the actual pushed SHA;
- H8 phase plan documented.

Validation gate:
- exact H7 checkpoint/base verification;
- dev-tool installation;
- Ruff check;
- mypy typed-boundary check;
- request-model typed-default regression discovered by mypy corrected without changing API behavior;
- focused H8A configuration tests;
- full pytest + coverage regression;
- Python sdist/wheel build;
- `pip check`;
- exact controlled benchmark;
- exact H8A changed-file set.

## H8B — CycloneDX + Python Reproducibility

Status: COMPLETE.

Delivered:
- CPython 3.13 platform-specific reproducibility strategy;
- hash-pinned Windows runtime dependency lock;
- hash-pinned Linux runtime dependency lock;
- hash-pinned Linux development/CI dependency lock;
- pinned `pip-tools==7.6.1` lock generator;
- pinned `cyclonedx-bom==7.4.0` SBOM generator;
- CycloneDX 1.6 JSON runtime SBOM;
- reproducible CycloneDX output verification by repeated SHA-256 comparison;
- repeated lock generation equality checks;
- fresh Windows virtual-environment installation from the hash lock;
- fresh Linux container installation from the hash lock;
- non-editable wheel installation with dependency resolution disabled after locked dependencies are installed;
- `pip check`, CLI/version, and installed-import-location verification on both validated runtime targets.

Validation boundary:
- the committed lock strategy targets the project's validated CPython 3.13
  Windows and Linux environments;
- H8D will consume the Linux development lock in GitHub Actions;
- broader Python/OS combinations are not claimed as verified.

Quality observation:
- H8A surfaced SQLite `ResourceWarning` messages under pytest coverage;
- those warnings are tracked for closure before the H8 final checkpoint.


## H8C — Frontend Reproducibility + Quality

Status: COMPLETE.

Delivered:
- clean cross-platform npm lockfile regeneration strategy;
- canonical frontend package manager pinned to `npm@10.9.9`; current npm Arborist `edgesOut` peer-resolution crash handled explicitly with `--legacy-peer-deps`, direct required-peer pins, and `npm ls --all` validation; the user's global npm installation is not modified;
- deterministic lock regeneration by repeated SHA-256 comparison;
- Windows and Linux `npm ci` validation;
- explicit checks for Windows/Linux TypeScript, Rolldown, and Lightning CSS native optional packages;
- ESLint 9.39.5 correctness gate on the Node-22.15-compatible Babel 7.29.7 parser stack;
- lint-discovered empty error-parser catch block documented explicitly without weakening the `no-empty` rule or changing fallback behavior;
- React Hooks lint rules;
- Babel TypeScript syntax parser for ESLint;
- explicit TypeScript typecheck;
- Vitest;
- npm high-severity audit gate;
- Vite production build;
- removal of H7's manual `npm pack` native-package extraction workaround;
- real Linux frontend-builder Docker-stage validation.
- synchronized H7 deployment regression assertions with the validated H8C Docker model: manual native-package injection is now forbidden and the pinned npm/lock install path is required;

Compatibility note:
- TypeScript remains pinned to `7.0.2`;
- current `typescript-eslint` does not officially support TypeScript 7;
- Babel 8's parser/core line requires a newer Node 22 patch than the frozen Node 22.15.0 runtime;
- H8C therefore uses the compatible Babel `7.29.7` parser/core/preset stack with ESLint `9.39.5`;
- `@testing-library/dom` `10.4.1` is pinned directly because React Testing Library v16 requires it as a peer;
- npm lock/install commands use the documented `--legacy-peer-deps` workaround for the current Arborist peer-set crash, followed by `npm ls --all` and full quality gates;
- TypeScript's compiler remains the semantic type checker.

## H8D — CI Integration + Final H8 Checkpoint

Status: IN PROGRESS.

### H8D1 — SQLite Resource Lifecycle Closure

Status: COMPLETE LOCALLY.

Delivered:
- deterministic SQLite connection closing with `contextlib.closing`;
- focused connection-lifecycle regression coverage;
- `ResourceWarning` promoted to a pytest error;
- full-suite proof must contain no SQLite resource warnings.
- test-harness `TestClient` lifetime hardened: shared, module-level, and one-off clients are explicitly closed;
- delayed Python finalizers are forced at test teardown with garbage collection, and `PytestUnraisableExceptionWarning` is a hard error;
- retention tests no longer use `sqlite3.Connection` as a transaction-only context manager; every direct test SQLite connection is explicitly closed with `contextlib.closing`;
- persistent AST regression coverage forbids direct `with sqlite3.connect(...)` usage in tests;

### H8D2 — Supported Frontend Tooling + CycloneDX Graph Closure

Status: COMPLETE LOCALLY.

Delivered:
- Node `22.23.2` frontend-builder baseline with frontend engine `^22.22.2`;
- npm `12.0.2` canonical frontend package manager;
- clean npm peer resolution with the H8C `--legacy-peer-deps` workaround removed;
- deterministic double lock generation and cross-platform TypeScript/Rolldown/
  Lightning CSS native package coverage;
- ESLint `10.10.0` with `@eslint/js` `10.0.1`;
- Babel `8.0.5` syntax parsing through direct `typescript` + `jsx` parser
  plugins, without a direct TypeScript transform preset;
- Windows and Linux `npm ci`, `npm ls`, lint, typecheck, Vitest, audit and Vite
  production-build proof;
- Docker frontend-builder compatibility on the supported Node/npm model;
- CycloneDX 1.6 regenerated from a fresh hash-locked installed Linux runtime
  environment;
- reproducible SBOM with a populated dependency graph: 6 direct root edges,
  42 total edges and zero unknown graph references;
- package version remains `0.12.7`.

H8D2 does not create a checkpoint commit. H8 remains uncommitted until H8D3
integrates the final CI gates and completes the cumulative H8 validation.

### H8D3 — CI Integration + H8 Checkpoint

Status: COMPLETE LOCALLY — CHECKPOINT READY.

Delivered:
- three-job GitHub Actions architecture for Python quality/reproducibility,
  frontend quality/reproducibility, and controlled security/reporting;
- default-deny workflow permissions with job-scoped least privilege;
- immutable full-SHA action pins, including the Node setup action;
- Linux Python development/CI installation from the checked-in hash lock;
- Ruff, mypy, pytest/branch coverage, package build and `pip check`;
- fresh Linux runtime environment from the runtime hash lock plus non-editable
  wheel installation and installed-import-location verification;
- reproducible CycloneDX environment generation and exact graph validation;
- Node 22.23.2/npm 12.0.2 frontend `npm ci`, `npm ls`, lint, typecheck, Vitest,
  high-severity audit and production build;
- exact vulnerable/secure/comparison benchmark assertions;
- the active hardening branch included in the push trigger so the H8 checkpoint
  receives hosted CI validation.

Final local H8D3 validation:
- workflow YAML syntax: PASS;
- focused CI/build-quality tests: 36 passed;
- Windows full regression: 222 passed, 2 skipped, both without and with
  branch-aware coverage;
- preserved raw coverage baseline: 83.56708123842286% (coverage.py display 84%);
- Ruff, mypy, wheel/sdist build and `pip check`: PASS;
- actual Docker frontend-builder and all Linux frontend gates: PASS;
- fresh Linux Python CI simulation: PASS, including hash locks, full pytest/
  coverage, fresh non-editable wheel installation, CycloneDX reproducibility
  and graph closure, exact benchmark, policy gates and SARIF generation;
- exact 30-file H8 candidate state remained unchanged and unstaged.

H8 is COMPLETE locally and H9 is NEXT. The single H8 checkpoint commit is the
only H8 commit to be pushed from the accumulated H8A-H8D3 working tree.
Acceptance of that checkpoint still requires the hosted GitHub Actions run to
succeed and the pushed branch to match the local checkpoint with a clean
working tree. If hosted CI fails, H8D3 is reopened and H9 does not begin.

# H9 — Evaluation Corpus + Adversarial Regression Testing

Status: NEXT.

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
