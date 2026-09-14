# BuildShield-CI v1.0.0 Final Blueprint

This file is the project source of truth for the final hardening program. It is updated whenever a verified phase is completed.

## Release Target

- Product: BuildShield-CI
- Final target: v1.0.0
- Development branch: `upgrade/v0.13-security-hardening`
- Historical verified release: `v0.12.7`
- Final scope: controlled, single-instance deployment with production-style security architecture
- Feature development ends after the verified v1.0.0 release.

## Verified Baseline

- Controlled vulnerable fixture: 22 findings, 4 Critical, 10 High, 7 Medium, 1 Low, score 5/100, CRITICAL, build gate FAILED, policy FAILED.
- Controlled hardened fixture: 0 findings, score 100/100, LOW, build gate PASSED, policy PASSED.
- Comparison: +95 score, 22 findings reduced, 100% risk reduction, `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED`.
- Pre-H1 regression baseline: 57 tests passing.
- H1 final local regression: 70 passed, 2 skipped.
- The two skipped tests are platform-dependent symlink-creation checks that require Windows symlink privileges; the canonical containment code and the remaining path-security tests passed.

## Final Program

| Stage | Scope | Status |
|---|---|---|
| H1 | Filesystem / workspace trust boundary | COMPLETE |
| H2 | Authentication, sessions and API authorization | NEXT |
| H3 | React + TypeScript dashboard and browser security | PENDING |
| H4 | Request validation, rate/resource controls | PENDING |
| H5 | Safe errors, structured logging and auditability | PENDING |
| H6 | Report/history security and retention | PENDING |
| H7 | Docker/runtime hardening | PENDING |
| H8 | CycloneDX, reproducible build, dependency and CI quality | PENDING |
| H9 | Security evaluation corpus and adversarial regression testing | PENDING |
| H10 | Final audit, cleanup, v1.0.0 freeze and release | PENDING |

## H1 — Filesystem / Workspace Trust Boundary

Status: COMPLETE.

### H1A — Pre-implementation freeze

Complete.

Verified:
- branch `upgrade/v0.13-security-hardening`;
- exact starting checkpoint `6e9e5822e87e026802ac6008886f99ac484685f8`;
- clean working tree;
- 57-test baseline;
- exact vulnerable/hardened/comparison benchmark.

### H1B — Workspace and report path security

Complete.

Implemented:
- `BUILDSHIELD_WORKSPACE_ROOT`;
- canonical workspace root resolution;
- canonical repository-directory validation;
- canonical policy-file validation;
- relative-path support inside the approved workspace;
- rejection of parent traversal;
- rejection of absolute external paths;
- rejection of sibling-prefix containment tricks;
- canonical symlink-aware containment checks;
- repository directory type enforcement;
- policy file type enforcement;
- API use of validated canonical paths for scan, inventory, OSV and comparison operations;
- report run-ID and filename component validation;
- canonical report-root containment;
- report symlink escape protection;
- `.env.example` workspace-root documentation;
- dedicated path-security regression tests.

### H1C — Final verification and checkpoint

Complete when the H1 checkpoint commit is created and pushed by the H1C finalization script.

Final H1 acceptance requirements:
- focused H1 regression passes;
- complete regression passes;
- controlled benchmark remains exact;
- `git diff --check` passes;
- exactly the five intended H1 files are committed;
- branch push succeeds;
- remote branch matches local H1 checkpoint;
- working tree is clean.

## Current Security Architecture After H1

The CLI remains capable of scanning explicit local paths as a trusted local-user interface.

The web/API boundary now follows:

```text
Caller-supplied path
        |
        v
Configured workspace root
        |
        v
Canonical path resolution
        |
        v
Path containment check
        |
        +--> outside workspace -> reject
        |
        v
Existence + file/directory validation
        |
        v
Canonical validated path
        |
        v
Scanner / policy / inventory / OSV / comparison
```

Report downloads now follow:

```text
run_id + filename
        |
        v
Single-component validation
        |
        v
Canonical report/run/file resolution
        |
        v
Containment verification
        |
        +--> escape/symlink escape -> reject
        |
        v
Existing regular report file
```

## Next Stage

H2 — Authentication, Sessions and API Authorization.

H2 will add a focused single-instance authentication foundation for sensitive API operations. It will not introduce enterprise multi-tenancy, SSO, SCIM or broad RBAC.

## Permanent Scope Boundaries

The final v1.0.0 does not add Maven, Go, NuGet, Rust, Kubernetes scanning, GitLab CI, Jenkins, AI/LLM remediation, multi-tenant SaaS architecture, distributed workers, enterprise SSO/SCIM, or cloud-provider-specific deployment stacks.

The internal Python package remains `supplysentinel`; the product and CLI brand remains BuildShield-CI.
