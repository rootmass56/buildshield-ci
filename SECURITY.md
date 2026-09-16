# Security Policy

## Scope

BuildShield-CI is a defensive DevSecOps and software supply-chain security project. Security reports should relate to the BuildShield-CI implementation itself, its CI/CD workflow, API/dashboard behavior, packaging, deployment configuration, or repository security controls.

The intentionally vulnerable fixtures under `samples/vulnerable-repo` are **not** security defects in BuildShield-CI. They are controlled test data used to validate detection rules, policy behavior, SARIF output and before/after demonstrations.

## Supported Versions

The current supported release line is:

| Version | Supported |
|---|---|
| `v1.0.0` | Yes |
| `v0.12.7` | Historical baseline only |
| Older versions | No |

For the authoritative released state, use the `v1.0.0` tag and published GitHub release. The default `main` branch may contain documentation-only or corrective maintenance after that tag.

## Reporting a Vulnerability

Please avoid publishing sensitive exploit details, credentials, tokens, private data, or weaponized proof-of-concept material in a public issue.

Preferred reporting flow:

1. If GitHub Private Vulnerability Reporting or a repository Security Advisory reporting option is available, use that private channel.
2. If no private GitHub security-reporting option is available, open a minimal GitHub issue stating that you want to report a potential security vulnerability and request a private follow-up channel.
3. Include only non-sensitive triage information in the public issue.

Useful triage information includes:

- affected component or file
- affected version/commit
- security impact
- reproduction prerequisites
- minimal safe reproduction steps
- expected behavior
- observed behavior
- suggested remediation, if known

Do not include live credentials, secrets, personal data, or destructive payloads.

## Safe Research Expectations

Keep testing limited to systems, repositories, accounts and environments you own or are explicitly authorized to test.

Do not:

- attack third-party infrastructure
- publish malicious packages
- abuse public package registries
- exfiltrate secrets or credentials
- perform destructive testing
- attempt denial-of-service testing
- use BuildShield-CI as authorization to test unrelated systems

A report should demonstrate the minimum behavior needed to establish the issue safely.

## Controlled Vulnerable Samples

The intentionally insecure fixture is:

```text
samples/vulnerable-repo/
```

It exists to exercise rules such as:

- dependency-confusion indicators
- missing lockfiles / loose dependency versions
- risky lifecycle scripts
- insecure GitHub Actions patterns
- secret-echo examples
- risky Dockerfile configuration

GitHub Code Scanning alerts generated from this fixture are expected demonstration findings.

The hardened fixture is:

```text
samples/secure-repo/
```

Its controlled static-analysis benchmark is expected to produce no BuildShield-CI configuration findings. This does **not** guarantee that dependencies will never have externally reported vulnerabilities; OSV intelligence is dynamic.

The representative mixed-posture fixture is:

```text
samples/realistic-repo/
```

It is used for routine demonstrations and intentionally retains a small number of non-critical findings so normal application posture is not represented as artificially perfect.

## Security Model and Limitations

BuildShield-CI performs passive static analysis and heuristic detection. It does not claim to provide complete vulnerability coverage, replace a full security program, or prove that a repository is secure.

The released `v1.0.0` architecture is suitable for controlled single-instance environments and production-style demonstrations. It includes focused single-tenant authentication/authorization, workspace containment, request/resource controls, audit logging, retention controls and hardened container runtime settings.

Enterprise or organization-wide deployment would require additional controls appropriate to that environment, especially for multi-tenant or distributed use, such as:

- external identity-provider integration, stronger RBAC and lifecycle governance
- tenant/repository isolation appropriate to the deployment model
- centralized secret management and rotation
- production TLS termination, network segmentation and edge controls
- distributed/shared rate limiting when multiple instances are introduced
- centralized observability, alerting and log retention
- backup, recovery and disaster-recovery procedures
- operational monitoring and incident-response processes
- dependency, base-image and container-image lifecycle management

## Release Security Evidence

Before `v1.0.0` was released, the final state passed:

- full Windows regression: **295 passed, 2 skipped**
- Ruff: **PASS**
- mypy typed-boundary gate: **PASS**
- `pip check`: **PASS**
- exact Node 22.23.2 / npm 12.0.2 frontend gates: **PASS**
- production Docker/API smoke: **PASS**
- authenticated live-browser review: **PASS**
- repository sanitation: **PASS**
- hosted GitHub Actions on the final checkpoint, pull request and merged `main`: **PASS**

The H9 deterministic evaluation result of precision/recall/F1 = 1.000000 is scoped only to the fixed curated 100-case regression corpus. It is not a claim of 100% real-world detection accuracy.

## Disclosure

Please allow reasonable time for validation and remediation before public disclosure of a confirmed vulnerability.

Reports concerning the intentionally vulnerable sample fixtures may be closed as expected behavior when they do not affect the BuildShield-CI implementation itself.
