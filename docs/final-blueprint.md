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
- H1 checkpoint commit: `aed539980677f871a45ac97ebf5b9edffd5cce68`.
- H2 final local regression: 90 passed, 2 skipped in 3.43s.
- H2 controlled benchmark: preserved exactly.

## Final Program

| Stage | Scope | Status |
|---|---|---|
| H1 | Filesystem / workspace trust boundary | COMPLETE |
| H2 | Authentication, sessions and API authorization | COMPLETE |
| H3 | React + TypeScript dashboard and browser security | NEXT |
| H4 | Request validation, rate/resource controls | PENDING |
| H5 | Safe errors, structured logging and auditability | PENDING |
| H6 | Report/history security and retention | PENDING |
| H7 | Docker/runtime hardening | PENDING |
| H8 | CycloneDX, reproducible build, dependency and CI quality | PENDING |
| H9 | Security evaluation corpus and adversarial regression testing | PENDING |
| H10 | Final audit, cleanup, v1.0.0 freeze and release | PENDING |

## H1 â€” Filesystem / Workspace Trust Boundary

Status: COMPLETE.

H1 added:
- `BUILDSHIELD_WORKSPACE_ROOT`;
- canonical repository and policy path validation;
- rejection of traversal, sibling-prefix and external absolute-path escapes;
- symlink-aware containment checks;
- canonical report-root containment and report filename/run-ID validation;
- dedicated path-security regression tests.

Final H1 checkpoint:

```text
aed539980677f871a45ac97ebf5b9edffd5cce68
Harden web workspace and report path boundaries
```

## H2 â€” Authentication, Sessions and API Authorization

Status: COMPLETE.

### H2A â€” Authentication foundation

Complete.

Implemented:
- PBKDF2-HMAC-SHA256 password hashing;
- environment-driven admin username and password hash;
- fail-closed missing/invalid authentication configuration;
- opaque cryptographically random server-side sessions;
- HttpOnly session cookie;
- SameSite=Strict cookie policy;
- configurable Secure-cookie mode for HTTPS deployment;
- bounded session lifetime;
- CSRF token generation and validation;
- logout/session invalidation;
- constant-time username/password comparison;
- generic invalid-credential responses;
- bounded temporary failed-login lockout;
- `/api/auth/login`;
- `/api/auth/session`;
- `/api/auth/logout`;
- authentication regression tests.

### H2B â€” API authorization integration

Complete.

Protected authenticated GET operations:
- `/api/sample-repositories`;
- `/api/history`;
- `/api/history/trend`;
- `/api/reports`;
- `/api/reports/{run_id}/{filename}`.

Protected authenticated + CSRF state-changing operations:
- `/api/scan`;
- `/api/inventory`;
- `/api/vulnerability-intelligence`;
- `/api/compare`;
- `/api/auth/logout`.

Public service/bootstrap endpoints:
- `/`;
- `/health`;
- `/api/auth/login`;
- `/api/auth/session`.

The existing API, scan-history, OSV and H1 path-security tests authenticate through the real login flow rather than bypassing authorization dependencies.

### H2C â€” Final verification and checkpoint

Complete when the H2C script creates and pushes the H2 checkpoint.

Final H2 acceptance requirements:
- authentication tests pass;
- authorization boundary tests pass;
- H1 security regressions remain intact;
- complete test suite passes;
- controlled 22-to-0 benchmark remains exact;
- `git diff --check` passes;
- exactly the intended ten H2 files are committed;
- remote upgrade branch matches the local H2 checkpoint;
- working tree is clean.

## Current Security Architecture After H2

```text
Browser / API client
        |
        +--> GET /health, GET / ----------------------> public
        |
        +--> /api/auth/login -------------------------> credential verification
        |                                                |
        |                                                v
        |                                      random server-side session
        |                                                |
        |                                      HttpOnly SameSite cookie
        |
        +--> protected GET ----------------------------> authenticated session required
        |
        +--> protected POST ---------------------------> authenticated session
                                                         + valid CSRF token
                                                               |
                                                               v
                                                   H1 workspace boundary
                                                               |
                                                               v
                                                   scanner / policy / OSV /
                                                   inventory / comparison
```

The authentication model is intentionally focused on controlled, single-instance deployment. It is not a multi-tenant SaaS identity platform.

## Next Stage

H3 â€” React + TypeScript dashboard and browser security.

H3 will replace the legacy vanilla dashboard with the final React/TypeScript interface while preserving the FastAPI backend, authenticated session model, H1 workspace boundary and current functional benchmark.

## Permanent Scope Boundaries

The final v1.0.0 does not add Maven, Go, NuGet, Rust, Kubernetes scanning, GitLab CI, Jenkins, AI/LLM remediation, multi-tenant SaaS architecture, distributed workers, enterprise SSO/SCIM, or cloud-provider-specific deployment stacks.

The internal Python package remains `supplysentinel`; the product and CLI brand remains BuildShield-CI.
