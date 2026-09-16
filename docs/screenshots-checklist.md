# BuildShield-CI Screenshots Checklist

Use this checklist for final portfolio, submission and demo capture from the released v1.0.0 project.

Release reference:

```text
v1.0.0
release commit: dec7eea405cd474fdea73bacd8f9847782887816
```

The default `main` branch may contain later documentation-only maintenance. The `v1.0.0` tag remains the immutable release reference.

## CLI and Validation

- [ ] `buildshield --help`
- [ ] `buildshield version` showing `1.0.0`
- [ ] full Windows regression showing `295 passed, 2 skipped`
- [ ] realistic application showing 3 findings / score 81/100 / MEDIUM / WARNING / policy PASS
- [ ] natural vulnerable-to-realistic comparison showing +76, 22 -> 3 findings and 80% controlled risk reduction
- [ ] vulnerable benchmark sample showing 22 findings / score 5/100
- [ ] hardened sample showing 0 findings / score 100/100
- [ ] controlled comparison showing +95 and 22 findings reduced

## H9 Evaluation Evidence

- [ ] H9C baseline metrics: 41 TP / 45 TN / 4 FP / 10 FN
- [ ] H9D unchanged-corpus result: 51 TP / 49 TN / 0 FP / 0 FN
- [ ] visible claim boundary that 1.000000 F1 is curated regression-corpus performance, not real-world accuracy

## Supply-Chain Intelligence

- [ ] SBOM-lite inventory output
- [ ] OSV offline-plan output
- [ ] optional live OSV result with capture date/time noted because external results are dynamic
- [ ] CycloneDX 1.6 SBOM metadata showing BuildShield-CI 1.0.0

## Dashboard

- [ ] login/authenticated dashboard entry
- [ ] overview
- [ ] realistic scanner result
- [ ] findings explorer
- [ ] policy result
- [ ] natural comparison view
- [ ] controlled benchmark comparison view
- [ ] inventory
- [ ] vulnerability intelligence
- [ ] history and trends
- [ ] reports/download view
- [ ] about/CI information if useful

## GitHub / CI

- [ ] final pre-release checkpoint CI success
- [ ] final pull-request check suite success
- [ ] post-merge `main` CI success
- [ ] Code Scanning page showing controlled sample alerts with explanation
- [ ] immutable full-SHA action pins in workflow
- [ ] published `v1.0.0` tag/release page

## Docker / Runtime

- [ ] `docker compose ps` with healthy service
- [ ] `/health` liveness response
- [ ] `/ready` production readiness response
- [ ] authenticated production login
- [ ] runtime inspection showing numeric non-root user and read-only root filesystem
- [ ] evidence of dropped capabilities / `no-new-privileges` if useful for technical portfolio material

## Recommended Naming

Use ordered names such as:

```text
01-version.png
02-tests-295-pass.png
03-realistic-scan.png
04-vulnerable-benchmark.png
05-hardened-benchmark.png
06-natural-comparison.png
07-controlled-comparison.png
08-h9-evaluation.png
09-dashboard-overview.png
10-findings.png
11-policy.png
12-inventory-osv.png
13-history-trends.png
14-ci-success.png
15-code-scanning.png
16-docker-ready.png
17-v1.0.0-release.png
```

## Capture Guidance

- Do not expose local credentials, password hashes, tokens, private paths or unrelated personal information.
- Keep the intentionally vulnerable fixture visibly labeled as controlled test data.
- When showing 100/100 or H9 F1 = 1.000000, include the benchmark/corpus boundary in the surrounding caption or portfolio text.
- Prefer the realistic 81/100 profile for the main dashboard screenshot so the product does not appear to produce only extreme scores.
