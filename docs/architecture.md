# BuildShield-CI Architecture

## 1. Overview

BuildShield-CI is an advanced CI/CD supply-chain security analyzer. It performs static analysis of repository files and identifies security weaknesses related to dependency confusion, insecure package usage, weak GitHub Actions configurations, risky build scripts, and policy violations.

The tool is designed for both local security assessment and automated DevSecOps pipeline enforcement.

---

## 2. High-Level Architecture

```text
Repository
   |
   v
File Discovery Engine
   |
   v
Analyzer Layer
   |-- npm Analyzer
   |-- Python Analyzer
   |-- GitHub Actions Analyzer
   |
   v
Finding Model
   |
   v
Risk Scoring Engine
   |
   v
Policy-as-Code Engine
   |
   v
Report Generation Layer
   |-- Terminal Output
   |-- JSON Report
   |-- Markdown Report
   |-- HTML Report
   |-- SARIF Report
   |
   v
CI/CD Integration
   |-- GitHub Actions
   |-- Artifact Upload
   |-- SARIF Code Scanning
```

---

## 3. Component Breakdown

### 3.1 CLI Layer

Location:

```text
src/supplysentinel/cli.py
```

Responsibilities:

- Provides `buildshield` command
- Supports scanning repositories
- Supports comparison between vulnerable and secure repositories
- Supports policy-as-code evaluation
- Supports report generation
- Supports CI/CD-compatible exit codes

Main commands:

```powershell
buildshield scan <target>
buildshield compare <baseline> <target>
buildshield version
```

---

### 3.2 File Discovery Engine

Location:

```text
src/supplysentinel/core/scanner.py
```

Responsibilities:

- Walks the repository directory
- Identifies security-relevant files
- Detects files such as:
  - `package.json`
  - `package-lock.json`
  - `requirements.txt`
  - `.npmrc`
  - `pip.conf`
  - `.github/workflows/*.yml`

---

### 3.3 Analyzer Layer

Location:

```text
src/supplysentinel/analyzers/
```

Analyzers:

| Analyzer | Purpose |
|---|---|
| npm Analyzer | Detects npm dependency and registry risks. |
| Python Analyzer | Detects Python dependency and package index risks. |
| GitHub Actions Analyzer | Detects CI/CD workflow risks. |

---

## 4. Detection Rules

### npm Rules

| Rule ID | Description |
|---|---|
| DG-NPM-001 | Missing npm lockfile |
| DG-NPM-002 | Loose npm dependency version |
| DG-NPM-003 | Risky npm lifecycle script |
| DG-NPM-004 | Potential npm dependency confusion risk |

### Python Rules

| Rule ID | Description |
|---|---|
| DG-PY-001 | Unpinned Python dependency |
| DG-PY-002 | Loose Python dependency version |
| DG-PY-003 | Potential Python dependency confusion risk |

### GitHub Actions Rules

| Rule ID | Description |
|---|---|
| DG-GHA-001 | GitHub Action not pinned to full commit SHA |
| DG-GHA-002 | Over-permissive GitHub Actions token permissions |
| DG-GHA-003 | Remote script piped directly to shell |
| DG-GHA-004 | Secret value printed in workflow |
| DG-GHA-005 | Use of pull_request_target trigger |

---

## 5. Risk Scoring Architecture

Location:

```text
src/supplysentinel/core/scoring.py
```

The risk scoring engine converts findings into a security score.

### Inputs

- Finding severity
- Finding category
- Confidence
- Number of findings
- Category risk caps

### Outputs

- Overall security score
- Risk level
- Build gate status
- Build gate reason
- Category-wise risk breakdown
- Top risk drivers

### Example

```text
Vulnerable repository:
Security Score: 5/100
Risk Level: CRITICAL
Build Gate Status: FAILED

Secure repository:
Security Score: 100/100
Risk Level: LOW
Build Gate Status: PASSED
```

---

## 6. Policy-as-Code Engine

Location:

```text
src/supplysentinel/policies/policy_engine.py
```

Policy file:

```text
buildshield-policy.yml
```

The policy engine checks whether the repository satisfies defined security requirements.

Example policy controls:

- Minimum security score
- Maximum allowed critical findings
- Maximum allowed high findings
- Require npm lockfiles
- Require pinned GitHub Actions
- Block secret echoing
- Block `curl | bash`
- Block dependency confusion risks
- Block risky `pull_request_target`

CI/CD behavior:

```text
Policy passed -> exit code 0
Policy failed -> exit code 2
```

---

## 7. Reporting Architecture

Location:

```text
src/supplysentinel/reporters/
```

Report types:

| Format | Purpose |
|---|---|
| JSON | Automation and machine-readable output |
| Markdown | Documentation and readable reports |
| HTML | Professional visual report |
| SARIF | GitHub Code Scanning integration |

---

## 8. SARIF Integration

Location:

```text
src/supplysentinel/reporters/sarif_reporter.py
```

BuildShield-CI generates SARIF 2.1.0 output and uploads it to GitHub Code Scanning through GitHub Actions.

SARIF output file:

```text
reports/buildshield-results.sarif
```

GitHub location:

```text
Security and quality → Code scanning
```

---

## 9. CI/CD Architecture

Location:

```text
.github/workflows/buildshield-ci.yml
```

The workflow performs:

1. Checkout repository
2. Set up Python
3. Install BuildShield-CI
4. Validate CLI
5. Run automated tests
6. Run secure repo policy gate
7. Demonstrate vulnerable repo policy failure
8. Generate JSON, Markdown, HTML reports
9. Generate SARIF
10. Upload SARIF to GitHub Code Scanning
11. Upload reports as artifacts

---

## 10. Testing Architecture

Location:

```text
tests/
```

Test coverage:

| Test File | Purpose |
|---|---|
| test_scan_engine.py | Validates detection engine |
| test_policy_engine.py | Validates policy pass/fail |
| test_comparison_engine.py | Validates before/after comparison |
| test_reporters.py | Validates report generation and SARIF |
| test_cli.py | Validates CLI and exit codes |

Expected test result:

```text
12 passed
```

---

## 11. Security Design Principles

BuildShield-CI follows these principles:

- Passive static analysis only
- No exploit execution
- No malware generation
- No credential collection
- No unauthorized scanning
- Safe vulnerable sample repository
- Policy-as-code enforcement
- CI/CD shift-left security
- Evidence-based findings
- Remediation-focused reporting

---

## 12. Limitations

Current limitations:

- Static analysis only
- No live package registry API validation
- No SBOM generation yet
- No CVE database integration yet
- No enterprise dashboard yet
- No multi-language support beyond npm, Python, and GitHub Actions

---

## 13. Future Enhancements

Planned enhancements:

- FastAPI backend
- React frontend dashboard
- SBOM generation
- OSV vulnerability database integration
- Package registry reputation checks
- Dockerfile analyzer
- Kubernetes manifest analyzer
- GitLab CI analyzer
- PDF report export
- Enterprise policy profiles