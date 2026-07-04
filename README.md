# BuildShield-CI

![BuildShield-CI Security Gate](https://github.com/rootmass56/buildshield-ci/actions/workflows/buildshield-ci.yml/badge.svg)

**BuildShield-CI** is an advanced CI/CD supply-chain risk analyzer and dependency confusion defense platform. It scans repositories for dependency confusion risks, insecure dependency declarations, risky package lifecycle scripts, weak GitHub Actions configurations, secret exposure patterns, and CI/CD policy violations.

The tool is designed as a DevSecOps security gate that can run locally or inside GitHub Actions.

---

## Project Objective

Modern software projects rely heavily on open-source packages, private package registries, and CI/CD workflows. Misconfigurations in these areas can introduce serious software supply-chain risks.

BuildShield-CI helps detect and prevent these risks before code reaches production by providing:

- Static repository scanning
- Dependency confusion risk detection
- npm and Python dependency analysis
- GitHub Actions workflow hardening checks
- Policy-as-code enforcement
- Security scoring
- SARIF output for GitHub Code Scanning
- JSON, Markdown, and HTML report generation
- CI/CD pipeline integration

---

## Key Features

| Feature | Description |
|---|---|
| npm Dependency Analysis | Detects missing lockfiles, loose dependency versions, risky lifecycle scripts, and scoped package registry risks. |
| Python Dependency Analysis | Detects unpinned requirements, loose versions, and potential internal package confusion risks. |
| GitHub Actions Analysis | Detects unpinned actions, over-permissive permissions, `curl | bash`, secret echoing, and risky triggers. |
| Advanced Risk Scoring | Produces a 0-100 security score with risk level, category risk, and top risk drivers. |
| Policy-as-Code | Reads YAML policy rules and fails builds when security thresholds are violated. |
| CI/CD Integration | Runs automatically through GitHub Actions on push, pull request, and manual workflow dispatch. |
| Report Generation | Generates JSON, Markdown, HTML, and SARIF reports. |
| GitHub Code Scanning | Uploads SARIF findings into GitHub Security → Code scanning. |
| Secure vs Vulnerable Demo | Includes sample vulnerable and hardened repositories for measurable before/after comparison. |
| Automated Tests | Includes pytest-based validation for scanner, policy, reporter, SARIF, and CLI behavior. |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| CLI Framework | Typer |
| Terminal UI | Rich |
| Data Models | Pydantic |
| Policy Format | YAML |
| CI/CD | GitHub Actions |
| Reports | JSON, Markdown, HTML, SARIF |
| Testing | pytest |
| Repository Hosting | GitHub |

---

## Repository Structure

```text
buildshield-ci/
├── .github/
│   └── workflows/
│       └── buildshield-ci.yml
├── docs/
│   ├── architecture.md
│   ├── demo-script.md
│   ├── final-report.md
│   ├── research-log.md
│   └── screenshots-checklist.md
├── reports/
├── samples/
│   ├── secure-repo/
│   └── vulnerable-repo/
├── src/
│   └── supplysentinel/
│       ├── analyzers/
│       ├── core/
│       ├── parsers/
│       ├── policies/
│       └── reporters/
├── tests/
├── buildshield-policy.yml
├── pyproject.toml
└── README.md
```

---

## Installation

Clone the repository:

```powershell
git clone https://github.com/rootmass56/buildshield-ci.git
cd buildshield-ci
```

Create virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
pip install -e .
```

Verify installation:

```powershell
buildshield --help
buildshield version
```

Expected:

```text
BuildShield-CI version: 0.10.0
```

---

## Usage

### Scan vulnerable repository

```powershell
buildshield scan samples/vulnerable-repo
```

### Scan secure repository

```powershell
buildshield scan samples/secure-repo
```

### Apply policy-as-code

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml
```

### Fail build when policy fails

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --fail-on-policy
```

Expected exit code:

```text
2
```

### Secure repository policy gate

```powershell
buildshield scan samples/secure-repo --policy buildshield-policy.yml --fail-on-policy
```

Expected exit code:

```text
0
```

---

## Generate Reports

### JSON report

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --report-format json --output reports/vulnerable-policy-report.json
```

### Markdown report

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --report-format md --output reports/vulnerable-policy-report.md
```

### HTML report

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --report-format html --output reports/vulnerable-policy-report.html
```

### SARIF report

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --report-format sarif --output reports/buildshield-results.sarif
```

---

## Compare Vulnerable and Secure Repositories

```powershell
buildshield compare samples/vulnerable-repo samples/secure-repo
```

Generate comparison report:

```powershell
buildshield compare samples/vulnerable-repo samples/secure-repo --report-format html --output reports/comparison-report.html
```

---

## Policy-as-Code

BuildShield-CI uses `buildshield-policy.yml`:

```yaml
minimum_score: 80

fail_on:
  - CRITICAL

max_allowed:
  critical: 0
  high: 0
  medium: 10
  low: 20

blocked_rules: []

rules:
  require_lockfiles: true
  require_pinned_actions: true
  block_write_all_permissions: true
  block_secret_echo: true
  block_curl_pipe_shell: true
  block_dependency_confusion: true
  block_pull_request_target: true
```

This policy enforces:

- Minimum score of 80
- No critical findings
- No high findings
- Lockfile requirement
- Pinned GitHub Actions
- Least-privilege GitHub token permissions
- No direct secret echoing
- No direct remote script pipe-to-shell execution
- No dependency confusion indicators

---

## GitHub Actions CI/CD Integration

BuildShield-CI runs automatically through GitHub Actions.

Workflow file:

```text
.github/workflows/buildshield-ci.yml
```

The pipeline performs:

1. Checkout repository
2. Set up Python
3. Install BuildShield-CI
4. Validate CLI
5. Run automated tests
6. Run secure repository policy gate
7. Demonstrate vulnerable repository policy failure
8. Generate security reports
9. Generate SARIF
10. Upload SARIF to GitHub Code Scanning
11. Upload JSON, Markdown, HTML, and SARIF reports as artifacts

---

## GitHub Code Scanning

BuildShield-CI generates SARIF 2.1.0 output and uploads it to GitHub Code Scanning.

Location:

```text
GitHub → Security and quality → Code scanning
```

The intentionally vulnerable sample repository produces alerts such as:

- Secret value printed in workflow
- Potential npm dependency confusion risk
- Remote script piped directly to shell
- GitHub Action not pinned to full commit SHA
- Over-permissive GitHub Actions token permissions
- Risky npm lifecycle script
- Potential Python dependency confusion risk

---

## Testing

Run tests locally:

```powershell
pytest -q
```

Expected:

```text
12 passed
```

Tests cover:

- Scan engine
- Policy engine
- Comparison engine
- JSON, Markdown, HTML reporters
- SARIF reporter
- CLI exit-code behavior

---

## Example Results

| Repository | Security Score | Risk Level | Policy Status | Exit Code |
|---|---:|---|---|---:|
| Vulnerable Repo | 5/100 | Critical | Failed | 2 |
| Secure Repo | 100/100 | Low | Passed | 0 |

---

## Security and Ethical Scope

BuildShield-CI performs passive static analysis only.

It does not:

- Exploit systems
- Download malware
- Execute third-party packages
- Steal credentials
- Perform network attacks
- Upload malicious packages
- Access private repositories without permission

The vulnerable repository is a controlled sample created only for demonstration and testing.

---

## Project Status

Completed stages:

- Project foundation
- Detection engine
- Risk scoring engine
- Secure vs vulnerable comparison
- Report generation
- Policy-as-code gate
- GitHub Actions CI/CD integration
- SARIF output and GitHub Code Scanning
- Automated test suite
- BuildShield-CI branding and CLI alias
- Final documentation package

---

## Author

**Saketh**  
GitHub: `rootmass56`

---

## License

This project is built for academic, internship, and portfolio demonstration purposes.