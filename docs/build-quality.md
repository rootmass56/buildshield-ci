# BuildShield-CI Build and Quality Gates

This document tracks the H8 dependency/build/CI quality work for the v1.0.0 roadmap.

## H8 phase structure

### H8A — Python quality/build foundation

H8A establishes the Python-side quality toolchain without changing the product version:

- Ruff is introduced as the fast static lint gate.
- mypy is introduced as the typed-code baseline.
- pytest-cov is introduced for branch-aware coverage measurement.
- `python -m build` is introduced as the canonical Python package build.
- `pip check` verifies the installed dependency graph.
- CycloneDX tooling is installed now so H8B can generate the committed/reproducible SBOM workflow.
- package version remains `0.12.7`; only H10 may bump it to `1.0.0`.

H8A intentionally uses a narrow Ruff error-focused ruleset first:
`E9`, `F63`, `F7`, and `F82`.
This catches syntax/undefined-name style correctness failures without turning H8A into an unrelated style-reformatting phase.

The first mypy gate targets strongly typed web/runtime boundaries. Later H8 validation can broaden the checked surface after the baseline is clean.

During H8A validation, mypy identified that Pydantic `Field` default factories for `Literal`-typed report-format lists were inferred as `list[str]`. H8A replaces those anonymous lambdas with explicitly typed factory functions. This is a static-typing correction only; the runtime defaults remain unchanged.

### H8B — CycloneDX + Python reproducibility

H8B is complete locally when its validation script succeeds.

Delivered:

- explicit CPython 3.13 platform lock strategy;
- hash-pinned Windows runtime lock;
- hash-pinned Linux runtime lock;
- hash-pinned Linux development/CI lock;
- `pip-tools==7.6.1` as the deterministic lock generator;
- `cyclonedx-bom==7.4.0` as the pinned SBOM generator;
- CycloneDX 1.6 JSON generated from the Linux runtime lock;
- CycloneDX reproducible-output mode and built-in validation;
- double-generation SHA-256 equality checks for locks/SBOM;
- fresh Windows virtual-environment runtime-lock installation;
- fresh non-editable wheel installation with `--no-deps`;
- fresh Windows `pip check`, CLI, version and import-location verification;
- fresh Linux container runtime-lock installation with `--require-hashes`;
- fresh Linux non-editable wheel installation and `pip check`;
- Linux CLI/version/import-location verification.

The lock strategy is intentionally explicit about its boundary: BuildShield-CI
currently validates CPython 3.13 on Windows and Linux. It does not claim one
universal lock is valid for every Python/OS combination.

The Linux development lock becomes the installation input for H8D CI.

The CycloneDX artifact is written to `sbom/cyclonedx-python.json`.

### H8C — Frontend reproducibility + quality

Planned:

- normalize the cross-platform frontend lockfile;
- remove the temporary H7 Linux native-package extraction workaround once the normalized lockfile is proven;
- add ESLint;
- add an explicit TypeScript typecheck script;
- validate `npm ci`, ESLint, typecheck, Vitest, and Vite production build;
- retain the zero-high-severity npm audit gate.

### H8D — CI integration + final H8 checkpoint

Planned:

- integrate Python/frontend build-quality gates into GitHub Actions;
- minimize workflow permissions by job;
- preserve immutable action SHA pins;
- run fresh-wheel verification in CI;
- run CycloneDX generation/validation in CI;
- run the complete backend/frontend regression set and controlled benchmark;
- checkpoint/push H8 only after all gates pass.

## H8A local verification commands

```powershell
python -m pip install -e ".[dev]"
ruff check src tests
mypy src/supplysentinel/web/runtime_config.py src/supplysentinel/web/request_models.py
pytest -q --cov=supplysentinel --cov-report=term-missing
python -m build
python -m pip check
```

H8A is a foundation stage only. Dependency locking, CycloneDX artifact production, cross-platform frontend lock normalization, and CI integration remain in H8B-H8D.


### H8A quality observation carried forward

The H8A coverage run completed successfully at 83% aggregate branch-aware
coverage, but pytest also surfaced `ResourceWarning` messages for unclosed
SQLite connections in a number of web/API tests. These warnings did not fail
H8A and are not a dependency-reproducibility defect, but they are tracked as
quality debt for closure before the H8 final checkpoint rather than being
silently ignored.


