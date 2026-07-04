# BuildShield-CI Final Project Report

## 1. Executive Overview

BuildShield-CI is an advanced CI/CD supply-chain risk analyzer and dependency confusion defense platform. The project focuses on detecting security weaknesses that commonly appear in modern software delivery pipelines, especially around dependency management, private package usage, GitHub Actions workflow security, and policy enforcement.

The project was designed as a DevSecOps security tool that can run locally and inside GitHub Actions. It generates machine-readable and human-readable security reports, enforces policy-as-code, uploads SARIF results to GitHub Code Scanning, and demonstrates measurable improvement between a vulnerable repository and a hardened repository.

---

## 2. Problem Statement

Modern development teams rely on external packages, private registries, automation workflows, and CI/CD pipelines. These systems introduce supply-chain risks such as:

- Dependency confusion
- Unpinned dependencies
- Missing lockfiles
- Risky package lifecycle scripts
- Over-permissive CI/CD tokens
- Remote script execution in workflows
- Secret exposure in workflow logs
- Unsafe `pull_request_target` usage
- Lack of automated policy enforcement

BuildShield-CI addresses these risks by statically analyzing repository configuration files and enforcing security rules before code reaches production.

---

## 3. Objectives

The main objectives of BuildShield-CI are:

1. Detect dependency confusion indicators in npm and Python projects.
2. Detect insecure dependency declarations.
3. Detect risky CI/CD workflow patterns.
4. Generate evidence-backed findings with severity and remediation.
5. Calculate an advanced risk score.
6. Enforce policy-as-code security gates.
7. Integrate with GitHub Actions.
8. Upload SARIF findings to GitHub Code Scanning.
9. Generate JSON, Markdown, and HTML reports.
10. Provide a secure vs vulnerable comparison demonstration.
11. Validate the system using automated tests.

---

## 4. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.13 |
| CLI Framework | Typer |
| Terminal Output | Rich |
| Data Validation | Pydantic |
| Policy Format | YAML |
| CI/CD | GitHub Actions |
| Reports | JSON, Markdown, HTML, SARIF |
| Testing | pytest |
| Hosting | GitHub |

---

## 5. System Architecture

```text
Repository
   |
   v
File Discovery Engine
   |
   v
Static Analyzers
   |-- npm Analyzer
   |-- Python Analyzer
   |-- GitHub Actions Analyzer
   |
   v
Finding Normalization
   |
   v
Risk Scoring Engine
   |
   v
Policy-as-Code Engine
   |
   v
Report Generation
   |-- Terminal
   |-- JSON
   |-- Markdown
   |-- HTML
   |-- SARIF
   |
   v
GitHub Actions CI/CD
   |
   v
Artifacts + GitHub Code Scanning
```

---

## 6. Implemented Features

### 6.1 npm Analyzer

The npm analyzer detects:

- Missing `package-lock.json`
- Loose dependency versions such as `^` or `~`
- Risky lifecycle scripts such as `preinstall` and `postinstall`
- Potential dependency confusion risk for scoped/internal packages without private registry configuration

### 6.2 Python Analyzer

The Python analyzer detects:

- Unpinned Python dependencies
- Loose Python dependency version specifiers
- Potential internal package confusion risk when private package handling is not configured

### 6.3 GitHub Actions Analyzer

The GitHub Actions analyzer detects:

- Actions not pinned to full commit SHA
- Over-permissive `permissions: write-all`
- Remote script piping such as `curl | bash`
- Secret echoing in workflow logs
- Risky `pull_request_target` triggers

### 6.4 Risk Scoring Engine

The scoring engine produces:

- Overall security score
- Risk level
- Build gate status
- Build gate reason
- Category-wise risk breakdown
- Top risk drivers

### 6.5 Policy-as-Code Engine

The policy engine reads `buildshield-policy.yml` and checks:

- Minimum security score
- Maximum allowed findings by severity
- Blocked security controls
- Required lockfiles
- Pinned GitHub Actions
- Secret echo prevention
- Dependency confusion prevention

### 6.6 Report Generation

Supported report formats:

- JSON
- Markdown
- HTML
- SARIF

### 6.7 GitHub Actions Integration

BuildShield-CI is integrated with GitHub Actions to run automatically on:

