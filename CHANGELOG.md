# Changelog

All notable BuildShield-CI release milestones are documented here.

## Unreleased

### Documentation and repository maintenance

- Synchronize current documentation with the already-published v1.0.0 release state.
- Preserve historical H9/H10 stage documents as engineering evidence while removing stale pending-release language from canonical documentation.
- Keep the v1.0.0 tag immutable; behavior-changing fixes will use a new versioned release.
- Allow dashboard comparisons to use arbitrary repository paths contained by the configured BuildShield workspace while retaining sample repositories as suggestions.
- Use neutral comparison examples and document the `BUILDSHIELD_WORKSPACE_ROOT` workflow for external-repository dashboard analysis.

## v1.0.0 — 2026-09-16

BuildShield-CI v1.0.0 completed the H1-H10 security-hardening program.

### Added / finalized

- 20 static security rules across npm, Python, GitHub Actions and Dockerfiles.
- Dependency-confusion and registry/index configuration heuristics.
- Risk scoring, build gate and YAML policy-as-code.
- JSON, Markdown, HTML and SARIF reporting.
- GitHub Code Scanning integration.
- SBOM-lite inventory and reproducible CycloneDX 1.6 runtime SBOM.
- OSV offline planning and online vulnerability intelligence.
- FastAPI backend and React/TypeScript dashboard.
- SQLite scan history and trends.
- Single-tenant authentication/authorization, path containment, request/resource controls, safe errors and audit logging.
- Hardened non-root/read-only Docker Compose deployment.
- Hash-locked Python dependencies and exact frontend reproducibility/quality gates.
- SHA-pinned GitHub Actions with least-privilege permissions.
- Fixed 100-case deterministic adversarial evaluation corpus across all 20 rules.
- Representative realistic demo profile at 81/100 with 3 findings.

### Verified release evidence

- Final pre-release checkpoint: `f397d257638f3e3bd50eaaa6b9966442e158a849`
- Release/merge commit: `dec7eea405cd474fdea73bacd8f9847782887816`
- Full Windows regression: **295 passed, 2 skipped**
- Realistic profile: **81/100, 3 findings, MEDIUM, WARNING, policy PASS**
- Natural vulnerable-to-realistic comparison: **5 -> 81, 22 -> 3, 80% controlled reduction**
- Controlled vulnerable-to-hardened benchmark: **5 -> 100, 22 -> 0**
- Hosted CI on final checkpoint, pull request and post-merge `main`: **PASS**
- Production Docker/API smoke and authenticated live-browser review: **PASS**
- Final repository sanitation: **PASS**

### Evaluation boundary

The H9 post-hardening result of 51 TP / 49 TN / 0 FP / 0 FN and F1 = 1.000000 applies only to the fixed curated regression corpus. It is not a real-world 100% accuracy claim.

## v0.12.7

Historical frozen baseline before the H1-H10 hardening program. Historical H9 evidence intentionally records this product version because the H9 evaluation was performed before the v1.0.0 release-version freeze.
