# BuildShield-CI Final Demo Script

## Demo Goal

Demonstrate the security problem, BuildShield-CI's static-analysis workflow, controlled hardening result, deterministic evaluation, policy enforcement, supply-chain intelligence, dashboard visibility, GitHub integration and hardened container deployment.

## 1. Pre-Demo Verification

```powershell
pytest -q
buildshield version
git status --short
```

Expected release-candidate baseline:

```text
295 passed, 2 skipped
BuildShield-CI version: 1.0.0
working tree contains only the reviewed final post-checkpoint candidate before the replacement release checkpoint
```

After the final H10D release checkpoint, use a clean tree for the public demo.

## 2. Realistic Application Profile

```powershell
buildshield scan samples/realistic-repo --policy buildshield-policy.yml --hide-files
```

Show:

```text
3 findings
0 Critical
0 High
2 Medium
1 Low
81/100
MEDIUM
Build Gate: WARNING
Policy: PASSED
```

Explain that this is the normal representative demo: a mostly hardened application with a small number of dependency/container findings. It avoids presenting a perfect 100/100 score as the expected outcome for every application.

Natural comparison:

```powershell
buildshield compare samples/vulnerable-repo samples/realistic-repo
```

Show +76 score, 19 findings reduced and 80% controlled risk reduction with `PARTIALLY_IMPROVED`.

## 3. Vulnerable Benchmark Sample

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

Explain that the repository is intentionally insecure and exists only for controlled demonstration and regression testing.

## 4. Hardened Benchmark Sample

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

## 5. Controlled Benchmark Comparison

```powershell
buildshield compare samples/vulnerable-repo samples/secure-repo
```

Show the +95 score change, 22 findings reduced and `SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED`. Describe the 100% reduction only as the result of this controlled benchmark.

## 6. Explain the 20 Static Rules

Summarize the four analyzer families:

- npm: lockfile, version ranges, lifecycle scripts and dependency-confusion indicators
- Python: pinning/version ranges and package-index/dependency-confusion indicators
- GitHub Actions: immutable action refs, permissions, remote shell execution, secret logging and `pull_request_target` risk
- Dockerfile: base-image pinning, final-stage user semantics, explicit root, secret-like ENV/ARG use, remote shell execution, package upgrades, health checks and remote-URL `ADD`

## 7. Deterministic H9 Evaluation

Show `docs/evaluation-metrics.md` and `evaluation/h9d-final-metrics-v1.json`.

Explain the before/after result on the same fixed 100-case corpus:

```text
H9C: 41 TP / 45 TN / 4 FP / 10 FN, micro F1 0.854167
H9D: 51 TP / 49 TN / 0 FP / 0 FN, micro F1 1.000000
```

State explicitly that 1.000000 is regression performance on the curated corpus, not a claim of perfect real-world detection.

## 8. Inventory and OSV Intelligence

```powershell
buildshield inventory samples/vulnerable-repo --hide-packages
buildshield vulncheck samples/secure-repo --offline-plan
```

Optional network-dependent lookup:

```powershell
buildshield vulncheck samples/secure-repo --online --timeout 15
```

Explain that online OSV results are dynamic and are not hard-coded into the deterministic static-rule metrics.

## 9. Dashboard

For a local development demonstration:

```powershell
buildshield dashboard --port 8080
```

Open `http://127.0.0.1:8080` and show scanning, findings, policy, comparison, inventory, vulnerability intelligence, reports, history and trends. The normal scanner preset should be the Realistic Application Repository (81/100, 3 findings), while the vulnerable and hardened fixtures remain benchmark presets.

## 10. GitHub Actions and Code Scanning

Show `.github/workflows/buildshield-ci.yml` and explain:

- immutable full-SHA third-party action pins
- Python quality/reproducibility gates
- exact Node 22.23.2 / npm 12.0.2 frontend gates
- controlled vulnerable/secure policy assertions
- SARIF upload to GitHub Code Scanning
- report artifacts

Alerts from the intentionally vulnerable fixture are demonstration findings, not proof that BuildShield-CI source itself is vulnerable.

## 11. Production-Style Docker Compose Demo

Production mode fails closed unless administrator authentication is configured. Generate an ephemeral demo hash without committing it:

```powershell
$env:BUILDSHIELD_ADMIN_USERNAME = "admin"
$env:BUILDSHIELD_ADMIN_PASSWORD_HASH = python -c "from supplysentinel.web.auth import hash_password; import getpass; print(hash_password(getpass.getpass('Admin password: ')))"
$env:BUILDSHIELD_COOKIE_SECURE = "false"
$env:BUILDSHIELD_HOST_PORT = "18080"

docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:18080/health
Invoke-RestMethod http://127.0.0.1:18080/ready
docker compose down
```

Explain the non-root UID/GID, read-only root filesystem, dropped Linux capabilities, `no-new-privileges`, bounded PID/tmpfs settings, localhost-only publication, persistent report/data volumes, liveness/readiness separation and graceful shutdown.

Never commit the generated password hash.

## Closing

BuildShield-CI combines supply-chain static analysis, policy-as-code, risk scoring, SARIF/Code Scanning, inventory, OSV intelligence, dashboard/history, reproducible CI/CD quality gates, deterministic adversarial evaluation and hardened container deployment.

The project's claims remain bounded: controlled benchmark results and curated regression-corpus metrics are evidence for the tested scenarios, not universal guarantees of repository security or real-world detection accuracy.