- Push
- Pull request
- Manual workflow dispatch

The workflow:

- Installs the tool
- Runs tests
- Applies policy
- Generates reports
- Uploads SARIF to GitHub Code Scanning
- Uploads reports as artifacts

### 6.8 Automated Testing

The test suite validates:

- Scanner behavior
- Policy pass/fail behavior
- Comparison logic
- Report generation
- SARIF generation
- CLI exit codes

Current result:

```text
12 passed
```

---

## 7. Demonstration Results

### Vulnerable Repository

| Metric | Result |
|---|---:|
| Security Score | 5/100 |
| Risk Level | Critical |
| Findings | 15 |
| Policy Status | Failed |
| CI/CD Exit Code | 2 |

### Secure Repository

| Metric | Result |
|---|---:|
| Security Score | 100/100 |
| Risk Level | Low |
| Findings | 0 |
| Policy Status | Passed |
| CI/CD Exit Code | 0 |

### Before vs After

| Metric | Vulnerable Repo | Secure Repo | Improvement |
|---|---:|---:|---:|
| Security Score | 5/100 | 100/100 | +95 |
| Findings | 15 | 0 | -15 |
| Critical Findings | 2 | 0 | -2 |
| High Findings | 6 | 0 | -6 |
| Policy Status | Failed | Passed | Improved |

---

## 8. Screenshots to Include

The final submission should include screenshots of:

1. Local vulnerable repository scan
2. Local secure repository scan
3. Policy failed output with exit code 2
4. Policy passed output with exit code 0
5. HTML report opened in browser
6. GitHub Actions successful workflow
7. GitHub Code Scanning alerts
8. Uploaded workflow artifacts
9. pytest result showing 12 passed
10. GitHub repository home page

---

## 9. Ethical and Safety Considerations

BuildShield-CI is designed for safe defensive use.

The project does not:

- Perform exploitation
- Generate malware
- Upload malicious packages
- Exfiltrate secrets
- Attack package registries
- Access unauthorized repositories
- Execute untrusted packages

All vulnerable examples are local sample files created for controlled demonstration.

---

## 10. Challenges Faced

### 10.1 SARIF Validation

GitHub Code Scanning rejected an invalid SARIF property named `runAutomationDetails`. The issue was fixed by removing the invalid field and regenerating standards-compliant SARIF.

### 10.2 Repository-Relative SARIF Paths

SARIF paths needed to map properly to files inside the GitHub repository. This was handled by generating repository-relative artifact URIs.

### 10.3 Encoding Issues

PowerShell-created files sometimes included UTF-8 BOM. The file reader was updated to handle `utf-8-sig`.

### 10.4 Avoiding False Positives

The secure sample repository required realistic private registry configuration to avoid false dependency confusion findings.

---

## 11. Performance and Reliability

The scanner runs quickly on the sample repositories. Current automated tests complete successfully with:

```text
12 passed
```

The GitHub Actions workflow validates:

- Installation
- CLI availability
- Test suite
- Policy gate
- Report generation
- SARIF upload
- Artifact upload

---

## 12. Limitations

Current limitations:

- Static analysis only
- Limited language ecosystem coverage
- No live package registry lookups
- No CVE database integration
- No SBOM output yet
- No web dashboard yet
- No enterprise authentication or multi-user management

---

## 13. Future Roadmap

Planned future enhancements:

1. FastAPI backend
2. React dashboard
3. Download reports from web UI
4. SBOM generation
5. OSV vulnerability database integration
6. Dockerfile scanner
7. Kubernetes YAML scanner
8. GitLab CI scanner
9. PDF report generation
10. Enterprise policy templates
11. Historical scan tracking
12. Risk trend dashboard

---

## 14. Conclusion

BuildShield-CI successfully demonstrates an advanced DevSecOps security platform for CI/CD supply-chain risk detection. It combines static analysis, policy enforcement, risk scoring, report generation, CI/CD automation, SARIF integration, GitHub Code Scanning, and automated tests.

The project is suitable for cybersecurity career preparation, especially for roles in:

- DevSecOps
- Application Security
- Product Security
- Cloud Security
- Security Engineering
- Secure SDLC
- CI/CD Pipeline Security