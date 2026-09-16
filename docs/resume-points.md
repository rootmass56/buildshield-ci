# BuildShield-CI Resume Points

## Project Title

**BuildShield-CI — DevSecOps CI/CD Supply Chain Security Analyzer**

## Recommended Technical Stack

Python, FastAPI, React, TypeScript, GitHub Actions, SARIF, OSV API, CycloneDX, Docker, SQLite, Pytest

## Recommended Two-Bullet Resume Version

- Engineered a DevSecOps supply-chain security platform analyzing npm/Python dependencies, package registries, GitHub Actions workflows and Dockerfiles to detect dependency confusion, insecure registry configurations, unpinned dependencies, secret exposure and CI/CD/container security misconfigurations.
- Implemented static analysis, risk scoring, policy-as-code security gates, SBOM-lite inventory, OSV vulnerability intelligence, SARIF/GitHub Code Scanning integration and a FastAPI/React security dashboard; reduced controlled benchmark findings from 22 to 0 and improved the internal security score from 5/100 to 100/100, with a fixed 100-case adversarial regression corpus reaching 0 FP/FN after remediation.

## Evaluation-Focused Optional Bullet

- Built a deterministic 100-case adversarial evaluation framework across 20 static security rules; identified 14 initial detector mismatches and improved micro F1 from 0.854167 to 1.000000 on the unchanged curated corpus while preserving the independent 22 -> 0 controlled benchmark.

Use the evaluation bullet only when space allows. **Do not shorten it to “100% accurate”**; the 1.000000 result is scoped to the fixed regression corpus.

## Short Project Summary

Built BuildShield-CI, a defensive DevSecOps platform for pre-deployment supply-chain and CI/CD risk analysis with explicit npm/Python/GitHub Actions/Dockerfile analyzers, policy-as-code gating, SARIF/Code Scanning, dependency inventory, OSV intelligence, FastAPI/React dashboarding, SQLite history, reproducible CI gates and hardened Docker deployment.

## Interview-Defensible Metrics

- Controlled vulnerable fixture: 22 findings, score 5/100
- Controlled hardened fixture: 0 findings, score 100/100
- Representative realistic fixture: 3 findings, score 81/100, MEDIUM risk, WARNING gate, policy PASS
- Natural vulnerable-to-realistic comparison: 5 -> 81, 22 -> 3 findings, 80% controlled reduction
- H9 pre-hardening corpus: 41 TP / 45 TN / 4 FP / 10 FN, micro F1 0.854167
- H9 post-hardening unchanged corpus: 51 TP / 49 TN / 0 FP / 0 FN, micro F1 1.000000
- Final pre-release Windows regression: 295 passed, 2 skipped
- Hosted CI on final checkpoint, pull request and post-merge `main`: PASS
- Released version: v1.0.0

The controlled benchmark and curated corpus are not population-level or real-world accuracy measurements.

## Skills Demonstrated

DevSecOps, CI/CD security, software supply-chain security, dependency confusion defense, static analysis, policy-as-code, GitHub Actions security, Docker security, SARIF, GitHub Code Scanning, OSV vulnerability intelligence, CycloneDX SBOM, FastAPI, React/TypeScript, SQLite, reproducible builds, test automation and adversarial evaluation.