## H8C Frontend Reproducibility and Quality

H8C normalizes the frontend dependency lock and removes the H7-only Linux native-package injection workaround.

The frontend remains on TypeScript 7.0.2. The current `typescript-eslint` release line does not officially support TypeScript 7, so H8C does not force an unsupported parser into the build. H8C used a temporary ESLint 9/Babel 7 compatibility stack for syntax-level linting while TypeScript itself remained the authoritative semantic type checker; H8D2 is responsible for moving that temporary stack to supported tooling.

H8C quality gates:

- clean, deterministic npm lockfile regeneration with no existing `node_modules`;
- Windows `npm ci`;
- Linux `npm ci` in Node 22.15.0;
- cross-platform optional-native package presence checks for TypeScript, Rolldown, and Lightning CSS;
- ESLint correctness rules;
- React Hooks rules;
- explicit TypeScript typecheck;
- Vitest;
- npm high-severity audit gate;
- Vite production build;
- Docker frontend-builder proof with no `npm pack`/manual native injection.

The package lock is regenerated twice from an empty temporary directory and its SHA-256 must be identical. H8C does not claim that npm's registry is globally immutable; it validates deterministic resolution for the pinned direct-dependency set at the time the lock is generated and then uses `npm ci` from the committed lock.


### H8C npm lock-generator correction

The developer workstation currently bundles npm `10.9.2`. During H8C, a clean
`npm install --package-lock-only` on that version failed inside Arborist with
`Cannot read properties of null (reading 'edgesOut')`.

H8C therefore pins the package manager to `npm@10.9.9` in `frontend/package.json`
and uses that exact npm 10 patch release for canonical lock generation and Linux
frontend-builder validation. The project does not modify the workstation's global
npm installation.

The canonical lock is generated in a clean `node:22.15.0-bookworm-slim`
container using npm 10.9.9, regenerated a second time from an empty directory,
and required to produce the same SHA-256. The resulting lock is then consumed
on both Windows and Linux with npm 10.9.9 and must contain the required native
optional packages for both platforms.


### H8C linter compatibility correction

The initial H8C candidate combined ESLint 10 with Babel 8 parser packages.
That was not a suitable fit for the project's frozen Node 22.15.0 runtime:
the Babel 8 parser/core line requires a newer Node 22 patch line, while the
Babel 7.29.7 parser line supports the current runtime but has an ESLint peer
range through ESLint 9.

The corrected H8C lint stack is therefore:

- ESLint `9.39.5`;
- `@eslint/js` `9.39.5`;
- `@babel/core` `7.29.7`;
- `@babel/eslint-parser` `7.29.7`;
- `@babel/preset-typescript` `7.29.7`;
- `eslint-plugin-react-hooks` `7.1.1`;
- TypeScript remains `7.0.2` and remains the semantic type checker.

This avoids forcing an unsupported parser/runtime combination. npm `10.9.9`
remains pinned for canonical lock generation, but the dependency graph itself
is corrected rather than relying on npm-version changes to mask peer/runtime
incompatibility.


### H8C npm Arborist peer-resolution workaround

Repeated clean lock generation on both Windows and Linux reproduced npm's
upstream Arborist crash:

`Cannot read properties of null (reading 'edgesOut')`

The crash occurs while npm builds peer sets and is tracked upstream in current
npm releases. H8C therefore stops treating npm patch-version changes as a
solution.

The controlled workaround is:

- keep the frontend on npm `10.9.9` for a stable documented package-manager
  version;
- generate/install with `--legacy-peer-deps` to bypass the crashing Arborist
  peer-set path;
- explicitly pin required peer dependencies that the application/tests
  actually need, including `@testing-library/dom==10.4.1`;
- keep React, React DOM, React Is, Vite, ESLint and Babel peer counterparts as
  direct exact dependencies;
- validate the resulting installed tree with `npm ls --all`;
- run lint, TypeScript, Vitest, audit and production build on both Windows and
  Linux;
- keep the workaround visible in the Dockerfile and build-quality
  documentation rather than hiding it in a user-level npm configuration.

This is an upstream npm compatibility workaround, not a claim that peer
validation is globally disabled without compensating controls.

### H8C lint-discovered frontend cleanup

