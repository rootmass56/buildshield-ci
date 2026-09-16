# BuildShield-CI Python Dependency Locks

H8B introduces explicit Python 3.13 dependency locks for the two environments
that BuildShield-CI actually validates during the v1.0.0 hardening roadmap.

## Lock files

- `runtime-py313-windows.lock.txt`
  - runtime dependencies resolved on Windows with CPython 3.13;
  - used by the fresh local wheel-install verification.
- `runtime-py313-linux.lock.txt`
  - runtime dependencies resolved inside the Python 3.13 slim Linux container;
  - used by the fresh Linux wheel-install verification and CycloneDX SBOM.
- `dev-py313-linux.lock.txt`
  - runtime + `[dev]` dependencies resolved for the Linux CI target;
  - consumed by the H8D3 GitHub Actions Python quality and security/reporting jobs.

Every generated lock is fully pinned and includes package hashes for pip
hash-checking mode.

## Resolver/tool versions

The H8B lock generator is pinned to:

- Python: 3.13 target
- pip-tools: 7.6.1
- CycloneDX Python: 7.4.0

The project version remains `0.12.7` until H10.

## Regeneration

Windows runtime lock:

```powershell
python -m piptools compile pyproject.toml `
  --output-file requirements/runtime-py313-windows.lock.txt `
  --generate-hashes `
  --strip-extras `
  --resolver=backtracking
```

Linux runtime/dev locks are generated inside `python:3.13-slim` with
`pip-tools==7.6.1`. H8D3 consumes the Linux development lock in GitHub Actions
with `pip --require-hashes`.

## Reproducibility boundary

These files pin Python dependency resolution for the validated CPython 3.13
targets. They do not claim that every historical/future Python version or every
operating system has been resolved.

The Linux lock is validated by installing it in a fresh Linux container with
`pip --require-hashes`, then installing the built BuildShield-CI wheel
non-editably with `--no-deps` and running `pip check`.

The Windows runtime lock is validated the same way in a fresh local virtual
environment.

## SBOM

`../sbom/cyclonedx-python.json` is generated from a fresh installed Linux
runtime environment, not by treating the requirements file itself as a complete
dependency graph.

The environment is created from `runtime-py313-linux.lock.txt` with
`pip --require-hashes`, the BuildShield-CI wheel is installed non-editably with
`--no-deps`, and `pip check` must pass. The pinned CycloneDX tool from the Linux
development lock then analyzes that runtime interpreter:

```text
cyclonedx-py environment \
  --pyproject /work/pyproject.toml \
  --spec-version 1.6 \
  --output-format JSON \
  --output-reproducible \
  --output-file /tmp/cyclonedx-python.json \
  /opt/runtime/bin/python
```

Using the installed-environment analysis mode allows CycloneDX to emit the real
package dependency relationships while `--pyproject` supplies the
BuildShield-CI root-component metadata. H8D2 requires:

- two independent SBOM generations to be byte-identical;
- root component `buildshield-ci` version `0.12.7`;
- a populated root dependency graph containing the six direct runtime
  dependencies;
- no dependency references to unknown components.

The H8D2 artifact contains 6 direct root edges and 42 total dependency edges.
No graph edges are hand-authored merely to silence a validator warning.
