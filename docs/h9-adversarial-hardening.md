# H9D Adversarial Detector Hardening

## Purpose

H9D reviews the fixed 14-case mismatch set produced by the H9C pre-hardening
baseline and applies bounded detector changes against the unchanged H9A oracle
and H9B corpus.

The H9C baseline was:

- TP 41 / TN 45 / FP 4 / FN 10;
- micro precision 0.911111;
- micro recall 0.803922;
- micro F1 0.854167;
- 14 classification mismatches;
- 1 cross-rule leakage case.

## Bounded hardening applied

The detector changes are limited to behaviors directly supported by the corpus
contract and security semantics:

- Docker final-stage awareness for USER and HEALTHCHECK;
- Docker recognition of `USER 0:0` as root;
- Docker secret-key matching based on secret-bearing variable names rather than
  arbitrary keyword substrings such as `PASSWORD_POLICY`;
- Docker pipe-to-shell recognition for `/bin/sh` and related shell paths;
- Docker apt/apt-get upgrade recognition when command options precede `upgrade`;
- GitHub Actions quoted `permissions: "write-all"` recognition;
- shell-aware GitHub Actions pipe-to-shell tokenization so quoted log text does
  not become a false positive;
- GitHub Actions secret-log detection for `printf` in addition to echo/Write-Host;
- GitHub Actions comment filtering for `pull_request_target`;
- npm internal-package classification based on explicit private scopes or
  structural internal tokens, avoiding the `oauth-client` substring collision;
- Python dependency-confusion handling that does not treat a private
  `--extra-index-url` as exclusive private resolution;
- Python requirement marker separation so environment-marker comparison
  operators do not become dependency-version false positives.

No rule IDs were removed, no H9 oracle labels were changed, and no corpus
fixture was rewritten to improve the result.

## Post-hardening deterministic result

The same 100-case corpus now produces:

- TP **51**
- TN **49**
- FP **0**
- FN **0**
- precision **1.000000**
- recall **1.000000**
- F1 **1.000000**
- accuracy **1.000000**
- perfect rules **20 / 20**
- classification mismatches **0**
- cross-rule leakage **0**
- duplicate target findings **0**

The original controlled benchmark remains a separate mandatory invariant:
vulnerable **22 findings / score 5** and secure **0 findings / score 100**.

## Claim boundary

The 100% result is valid only for the checked-in curated deterministic H9
corpus. It is not a claim of 100% real-world security detection accuracy or a
population-level false-positive/false-negative rate.


## Validation closure

H9D cumulative validation passed without changing the oracle or fixture corpus:

- direct hardening regression: **10 passed**;
- combined H9A-H9D regression: **37 passed**;
- Ruff: **PASS**;
- full Windows Python regression: **259 passed, 2 skipped**;
- exact controlled benchmark: **22 vulnerable findings → 0 secure findings**;
- historical H9C baseline retained;
- final H9D metrics regenerated deterministically;
- working tree remained in the exact expected 143-file candidate state;
- no files were staged during validation.

H9D is therefore complete and the accumulated H9 tree is ready for the single
H9 checkpoint commit. Hosted CI must pass before H10 changes begin.
