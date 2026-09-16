# H9 Evaluation Corpus Design

## Status

H9A — Rule/Evaluator Inventory + Corpus Design: **COMPLETE LOCALLY.**

This design is anchored to H8 checkpoint
`367ead5670b26c7e6076d063e08b9fb8fdcb206e` and package version `0.12.7`.

## Inventory Result

The accepted H8 implementation exposes four deterministic static analyzers and
20 `DG-*` rules:

- npm: 4 rules;
- Python requirements: 3 rules;
- GitHub Actions: 5 rules;
- Dockerfile: 8 rules.

The existing controlled benchmark remains 22 findings for
`samples/vulnerable-repo` and 0 findings for `samples/secure-repo`.
The inventory also found two rules with neither a literal existing test
reference nor a hit in the vulnerable benchmark:
`DG-DOCKER-003` and `DG-DOCKER-008`.

H9 does not replace the controlled 22→0 benchmark. It adds a purpose-built
classification corpus so individual rules can be measured independently.

## Ground-Truth Contract

`evaluation/corpus-design-v1.json` is the H9 corpus oracle. It defines exactly
100 isolated classification cases: five cases for each of the 20 static rules.

Every rule receives:

1. one canonical positive;
2. one canonical negative;
3. one positive boundary case;
4. one negative near-miss case;
5. one adversarial case whose expected label is explicitly documented.

A case is evaluated only against its declared `rule_id`. A predicted positive
means the scan contains at least one finding with that rule ID. Positive cases
expect exactly one target finding; negative cases expect zero. Additional
non-target findings are recorded as cross-rule leakage rather than silently
changing the target classifier label.

This isolation rule prevents a deliberately vulnerable npm case, for example,
from being counted as a Docker or GitHub Actions classification opportunity.

## Metrics

For every rule H9C will compute TP, TN, FP and FN from the five declared cases,
then calculate precision, recall and F1. It will also report:

- micro totals/precision/recall/F1 across all 100 static cases;
- macro mean precision/recall/F1 across the 20 rules;
- duplicate-target-finding defects;
- cross-rule leakage observations;
- case-level failures with fixture and rule identifiers.

A zero metric denominator evaluates to `0.0` instead of producing NaN. This
keeps reports deterministic and machine-readable.

These measurements are **only performance on the curated deterministic H9
corpus**. They must not be presented as real-world detection accuracy,
population-level false-positive rates, or independent benchmark performance.

## Fixture Isolation

H9B will materialize each case under:

`evaluation/corpus/<RULE-ID>/<case-id>-<case-type>/`

Fixtures will contain only the files required for the target analyzer and safe
baseline controls for unrelated rules. No case requires network access.

The corpus is deliberately designed to include both straightforward cases and
known heuristic stress points. Examples include quoted `write-all` permissions,
commented `pull_request_target`, `printf` secret logging, final-stage Docker
semantics, `USER 0:0`, `HEALTHCHECK NONE`, keyword collisions in package names,
and private-index configurations that still leave public resolution eligible.

These cases are ground-truth requirements, not promises that the H8
implementation already passes all 100. False positives and false negatives
discovered by H9 are expected to be measured explicitly before any bounded
rule-hardening work in H9D.

## OSV Evaluation Boundary

OSV remains part of BuildShield-CI, but it is not mixed into the 20-rule static
confusion matrix because it is external vulnerability intelligence rather than
a `DG-*` static analyzer.

H9 will exercise OSV deterministically with mocked responses for exact-version
query construction, unqueryable loose versions, vulnerable responses and
failure handling. Live OSV data will not determine H9 precision/recall/F1.

## H9 Subphases

- **H9A — COMPLETE LOCALLY:** inventory and immutable corpus/oracle design.
- **H9B — COMPLETE LOCALLY:** 100 isolated static fixtures plus six deterministic
  OSV cases are materialized, hash-indexed and regression-tested.
- **H9C — COMPLETE LOCALLY:** deterministic evaluation
  engine, TP/TN/FP/FN, per-rule metrics, micro/macro metrics and baseline report.
- **H9D — COMPLETE:** adversarial failure review, bounded detector hardening,
  regression closure and checkpoint-ready validation are complete.

No H9 commit is created at the H9A boundary.

## H9B Materialized Corpus Candidate

H9B materializes the H9A oracle without changing its labels.

Status: **COMPLETE LOCALLY when H9B validation succeeds.**

Materialized assets:

- 100 isolated static-analysis fixture repositories under `evaluation/corpus/`;
- exactly five cases per each of the 20 static `DG-*` rules;
- `evaluation/corpus-index-v1.json`, binding every fixture file to its SHA-256;
- `evaluation/osv-cases-v1.json`, containing six network-free deterministic OSV cases;
- structural/determinism regression tests for the complete corpus.

The fixture materialization intentionally preserves adversarial cases that the
current H8 detectors may not classify correctly. H9B validates that the corpus
exists, is immutable relative to its index, is discoverable by the scanner,
runs deterministically, and does not disturb the controlled 22→0 benchmark.
H9B does **not** redefine ground truth to match current detector behavior.

Official TP/TN/FP/FN and precision/recall/F1 calculations remain H9C work.
Any H9B diagnostic prediction snapshot is evidence of the current implementation
only, not a revised oracle and not a real-world accuracy claim.


## H9C Evaluation Engine Candidate

Status: **COMPLETE LOCALLY.**

The H9C evaluator turns the H9A oracle and H9B fixtures into a deterministic
machine-readable baseline. The current pre-hardening detector state produces
41 TP, 45 TN, 4 FP and 10 FN across the 100 static cases, for micro precision
0.911111, micro recall 0.803922 and micro F1 0.854167. Fourteen case labels are
currently mismatched. Eight of the 20 rules classify all five assigned cases
correctly.

This baseline is intentionally not rewritten to make the implementation look
better. H9D will inspect the 14 mismatches against the documented oracle and
apply only bounded, justified detector hardening.

The checked-in baseline is
`evaluation/h9c-baseline-metrics-v1.json`; H9C validation must regenerate the
same deterministic report from the live scanner.

The metrics remain limited to the curated deterministic corpus and are not a
real-world accuracy claim.


## H9D Adversarial Hardening Closure

Status: **COMPLETE.**

H9D keeps the 100-case oracle and fixture corpus fixed while hardening the
detectors against the H9C mismatch set. The candidate reaches 51 TP, 49 TN,
0 FP and 0 FN on the unchanged corpus, with precision/recall/F1 all 1.000000,
20/20 perfect rules, zero classification mismatches, zero target-count
mismatches and zero cross-rule leakage.

The historical H9C baseline is retained separately so the improvement remains
auditable rather than being hidden by replacing the original measurements.

These metrics remain valid only for the curated deterministic corpus.


## H9D Cumulative Validation

The unchanged 100-case corpus was rerun after bounded detector hardening.

Validated result:
- 51 TP / 49 TN / 0 FP / 0 FN;
- micro precision/recall/F1/accuracy: 1.000000;
- macro precision/recall/F1: 1.000000;
- 20/20 rules perfect on their five assigned cases;
- zero classification mismatches;
- zero target-count mismatches;
- zero cross-rule leakage;
- zero duplicate target findings;
- 10 direct H9D hardening tests passed;
- 37 combined H9A-H9D tests passed;
- full Python regression: 259 passed, 2 skipped;
- exact controlled 22→0 benchmark preserved.

The result remains scoped to the curated deterministic corpus. The H9 oracle
and fixture corpus were not changed to obtain the post-hardening score.
