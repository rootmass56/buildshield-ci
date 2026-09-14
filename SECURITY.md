# Security Policy

## Scope

BuildShield-CI is a defensive DevSecOps and software supply-chain security project. Security reports should relate to the BuildShield-CI implementation itself, its CI/CD workflow, API/dashboard behavior, packaging, deployment configuration, or repository security controls.

The intentionally vulnerable fixtures under `samples/vulnerable-repo` are **not** security defects in BuildShield-CI. They are controlled test data used to validate detection rules, policy behavior, SARIF output, and before/after demonstrations.

## Supported Versions

Security fixes are applied to the current maintained release line and the active development branch as appropriate. Older historical tags may not receive backported fixes.

For the authoritative current version, use the latest release/tag and the repository's `main` branch.

## Reporting a Vulnerability

Please avoid publishing sensitive exploit details, credentials, tokens, private data, or weaponized proof-of-concept material in a public issue.

Preferred reporting flow:

1. If GitHub Private Vulnerability Reporting or a repository Security Advisory reporting option is available, use that private channel.
2. If no private GitHub security-reporting option is available, open a minimal GitHub issue stating that you want to report a potential security vulnerability and request a private follow-up channel.
3. Include only non-sensitive triage information in the public issue.

Useful triage information includes:

- Affected component or file
- Affected version/commit
- Security impact
- Reproduction prerequisites
- Minimal safe reproduction steps
- Expected behavior
- Observed behavior
- Suggested remediation, if known

Do not include live credentials, secrets, personal data, or destructive payloads.

## Safe Research Expectations

Please keep testing limited to systems, repositories, accounts, and environments you own or are explicitly authorized to test.

Do not:

- Attack third-party infrastructure
- Publish malicious packages
- Abuse public package registries
- Exfiltrate secrets or credentials
- Perform destructive testing
- Attempt denial-of-service testing
- Use BuildShield-CI as authorization to test unrelated systems

A report should demonstrate the minimum behavior needed to establish the issue safely.

## Controlled Vulnerable Samples

The following content is intentionally insecure:

```text
samples/vulnerable-repo/
```

It exists to exercise rules such as:

- Dependency confusion indicators
- Missing lockfiles / loose dependency versions
- Risky lifecycle scripts
- Insecure GitHub Actions patterns
- Secret-echo examples
- Risky Dockerfile configuration

GitHub Code Scanning alerts generated from this fixture are expected demonstration findings.

The hardened fixture is:

```text
samples/secure-repo/
```

Its controlled static-analysis benchmark is expected to produce no BuildShield-CI configuration findings. This does **not** guarantee that the dependencies will never have externally reported vulnerabilities; OSV intelligence is dynamic.

## Security Model and Limitations

BuildShield-CI performs passive static analysis and heuristic detection. It does not claim to provide complete vulnerability coverage or prove that a repository is secure.

The current platform is suitable for controlled environments and production-style demonstrations. Enterprise deployment would require additional controls such as:

- Authentication and authorization
- Tenant/repository isolation
- Secret management
- TLS and network hardening
- Rate limiting and resource controls
- Audit logging
- Centralized observability
- Backup and recovery
- Operational monitoring and incident response
- Dependency and container-image lifecycle management

## Disclosure

Please allow reasonable time for validation and remediation before public disclosure of a confirmed vulnerability.

Reports concerning the intentionally vulnerable sample fixtures may be closed as expected behavior when they do not affect the BuildShield-CI implementation itself.
