# BuildShield-CI Screenshots Checklist

Use this checklist for the final portfolio/submission/demo capture. Capture final public-facing screenshots after H10D unless the item is explicitly marked as release-candidate evidence.

## CLI and Validation

- [ ] `buildshield --help`
- [ ] `buildshield version` showing `1.0.0`
- [ ] full Windows regression showing `276 passed, 2 skipped` as H10B release-candidate evidence
- [ ] vulnerable sample showing 22 findings / score 5/100
- [ ] hardened sample showing 0 findings / score 100/100
- [ ] comparison showing +95 and 22 findings reduced

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
- [ ] scanner
- [ ] findings explorer
- [ ] policy result
- [ ] compare view
- [ ] inventory
- [ ] vulnerability intelligence
- [ ] history and trends
- [ ] reports/download view

## GitHub / CI

- [ ] hardening-branch H9 hosted CI success
- [ ] final H10D PR/check suite success
- [ ] Code Scanning page showing controlled sample alerts with explanation
- [ ] immutable full-SHA action pins in workflow
- [ ] final `v1.0.0` tag/release page **after H10D only**

## Docker / Runtime

- [ ] `docker compose ps` with healthy service
- [ ] `/health` liveness response
- [ ] `/ready` production readiness response
- [ ] runtime inspection showing numeric non-root user and read-only root filesystem
- [ ] evidence of dropped capabilities / `no-new-privileges` if desired for technical portfolio material

## Recommended Naming

Use ordered names such as:

```text
01-version.png
02-tests.png
03-vulnerable-scan.png
04-hardened-scan.png
05-comparison.png
06-h9-evaluation.png
07-dashboard-overview.png
08-findings.png
09-policy.png
10-inventory-osv.png
11-history-trends.png
12-ci-success.png
13-code-scanning.png
14-docker-ready.png
15-v1.0.0-release.png
```