The first H8C ESLint run found one pre-existing empty `catch` block in
`frontend/src/api/client.ts`. The behavior was already intentional: if an API
error response body is not JSON, the client falls back to the generic HTTP
status message. H8C keeps that behavior and adds an explanatory comment inside
the catch block so the intent is explicit and the `no-empty` correctness rule
remains enabled.

### H8D follow-up recorded from H8C

The Windows H8C install reports that ESLint 9.39.5 is no longer supported.
H8C keeps the compatibility-tested stack long enough to finish the current
frontend correctness pass, but H8D must resolve this support/deprecation warning
before the final H8 checkpoint. H8 will not be declared complete with that
tooling-support warning left unreviewed.

### H8C deployment-test synchronization

After the H8C Docker frontend builder passed without manual native-package
injection, the full Python suite correctly exposed one stale H7-era deployment
test. That test still required the temporary H7 `npm pack` injection commands.

H8C updates the deployment test to assert the new validated state instead:

- pinned npm `10.9.9` in the frontend builder;
- `npm ci --ignore-scripts --legacy-peer-deps`;
- explicit frontend typecheck + build;
- no `npm pack`;
- no `install_native_package` helper;
- no manually injected TypeScript, Rolldown, or Lightning CSS Linux packages.

This is a test expectation update for an intentional H8C deployment change,
not a suppression of a product regression.


## H8D1 SQLite Resource Lifecycle Closure

H8C completed with 211 passing tests but still surfaced 97 Python 3.13
`ResourceWarning` messages for unclosed SQLite connections.

Root cause: `sqlite3.Connection`'s context-manager protocol manages transaction
commit/rollback behavior; it does not itself guarantee `close()` on context
exit. The history layer therefore retained connections until garbage
collection.

H8D1 changes the history persistence layer to wrap every connection with
`contextlib.closing`, guaranteeing deterministic close semantics after each
database operation.

Quality enforcement:
- a focused lifecycle regression test exercises create/save/read/trend/
  retention/metadata-clear/history-clear operations and checks that no
  `ResourceWarning` is emitted after garbage collection;
- pytest now treats every `ResourceWarning` as an error through
  `filterwarnings = ["error::ResourceWarning"]`;
- the complete suite must pass with no SQLite resource warning debt.

H8D1 does not modify history retention behavior, schema, API contracts, or
controlled scanner benchmark behavior.


### H8D1 final root-cause closure: test-client lifecycle

A complete no-coverage suite proved that a few SQLite finalizer warnings still
appeared even after every BuildShield history connection was explicitly closed.

The warnings were nondeterministic because several tests kept Starlette/FastAPI
`TestClient` objects alive beyond the test that created them:

- the shared authenticated client fixture did not call `close()`;
- dashboard, auth, and React-production tests kept module-level clients alive;
- several logging/error/report tests created local clients without closing them.

Those long-lived ASGI test transports retained request/application object
graphs until later garbage collection, so SQLite finalizers could surface under
an unrelated later test name.

H8D1 closes the test harness lifecycle itself:

- the authenticated-client fixture always closes its `TestClient`;
- every module-level `TestClient` is explicitly closed at module teardown;
- every one-off `TestClient` is closed in the creating test;
- an autouse garbage-collection fixture forces delayed finalizers to surface at
  the end of each test rather than much later in the suite;
- `PytestUnraisableExceptionWarning` is promoted to an error, alongside
  `ResourceWarning`, so this class of lifecycle regression cannot be hidden.

The production SQLite safeguard remains unchanged: every application database
connection is explicitly closed with `contextlib.closing`.


### H8D1 final SQLite warning root cause

The strict per-test garbage-collection gate then exposed the remaining four
warnings with exact allocation tracebacks. They were not production history
connections and were not coverage noise.

The allocations came directly from retention tests that used
`with sqlite3.connect(...) as connection:`. Python's SQLite connection context
manager controls transaction commit/rollback but does not close the connection
when the `with` block exits. Those four test-only connections therefore remained
open until garbage collection.

Final closure:
- the three direct SQLite contexts in `test_web_history_retention.py` now wrap
  `sqlite3.connect(...)` with `contextlib.closing`;
- the direct SQLite context in `test_web_report_retention.py` does the same;
- a persistent AST regression test forbids using `sqlite3.connect(...)`
  directly as a context manager anywhere in the test suite;
- application history connections remain explicitly closed;
- TestClient lifecycles remain explicitly closed;
- delayed finalizers continue to be forced at test teardown;
- both `ResourceWarning` and `PytestUnraisableExceptionWarning` remain hard
  errors. No warning suppression is used.

