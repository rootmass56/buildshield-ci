# H10D Final Release Acceptance

## Status

LOCAL RELEASE ACCEPTANCE: PASS — this finalized acceptance text is intended for the single H10 checkpoint; merge, tag and GitHub release remain deferred pending hosted CI.

## Accepted basis

- development branch: `upgrade/v0.13-security-hardening`
- accepted H9 checkpoint: `7dc643bf5ab6446e9b9e463be14431fb2d76be6e`
- H10A cleanup: PASS
- H10B v1.0.0 release-candidate freeze: PASS
- H10C portfolio/demo/documentation closure: PASS
- H10C Windows regression: 286 passed, 2 skipped
- package/runtime/frontend release identity: `1.0.0`
- historical H9 deterministic evidence: 51 TP / 49 TN / 0 FP / 0 FN
- controlled benchmark: 22 vulnerable findings -> 0 secure findings

## Local final acceptance gates

The authoritative H10D local/container acceptance run passed all of the following gates before any H10 commit:

1. release identity remains `1.0.0` across Python, runtime, frontend and SBOM surfaces;
2. H10A/H10B/H10C and H9 regression contracts remain green;
3. historical H9 evidence remains byte-for-byte unchanged;
4. Ruff, mypy and `pip check` remain green;
5. the exact controlled 22 -> 0 benchmark remains unchanged;
6. a fresh production Docker image builds from the current release candidate;
7. the image reports BuildShield-CI `1.0.0`, runs as UID/GID `10001:10001`,
   contains production frontend assets and does not contain `/app/src`;
8. production startup without required authentication configuration fails closed;
9. Docker Compose starts with ephemeral validation credentials on a
   localhost-only random port;
10. the running container preserves read-only rootfs, `cap_drop: ALL`,
    `no-new-privileges`, PID limit 256 and restricted `/tmp`;
11. `/health` and `/ready` pass, authenticated login/session works,
    `/app/reports`, `/app/data` and `/tmp` are writable, and `/app` root
    remains non-writable;
12. restart returns to readiness and Compose shuts down cleanly;
13. the complete Windows Python regression passes;
14. the repository remains the exact expected uncommitted H10 candidate with
    zero staging and `git diff --check` clean.

Authoritative H10D local result:
- final-release invariant tests: 8 passed;
- cumulative H9/H10 selected release regression: 72 passed;
- full Windows regression: 294 passed, 2 skipped;
- historical H9 metrics: 51 TP / 49 TN / 0 FP / 0 FN, byte-for-byte preserved;
- controlled benchmark: 22 vulnerable findings -> 0 secure findings;
- fresh production image / hardened Compose / authentication / restart gates: PASS;
- exact 34-file candidate preserved with zero staging;
- Docker validation resources cleaned up.

## Post-Checkpoint Final Polish Evidence

After the original H10 checkpoint passed hosted CI, the release candidate received a final professional UI pass and a representative realistic application profile. Those post-checkpoint changes were validated independently:

- realistic dashboard/API contract: PASS;
- realistic application: 81/100, 3 findings, MEDIUM risk, WARNING gate, policy PASS;
- natural vulnerable-to-realistic comparison: +76 score, 19 findings reduced, 80% controlled risk reduction;
- original vulnerable/hardened benchmark preserved at 5/100 -> 100/100 and 22 -> 0 findings;
- exact Node 22.23.2 / npm 12.0.2 frontend gates: PASS;
- production Docker/API smoke with all three profiles and authentication/session: PASS;
- full Windows regression: **295 passed, 2 skipped**;
- live browser review: PASS;
- final repository sanitation: PASS with zero staging.

Because these changes were made after checkpoint `7bc58e905789fe2990223d3cf520729c14d98e1f`, a replacement final checkpoint must pass hosted CI before merge/tag/release.

## Release sequence after local acceptance

Passing local H10D validation does not itself release v1.0.0. The checkpoint commit containing this finalized acceptance record must still pass hosted CI before merge, tag and GitHub release.

The remaining release sequence is:

1. synchronize final release documentation with the post-checkpoint evidence;
2. create the replacement final checkpoint commit;
3. push the hardening branch;
4. require hosted GitHub Actions success on that exact replacement checkpoint;
5. open/review the final pull request;
6. merge the accepted release state;
7. verify `main` and hosted CI on the merged release state;
8. create and push an annotated `v1.0.0` tag on the verified release commit;
9. create/verify the GitHub release and release artifacts;
10. freeze normal feature development except critical corrective patches.

## Claim boundary

Container/runtime acceptance demonstrates the tested single-instance deployment
profile. It does not convert BuildShield-CI into enterprise multi-tenant SaaS.

The H9 1.000000 precision/recall/F1 result remains scoped to the fixed curated
100-case deterministic corpus and is not a real-world 100% accuracy claim.
