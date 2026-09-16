# H10A Final Release Audit

## Accepted audit basis

H10A audits the exact accepted H9 checkpoint:

- branch: `upgrade/v0.13-security-hardening`
- H9 checkpoint: `7dc643bf5ab6446e9b9e463be14431fb2d76be6e`
- H8 parent: `367ead5670b26c7e6076d063e08b9fb8fdcb206e`
- package version during H10A: `0.12.7`
- H9 hosted CI: successful
- H9 Windows Python regression: 259 passed, 2 skipped
- H9 deterministic corpus: 51 TP / 49 TN / 0 FP / 0 FN on the unchanged 100-case corpus
- controlled benchmark: 22 vulnerable findings / score 5 → 0 secure findings / score 100

The 100% H9 corpus result is regression evidence on a curated deterministic corpus, not a real-world detection-accuracy claim.

## Audit findings

The accepted H9 snapshot was inspected before any H10A repository mutation.

### Release-documentation drift

Several historical documents still described the pre-hardening v0.12.7 state as current, including:

- `57 passed` test-count references;
- statements that H1 had not started;
- statements that API authentication/authorization, browser security, resource controls, report/history hardening and Docker/runtime hardening were still pending;
- the old HTML/CSS/JavaScript frontend stack description after the React/TypeScript migration.

These references are synchronized in H10A while preserving v0.12.7 as the historical tagged baseline.

### Dead/obsolete repository scaffolding

The audit identified bounded cleanup items that are not part of the active runtime:

- empty `src/supplysentinel/parsers/__init__.py` package with no repository references;
- unused duplicate `SECURITY_RELEVANT_FILENAMES` definition in `core/constants.py`;
- unused `InvalidTargetError` and `ScannerExecutionError` exception classes;
- setuptools package-data entries for deleted legacy `src/supplysentinel/web/static/*` files.

The active scanner/analyzer/API architecture is unchanged by removing these residues.

### Line-ending policy

The repository index is normalized, but Windows working-tree evidence showed explicit policy gaps for `.npmrc`, `.pypirc`/`*.conf`, and `.tgz` fixture paths. H10A makes package-manager config files explicit LF text and classifies `.tgz` as binary. Existing H9 fixture semantics are unchanged.

### Generated artifacts

No tracked Python bytecode, pytest caches, Node `node_modules`, frontend build output, coverage output, or TypeScript build-info files were found in the accepted source snapshot.

### Dependency cleanup boundary

No runtime or frontend dependency is removed solely because application source does not import it directly: some direct frontend pins satisfy peer dependencies, and the Python lock/reproducibility strategy is already verified. Dependency/version changes are deferred to H10B only when required by the `1.0.0` freeze.

## H10A acceptance criteria

H10A is complete only when:

- the exact H9 checkpoint is the clean starting point;
- the bounded cleanup applies with no unrelated changes;
- package version remains `0.12.7`;
- targeted H10A release-hygiene tests pass;
- the combined H9 evaluation regression still passes;
- Ruff passes;
- the full Python suite passes;
- the exact controlled 22→0 benchmark is preserved;
- Git diff checks are clean;
- no files are staged or committed.

H10A does not create a checkpoint commit. H10B starts only after H10A validation evidence is accepted.


## H10A validation closure

H10A validation is complete locally:

- H10A release-hygiene regression: 9 passed;
- focused existing security/frontend integration regression: 16 passed;
- complete H9 evaluation regression: 37 passed;
- H9 final metrics preserved byte-for-byte;
- Ruff: PASS;
- mypy cleanup boundary: PASS;
- `pip check`: PASS;
- fresh-source wheel excludes the removed parser and legacy web/static residue;
- full Windows Python regression: 268 passed, 2 skipped;
- exact controlled benchmark: 22 vulnerable findings → 0 secure findings;
- exact 17-file H10A candidate state preserved with zero staging.

H10A is complete. H10B is the `1.0.0` release-candidate version freeze and
reproducible build/SBOM refresh. No H10 checkpoint commit is created in H10A.