## H8D2 Supported Frontend Tooling + CycloneDX Graph Closure

H8D2 is complete locally when the final H8D2 validation receipt succeeds.

### Supported frontend toolchain

The H8C compatibility stack is replaced with:

- Node `22.23.2` in the Docker frontend builder;
- frontend Node engine `^22.22.2`;
- npm `12.0.2`;
- ESLint `10.10.0`;
- `@eslint/js` `10.0.1`;
- `@babel/core` `8.0.5`;
- `@babel/eslint-parser` `8.0.5`;
- `eslint-plugin-react-hooks` `7.1.1`;
- TypeScript `7.0.2`;
- Vite `8.2.2`;
- Vitest `5.0.0`.

Babel is used only as the ESLint syntax parser. The final flat config enables
the `typescript` and `jsx` parser syntax plugins directly through
`babelOptions.parserOpts.plugins`; `@babel/preset-typescript` is no longer a
direct frontend dependency. TypeScript remains the semantic type checker.

### npm peer-resolution closure

The H8C npm 10 `--legacy-peer-deps` workaround is removed.

The final Node 22.23.2/npm 12.0.2 candidate was generated from empty lock state
twice without `--legacy-peer-deps`. Both generations produced the same
`package-lock.json` SHA-256, `npm ci` succeeded on Windows and Linux, and
`npm ls --all` accepted the installed dependency graph.

`@testing-library/dom==10.4.1` remains an explicit direct peer because React
Testing Library requires it; removal of `--legacy-peer-deps` is not used as a
reason to make required peers implicit.

The final cross-platform lock continues to contain Windows/Linux native
packages for TypeScript, Rolldown and Lightning CSS. H7's manual `npm pack`
native-package injection remains forbidden.

### Frontend quality evidence

The supported candidate passes:

- Windows `npm ci` without `--legacy-peer-deps`;
- Windows `npm ls --all`;
- ESLint;
- TypeScript typecheck;
- all 6 Vitest tests;
- `npm audit --audit-level=high` with zero vulnerabilities;
- Vite production build;
- Linux Docker `npm ci` and `npm ls --all`;
- Linux ESLint, typecheck, Vitest, audit and production build.

The user's global Node/npm installation is not modified by the validation
workflow; portable/pinned tooling is used for reproducibility checks.

### CycloneDX root dependency graph closure

The previous SBOM contained package components and dependency records but no
populated `dependsOn` edges. H8D2 does not fabricate dependency edges.

Instead, the hash-pinned Linux runtime lock is installed into a fresh Python
3.13 environment, the BuildShield-CI wheel is installed non-editably with
`--no-deps`, and the pinned `cyclonedx-py environment` analyzer inspects that
runtime interpreter while `--pyproject` supplies project/root metadata.

The resulting reproducible CycloneDX 1.6 artifact has:

- root component `buildshield-ci` version `0.12.7`;
- 26 components;
- 27 dependency records;
- 6 direct root dependency edges;
- 42 total dependency edges;
- zero references to unknown graph components.

Two independent generations produced the same SHA-256. Persistent regression
tests require the root dependency entry to remain populated with the six direct
runtime dependencies and reject unknown graph references.

### H8D2 scope boundary

H8D2 changes build/reproducibility tooling and the committed SBOM artifact. It
does not change scanner rules, API behavior, package version, authentication,
history/report semantics, or the controlled security benchmark.

H8D3 remains responsible for integrating these validated gates into GitHub
Actions and creating the single H8 checkpoint commit.

## H8D3 CI Integration — Final H8 Checkpoint

Status: COMPLETE LOCALLY — cumulative H8 validation passed. This document is
finalized as part of the single H8 checkpoint commit. The pushed checkpoint is
accepted only after the hosted GitHub Actions run succeeds; a hosted-CI failure
reopens H8D3 rather than advancing H9.

### Job-scoped least privilege

The GitHub Actions workflow now denies token permissions by default with
`permissions: {}` and grants only job-specific permissions:

- Python quality/reproducibility: `contents: read`;
- frontend quality/reproducibility: `contents: read`;
- controlled security/reporting: `contents: read`, `actions: read`, and
  `security-events: write` for SARIF upload.

