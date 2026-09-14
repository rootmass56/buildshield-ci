# BuildShield-CI Final Demo Script

## Demo Goal

Demonstrate the problem, the scanner, measurable hardening, policy enforcement, vulnerability intelligence, dashboard visibility, GitHub integration, and container deployment.

## 1. Pre-Demo Verification

```powershell
pytest -q
buildshield version
git status --short
```

Expected maintenance baseline:

```text
53 passed
BuildShield-CI version: 0.12.6
working tree clean
```

## 2. Vulnerable Sample

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --hide-files
```

Show:

```text
22 findings
4 Critical
10 High
7 Medium
1 Low
5/100
CRITICAL
Build Gate: FAILED
Policy: FAILED
```

Explain that the sample is intentionally insecure and exists only for controlled demonstration.

## 3. Hardened Sample

```powershell
buildshield scan samples/secure-repo --policy buildshield-policy.yml --hide-files
```

Show:

```text
0 findings
100/100
LOW
Build Gate: PASSED
Policy: PASSED
```

## 4. Comparison

```powershell
buildshield compare samples/vulnerable-repo samples/secure-repo
```

Show:

```text
+95 score
22 findings reduced
100% risk reduction
SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED
```

## 5. Explain Analyzer Coverage

Briefly show that BuildShield-CI analyzes:

- npm dependencies / lockfiles / registries / lifecycle scripts
- Python dependencies / indexes
- GitHub Actions refs, permissions, secrets, remote shell execution, triggers
- Dockerfile base images, user, secrets, remote scripts, upgrades, health checks

Mention that analyzer orchestration is now explicit; legacy dynamic fallback routing was removed and regression-tested.

## 6. SBOM-lite Inventory

```powershell
buildshield inventory samples/vulnerable-repo --hide-packages
```

Explain that the inventory extracts supply-chain dependency metadata and pinning state.

## 7. OSV Intelligence

Offline:

```powershell
buildshield vulncheck samples/secure-repo --offline-plan
```

Online:

```powershell
buildshield vulncheck samples/secure-repo --online --timeout 15
```

Explain that online vulnerability counts are dynamic and should not be hard-coded.

## 8. Dashboard

```powershell
buildshield dashboard --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

Show scanning, findings, policy, reports, inventory, vulnerability intelligence, comparison, history, and trends.

## 9. GitHub Actions Self-Hardening

Show:

```text
.github/workflows/buildshield-ci.yml
```

Explain:

- Workflow runs tests and security gates.
- SARIF is uploaded to GitHub Code Scanning.
- Reports are uploaded as artifacts.
- Third-party actions are pinned to full commit SHAs.
- A regression test prevents mutable action refs.

Optional self-scan:

```powershell
buildshield scan .github --hide-files
```

Expected:

```text
0 findings
100/100
LOW
PASSED
```

## 10. GitHub Code Scanning

Open the repository's Code Scanning page.

Explain clearly that alerts generated from `samples/vulnerable-repo` are intentional demonstration findings.

## 11. Docker

```powershell
docker build -t buildshield-ci:latest .
docker run -d --name buildshield-ci-test -p 8080:8080 buildshield-ci:latest
Invoke-RestMethod http://127.0.0.1:8080/health
docker stop buildshield-ci-test
docker rm buildshield-ci-test
```

Explain:

- Non-root container user
- Health endpoint
- Controlled deployment readiness

## 12. Docker Compose

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8080/health
docker compose down
```

Explain persistent report/data volumes.

## Closing

BuildShield-CI combines static analysis, scoring, policy-as-code, SARIF, Code Scanning, dependency inventory, OSV intelligence, dashboard/history, CI/CD hardening, Docker deployment, and automated regression testing.

For enterprise production use, additional authentication, authorization, isolation, secret-management, observability, and operational hardening would still be required.
