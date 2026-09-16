# H9C Deterministic Evaluation Metrics

## Status

H9C — Evaluation Engine + Metrics: **COMPLETE LOCALLY.**

The evaluator is intentionally deterministic and offline. It measures the 20
static `DG-*` analyzers against the 100-case curated H9 corpus materialized in
H9B. OSV remains a separate six-case deterministic auxiliary evaluation and is
not included in the static confusion matrix.

## Current pre-hardening baseline

The H8 detector implementation evaluated against the H9 corpus produces:

- TP: **41**
- TN: **45**
- FP: **4**
- FN: **10**
- micro precision: **0.911111**
- micro recall: **0.803922**
- micro F1: **0.854167**
- classification accuracy on this corpus: **0.860000**
- macro precision: **0.933333**
- macro recall: **0.833333**
- macro F1: **0.850000**
- classification mismatches: **14 / 100**
- perfect rules on all five assigned cases: **8 / 20**
- cross-rule leakage cases: **1**
- duplicate target findings: **0**

These numbers are the **pre-hardening H9 baseline**. H9D will investigate the
14 mismatches and may apply bounded detector changes where the oracle reflects
the intended security contract.

## Per-rule baseline

| Rule | TP | TN | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| DG-DOCKER-001 | 2 | 3 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| DG-DOCKER-002 | 1 | 2 | 0 | 2 | 1.000000 | 0.333333 | 0.500000 |
| DG-DOCKER-003 | 2 | 2 | 0 | 1 | 1.000000 | 0.666667 | 0.800000 |
| DG-DOCKER-004 | 2 | 2 | 1 | 0 | 0.666667 | 1.000000 | 0.800000 |
| DG-DOCKER-005 | 2 | 2 | 0 | 1 | 1.000000 | 0.666667 | 0.800000 |
| DG-DOCKER-006 | 2 | 2 | 0 | 1 | 1.000000 | 0.666667 | 0.800000 |
| DG-DOCKER-007 | 1 | 2 | 0 | 2 | 1.000000 | 0.333333 | 0.500000 |
| DG-DOCKER-008 | 3 | 2 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| DG-GHA-001 | 2 | 3 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| DG-GHA-002 | 2 | 2 | 0 | 1 | 1.000000 | 0.666667 | 0.800000 |
| DG-GHA-003 | 2 | 2 | 1 | 0 | 0.666667 | 1.000000 | 0.800000 |
| DG-GHA-004 | 2 | 2 | 0 | 1 | 1.000000 | 0.666667 | 0.800000 |
| DG-GHA-005 | 2 | 2 | 1 | 0 | 0.666667 | 1.000000 | 0.800000 |
| DG-NPM-001 | 2 | 3 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| DG-NPM-002 | 3 | 2 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| DG-NPM-003 | 2 | 3 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| DG-NPM-004 | 2 | 2 | 1 | 0 | 0.666667 | 1.000000 | 0.800000 |
| DG-PY-001 | 2 | 3 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| DG-PY-002 | 3 | 2 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| DG-PY-003 | 2 | 2 | 0 | 1 | 1.000000 | 0.666667 | 0.800000 |

## Reproducibility contract

`src/supplysentinel/evaluation/corpus_evaluator.py`:

- loads `evaluation/corpus-design-v1.json` as the immutable case oracle;
- scans each materialized fixture through the normal BuildShield-CI scanner;
- evaluates only the declared target rule for TP/TN/FP/FN;
- records non-target findings separately as cross-rule leakage;
- records target-count deviations independently from classification outcome;
- emits stable per-rule, micro and macro metrics;
- contains no wall-clock timestamps or live-network inputs;
- writes deterministic JSON and Markdown reports.

`evaluation/h9c-baseline-metrics-v1.json` is the checked-in pre-hardening
baseline. H9C validation regenerates the JSON report from the live scanner and
requires exact byte-for-byte equality with that baseline.

Report writers emit canonical UTF-8 bytes with LF (`\n`) line endings rather
than relying on platform text-mode newline translation. This keeps generated
JSON and Markdown byte-stable across Windows and Linux and prevents CRLF/LF
differences from being mistaken for metric drift.

## OSV boundary

The six OSV cases are evaluated without network access:

- exact npm versions become queryable npm OSV requests;
- loose npm versions are skipped;
- exact Python pins become queryable PyPI requests;
- loose Python requirements are skipped;
- a mocked OSV response deterministically produces one vulnerable dependency
  with two vulnerabilities;
- a mocked connection failure exercises the real `FAILED` report path.

OSV results are not folded into the static rule precision/recall/F1 metrics.

## Claim boundary

The metrics above describe **only the curated deterministic H9 corpus**. They
are not estimates of real-world BuildShield-CI detection accuracy, population
false-positive rates, or independent benchmark performance.

H9D subsequently reviewed every mismatch, applied only bounded detector
hardening supported by the defined security contract, reran the same 100-case
evaluation, preserved the controlled 22→0 benchmark and closed the local H9
validation work.


## H9D post-hardening result

H9D keeps the H9A oracle and H9B fixture corpus unchanged. Detector logic was
hardened against the exact failure modes exposed by the pre-hardening H9C
baseline, then the same 100 cases were reevaluated.

Post-hardening deterministic corpus result:

- TP: **51**
- TN: **49**
- FP: **0**
- FN: **0**
- micro precision: **1.000000**
- micro recall: **1.000000**
- micro F1: **1.000000**
- classification accuracy on this corpus: **1.000000**
- macro precision: **1.000000**
- macro recall: **1.000000**
- macro F1: **1.000000**
- classification mismatches: **0 / 100**
- perfect rules: **20 / 20**
- cross-rule leakage cases: **0**
- duplicate target findings: **0**

`evaluation/h9c-baseline-metrics-v1.json` remains unchanged as the historical
pre-hardening baseline. `evaluation/h9d-final-metrics-v1.json` records the
post-hardening result.

This improvement was obtained by changing detector behavior, not by changing
the H9A ground-truth labels or H9B fixture corpus.

The result remains explicitly bounded to the curated deterministic H9 corpus.
It must not be described as 100% real-world detection accuracy.


## H9D validation evidence

The post-hardening metrics were regenerated from the live scanner and matched
`evaluation/h9d-final-metrics-v1.json` exactly.

Validation:
- direct H9D adversarial tests: 10 passed;
- combined H9A-H9D regression: 37 passed;
- Ruff: PASS;
- full Windows Python regression: 259 passed, 2 skipped;
- controlled vulnerable/secure benchmark: exact 22→0 preserved;
- repository state remained unchanged and unstaged.

The historical H9C pre-hardening baseline is intentionally retained for an
auditable before/after comparison.