SARIF upload is skipped for pull requests originating from forks, where the
GitHub token cannot receive the required code-scanning write permission.

All third-party actions remain pinned to full 40-character commit SHAs.
The H8D3 Node job adds `actions/setup-node` at the immutable commit associated
with the validated v7.0.0 setup action.

### Python CI quality and reproducibility

The Python job targets CPython 3.13 and installs the checked-in
`requirements/dev-py313-linux.lock.txt` with `pip --require-hashes`; editable
project installation and mutable `pip install --upgrade pip` behavior are
forbidden.

The job runs:

- Ruff correctness checks;
- the established mypy typed-boundary gate;
- full pytest with branch coverage;
- the preserved H8 coverage baseline (raw branch-aware coverage must not fall
  below `83.56708123842286%`, while coverage.py's normal zero-decimal display
  remains at least `84%`);
- wheel and source-distribution build;
- a fresh Linux runtime virtual environment installed from
  `runtime-py313-linux.lock.txt` with hashes;
- non-editable project-wheel installation with `--no-deps`;
- `pip check`, CLI/version validation, and an installed-import-path check that
  rejects imports from the checkout;
- two reproducible CycloneDX environment generations;
- byte comparison against the committed SBOM;
- exact CycloneDX graph checks: 26 components, 27 dependency records, six
  direct root edges, 42 total edges, and zero unknown graph references.

### Frontend CI quality and reproducibility

The frontend job uses Node `22.23.2` and pins npm to `12.0.2`. It consumes the
canonical package lock with clean `npm ci` and does not use
`--legacy-peer-deps`.

The job requires:

- `npm ls --all`;
- unchanged `package-lock.json` after `npm ci`;
- ESLint;
- TypeScript typecheck;
- Vitest;
- high-severity npm audit;
- Vite production build.

### Controlled security/reporting gate

The final job runs only after Python and frontend quality jobs succeed. It
installs the Linux CI hash lock, builds and installs the project wheel
non-editably, generates JSON/Markdown/HTML reports plus SARIF, asserts the
vulnerable policy gate exits with code 2, asserts the secure policy gate
passes, and verifies the exact controlled benchmark:

- vulnerable: 22 findings; 4 Critical, 10 High, 7 Medium, 1 Low; score 5;
  CRITICAL; build gate FAILED; policy FAILED;
- secure: 0 findings; score 100; LOW; build gate PASSED; policy PASSED;
- comparison: +95 score; 22 findings reduced; 100% risk reduction;
  `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED`.

The active hardening branch is included in the push trigger so the eventual H8
checkpoint push receives a real hosted CI run before H8 is closed.

### H8D3 cumulative validation result

The local H8D3 cumulative validation passed before checkpoint finalization:

- workflow YAML parsed successfully;
- focused CI/build-quality regression: 36 passed;
- Windows full regression: 222 passed, 2 skipped without coverage;
- Windows full regression: 222 passed, 2 skipped with branch-aware coverage;
- raw branch-aware coverage: 83.56708123842286%; coverage.py display: 84%;
- no `ResourceWarning` or `PytestUnraisableExceptionWarning` debt;
- Ruff: all checks passed;
- mypy: no issues in the established typed-boundary targets;
- wheel + sdist build succeeded;
- `pip check` passed;
- actual Docker frontend-builder and Linux lint/typecheck/Vitest/audit/build passed;
- fresh Linux CI simulation consumed the checked-in development hash lock,
  built and fresh-installed the project wheel against the runtime hash lock,
  passed Linux pytest/coverage, verified installed imports outside the checkout,
  regenerated the exact CycloneDX SBOM/graph, reproduced the exact controlled
  benchmark, exercised both policy gates, and generated SARIF;
- the Linux simulation completed 224 tests and surfaced one third-party
  Starlette/AnyIO `DeprecationWarning`; it did not reintroduce the H8D1
  `ResourceWarning` or `PytestUnraisableExceptionWarning` debt;
- the exact 30-file H8 candidate state remained unchanged after validation.

The single H8 checkpoint commit is therefore ready. After it is pushed,
BuildShield-CI must receive a successful hosted GitHub Actions run on
`upgrade/v0.13-security-hardening`. Only that pushed checkpoint is accepted as
the completed H8 baseline; a hosted-CI failure reopens H8D3.

Package version remains `0.12.7`. The `1.0.0` bump remains reserved for H10.
