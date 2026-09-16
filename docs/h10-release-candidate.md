# H10B v1.0.0 Release-Candidate Freeze

## Status

COMPLETE LOCALLY — H10B validation passed.

H10B changes release identity and release metadata only after H10A cleanup has
passed. It does not create the final Git tag or GitHub release.

## Accepted basis

- branch: `upgrade/v0.13-security-hardening`
- accepted H9 checkpoint: `7dc643bf5ab6446e9b9e463be14431fb2d76be6e`
- H10A validation: PASS
- H10A Windows regression: 268 passed, 2 skipped
- H9 deterministic corpus: 51 TP / 49 TN / 0 FP / 0 FN
- controlled benchmark: 22 vulnerable findings → 0 secure findings

## Release identity freeze

The H10B candidate aligns these active release surfaces to `1.0.0`:

- Python project metadata in `pyproject.toml`;
- runtime `supplysentinel.__version__`;
- private frontend `package.json`;
- frontend lockfile root package identity;
- CycloneDX root-component metadata;
- hosted-CI SBOM root-version assertion;
- current deployment/demo/release documentation.

The Python project classifier advances from Beta to
`Development Status :: 5 - Production/Stable`.

## Historical evidence boundary

H9 evaluation artifacts remain historical evidence and intentionally retain the
product version that was active when H9 ran:

- `evaluation/h9c-baseline-metrics-v1.json` → `0.12.7`;
- `evaluation/h9d-final-metrics-v1.json` → `0.12.7`;
- `evaluation/corpus-design-v1.json` records
  `product_version_during_h9 = 0.12.7`.

They are not rewritten to make historical evidence appear to have been produced
by v1.0.0.

## Dependency and SBOM boundary

H10B does not change runtime/frontend dependency versions merely because the
release version changes.

The existing hash-locked Python dependency inputs remain unchanged. The
CycloneDX dependency graph remains unchanged; only the BuildShield-CI root
component version advances to `1.0.0`. Final hosted CI must regenerate the
CycloneDX artifact from the fresh Linux installed environment and require
byte-for-byte equality with the committed SBOM.

## Acceptance

H10B is complete locally only when:

- all active version surfaces equal `1.0.0`;
- historical H9 version evidence remains `0.12.7`;
- H10A and H9 regressions remain green;
- Ruff, mypy and `pip check` pass;
- a fresh-source wheel is version `1.0.0`;
- a fresh Windows lock-based install reports BuildShield-CI `1.0.0`;
- frontend `npm ci`, lock immutability, lint, typecheck, Vitest, audit and
  production build pass;
- the CycloneDX graph is unchanged except for root version metadata;
- the controlled 22→0 benchmark remains exact;
- the complete Windows Python suite passes;
- the working tree remains the exact expected candidate with zero staging.

No H10 checkpoint commit is created in H10B. H10C is the final
portfolio/demo/documentation pass, and H10D performs final checkpoint/PR/CI/
merge/tag/release verification.


## H10B validation closure

Authoritative Windows release-candidate validation passed with:

- H10B release-candidate tests: 8 passed;
- H10A cleanup regression: 9 passed;
- complete H9 regression: 37 passed;
- historical H9 51 TP / 49 TN / 0 FP / 0 FN metrics byte-identical;
- Ruff, mypy and `pip check`: PASS;
- fresh v1.0.0 wheel + sdist metadata: PASS;
- fresh Windows hash-lock installation reports BuildShield-CI 1.0.0;
- CycloneDX dependency graph preserved with only the root version advanced to 1.0.0;
- exact frontend quality gates passed on Node 22.23.2 / npm 12.0.2 via a disposable Docker fallback because the host toolchain was older;
- exact controlled 22 -> 0 benchmark preserved;
- full Windows Python regression: 276 passed, 2 skipped;
- exact 29-file candidate state preserved with zero staging.

H10B is complete. No final tag or release has been created. H10C is documentation/portfolio closure; H10D remains the final cumulative release acceptance.
