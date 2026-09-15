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
- H1 final local regression: 70 passed, 2 skipped.
- H1 checkpoint: `aed539980677f871a45ac97ebf5b9edffd5cce68`.
- H2 final local regression: 90 passed, 2 skipped.
- H2 checkpoint: `d6c687244bc8b3573f111a20c4a253b43e517964`.
- H3A: React foundation validated; React tests/build passed; Python regression 94 passed, 2 skipped; benchmark preserved.
- H3B: complete React feature migration validated; React tests/build passed; Python regression 96 passed, 2 skipped; benchmark preserved.
- H3C: React production integration and browser security validated; React 6 tests passed; Python regression 102 passed, 2 skipped; exact benchmark preserved.
- H3 final checkpoint: the H3D commit that marks H3 COMPLETE on `upgrade/v0.13-security-hardening`.

## Final Program

| Stage | Scope | Status |
|---|---|---|
| H1 | Filesystem / workspace trust boundary | COMPLETE |
| H2 | Authentication, sessions and API authorization | COMPLETE |
| H3 | React + TypeScript dashboard and browser security | COMPLETE |
| H4 | Request validation, rate/resource controls | NEXT |
| H5 | Safe errors, structured logging and auditability | PENDING |
| H6 | Report/history security and retention | PENDING |
| H7 | Docker/runtime hardening | PENDING |
| H8 | CycloneDX, reproducible build, dependency and CI quality | PENDING |
| H9 | Security evaluation corpus and adversarial regression testing | PENDING |
| H10 | Final audit, cleanup, v1.0.0 freeze and release | PENDING |

## H3 — React + TypeScript Dashboard and Browser Security

Status: COMPLETE.

### H3A — React application foundation

Status: COMPLETE.

Delivered:
- React + TypeScript + Vite application foundation;
- strict TypeScript configuration;
- React Router;
- authenticated application shell;
- typed H2 session API client;
- administrator login;
- Vitest + React Testing Library;
- Vite production build;
- regression checks preventing raw HTML-rendering APIs;
- no credential persistence in browser local/session storage.

### H3B — Full React feature migration

Status: COMPLETE.

Delivered React workflows:
- security posture overview;
- protected repository scanner;
- findings explorer with search and severity filtering;
- policy-as-code results;
- dependency inventory;
- OSV vulnerability intelligence;
- vulnerable-versus-hardened comparison;
- scan history;
- Recharts security-score trends;
- authenticated report center;
- CI/CD security posture;
- product health/about page.

Security behavior:
- H2 CSRF token is sent on state-changing operations;
- scanner-controlled values are rendered using React text interpolation;
- external OSV links are passed through `safeOsvUrl`;
- no `dangerouslySetInnerHTML`, `.innerHTML`, `.outerHTML` or `document.write`;
- no authentication credentials are stored in localStorage/sessionStorage.

### H3C — Production integration and browser security

Status: COMPLETE.

Delivered:
- FastAPI serves the built Vite React SPA;
- direct `/app/...` routes receive the React shell;
- unknown `/api/...` routes remain API 404 responses rather than SPA rewrites;
- canonical frontend-asset containment blocks asset traversal;
- legacy vanilla dashboard assets were removed after React parity;
- feature pages use lazy loading/code splitting;
- Content Security Policy is enforced;
- `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, `Permissions-Policy`, COOP and CORP headers are applied;
- HTML/API responses use `Cache-Control: no-store`;
- hashed Vite assets use long-term immutable caching;
- dedicated FindingsPage XSS regression proves HTML-looking finding content is rendered as inert text;
- dedicated OSV URL unit tests cover valid HTTPS `osv.dev`, HTTP rejection, lookalike-domain rejection and `javascript:` rejection;
- obsolete vanilla OSV UI regression was migrated to the React implementation.

Final H3 verification before checkpoint:
- React/Vitest: 6 passed;
- TypeScript/Vite production build: PASS;
- FastAPI React production integration: PASS;
- React OSV SPA route: PASS;
- browser security controls: PASS;
- legacy vanilla UI removal: PASS;
- Python regression: 102 passed, 2 skipped;
- controlled benchmark: exact 22 findings / 5 score to 0 findings / 100 score preserved.

The 2 skipped Python tests are the existing Windows symlink tests that require symlink-creation privilege; the security tests remain present.

### H3D — Final H3 verification and checkpoint

Status: COMPLETE when the H3D checkpoint script succeeds.

H3D performs:
- final frontend unit/security tests;
- final TypeScript/Vite production build;
- final focused H1/H2/H3 security regression;
- final complete Python regression;
- final exact controlled benchmark verification;
- exact changed-file validation;
- H3 commit creation and push;
- local/remote commit equality verification;
- clean working-tree verification.

## H4 — Next Stage

H4 will harden request validation and resource-abuse controls, including bounded request inputs, scan/resource limits and rate controls appropriate for the controlled single-instance deployment model.

## Permanent Scope Boundaries

The final v1.0.0 does not add Maven, Go, NuGet, Rust, Kubernetes scanning, GitLab CI, Jenkins, AI/LLM remediation, multi-tenant SaaS architecture, Redis/Kafka/Celery, distributed workers, enterprise SSO/SCIM, extra databases, cloud-provider-specific deployment stacks, or package-wide renaming.

The internal Python package remains `supplysentinel`; the product and CLI brand remains BuildShield-CI.

The package version remains `0.12.7` until H10 performs the final verified `1.0.0` version bump and release freeze.
