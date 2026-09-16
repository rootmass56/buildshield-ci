# BuildShield-CI Interview Explanation

## 30-Second Explanation

BuildShield-CI is a DevSecOps supply-chain security platform that statically analyzes npm/Python dependencies, registry configuration, GitHub Actions workflows and Dockerfiles before deployment. It normalizes findings, calculates risk, enforces policy-as-code, generates SARIF for GitHub Code Scanning, adds dependency inventory and OSV intelligence, exposes results through FastAPI plus a React/TypeScript dashboard, stores history in SQLite and supports a hardened Docker deployment.

## 1-Minute Explanation

I built BuildShield-CI to catch software supply-chain and CI/CD configuration risks before deployment. The scanner discovers relevant files and routes them explicitly to four canonical analyzer families. The analyzers produce structured findings with severity, evidence, impact and remediation. The platform then calculates a security score and build-gate decision, evaluates YAML policy, creates JSON/Markdown/HTML/SARIF reports, supports GitHub Code Scanning, produces dependency inventory, optionally queries OSV, stores scan history and trends, and exposes the workflow through a FastAPI backend and React/TypeScript dashboard.

The project also hardens its own delivery path with hash-locked Python dependencies, an exact Node/npm frontend baseline, immutable GitHub Actions references, fresh wheel verification, CycloneDX 1.6 SBOM checks and a non-root/read-only Docker runtime.

## Architecture Point to Explain

A key engineering improvement was removing dynamic analyzer-name guessing and hidden fallback analyzers. The scanner now calls canonical npm, Python, GitHub Actions and Dockerfile analyzer interfaces explicitly, making routing deterministic and easier to test.

## Controlled Benchmark

The intentionally vulnerable fixture produces 22 findings, a 5/100 score, CRITICAL risk and a failed build/policy gate. The hardened fixture produces 0 static configuration findings, a 100/100 score, LOW risk and passing gates. The +95 score and 22-finding reduction are controlled benchmark results, not a universal security guarantee.

## Representative Realistic Demo

For normal demonstrations, I use a mixed-posture repository rather than always comparing a deliberately broken project with a perfect fixture. The realistic application produces 3 findings (2 Medium, 1 Low), an 81/100 score, MEDIUM risk, a WARNING build gate and passing policy. Comparing the vulnerable benchmark to that realistic application improves the score from 5 to 81 and reduces findings from 22 to 3, an 80% controlled reduction. The 100/100 hardened fixture remains a regression endpoint, not a claim that every healthy repository should score perfectly.

## H9 Evaluation Answer

A strong interview explanation is:

> I first evaluated the unchanged 100-case deterministic adversarial corpus and measured 41 TP, 45 TN, 4 FP and 10 FN, which was a micro F1 of 0.854167. I then fixed the 14 identified detector mismatches without changing the oracle or fixture corpus. The final regression result was 51 TP, 49 TN, 0 FP and 0 FN, so precision, recall and F1 are 1.0 on that fixed corpus. I explicitly do not present that as 100% real-world detection accuracy; it is regression evidence on a curated deterministic test set.

## Why Dependency Confusion Matters

Dependency confusion can occur when an internal-looking package name is resolved from an unintended public registry. BuildShield-CI uses static heuristics around package names and private-registry/index configuration; it does not publish packages or attempt registry takeover.

## Why Pin GitHub Actions

Tags and branches are mutable. Pinning third-party actions to full commit SHAs improves reproducibility and reduces supply-chain risk from mutable references. BuildShield-CI also tests its own workflow for immutable action references.

## Why SARIF and Policy-as-Code

SARIF makes findings consumable by GitHub Code Scanning. Policy-as-code converts findings into deterministic CI decisions, allowing organizations to define when a build should fail instead of relying only on a numeric score.

## SBOM and OSV

The project has two related but distinct supply-chain views: repository inventory/SBOM-lite for discovered package metadata, and a CycloneDX 1.6 runtime SBOM for the BuildShield-CI release environment. OSV lookup is external intelligence and is intentionally kept separate from the deterministic static-rule metrics.

## Deployment Answer

The v1.0.0 release candidate is positioned for controlled single-instance deployment and production-style demonstrations. Production configuration fails closed if required administrator authentication/workspace settings are missing. The Compose runtime uses a numeric non-root user, read-only root filesystem, dropped capabilities, `no-new-privileges`, bounded PID/tmpfs controls, localhost-only publication and separate liveness/readiness checks. I would not describe it as enterprise multi-tenant SaaS without additional identity/RBAC, tenant isolation, centralized secrets, TLS/networking, observability, backup/recovery and operational controls.

## Current Automated Validation

The final post-checkpoint pre-release candidate completed:

```text
295 passed, 2 skipped
```

It also passed the exact Node 22.23.2 / npm 12.0.2 frontend gates, Ruff, production Docker/API smoke, the realistic 81/100 profile contract, natural 5 -> 81 comparison, the preserved 22 -> 0 controlled benchmark, live browser review and final repository sanitation. The project remains a release candidate until the replacement final checkpoint passes hosted CI and the PR/tag/release sequence completes.

## Strong Resume/Interview Summary

BuildShield-CI demonstrates practical engineering across DevSecOps, application security, CI/CD hardening, software supply-chain security, static analysis, policy-as-code, SARIF, vulnerability intelligence, React/FastAPI application development, persistence, reproducible builds, Docker hardening and adversarial regression testing.
