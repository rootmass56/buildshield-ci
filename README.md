# BuildShield-CI

**Advanced CI/CD Supply Chain Risk Analyzer and Dependency Confusion Defense Platform**

BuildShield-CI is a DevSecOps security platform that detects CI/CD supply-chain risks before deployment. It analyzes repository files, dependencies, GitHub Actions workflows, Dockerfiles, registry configuration, policy rules, and known vulnerable package versions.

The project includes a CLI scanner, FastAPI backend, premium web dashboard, policy-as-code gate, SARIF/GitHub Code Scanning integration, SBOM-lite inventory, OSV vulnerability intelligence, SQLite scan history, Docker deployment, and automated tests.

---

## Project Highlights

- Detects dependency confusion risks
- Detects insecure npm and Python dependency configuration
- Detects weak GitHub Actions workflow security
- Detects Dockerfile hardening issues
- Enforces YAML policy-as-code rules
- Calculates security score and build-gate status
- Generates JSON, Markdown, HTML, SARIF, SBOM-lite, and OSV reports
- Uploads SARIF to GitHub Code Scanning
- Provides a FastAPI-powered security dashboard
- Tracks scan history using SQLite
- Visualizes security score and findings trends
- Integrates OSV vulnerability intelligence
- Supports Docker and Docker Compose deployment
- Includes automated pytest coverage

---

## Why BuildShield-CI Matters

Modern CI/CD pipelines depend on many moving parts:

- Public packages
- Private packages
- Package registries
- GitHub Actions workflows
- Dockerfiles
- Build scripts
- Secrets
- Lockfiles
- Dependency versions
- Cloud deployment pipelines

A small misconfiguration can create serious supply-chain risk. BuildShield-CI helps detect these risks early, before deployment.

---

## Security Risks Detected

### npm Security Analysis

- Missing npm lockfile
- Loose dependency versions
- Risky npm lifecycle scripts
- Internal package dependency confusion risk
- Missing private registry configuration

### Python Security Analysis

- Unpinned Python dependencies
- Loose Python dependency versions
- Internal package dependency confusion risk
- Missing private package index configuration

### GitHub Actions Security Analysis

- GitHub Actions not pinned to full commit SHA
- Over-permissive workflow token permissions
- Remote script piped directly to shell
- Secret value printed in workflow logs
- Risky `pull_request_target` trigger usage

### Dockerfile Security Analysis

- Latest or unpinned base image
- Missing non-root user
- Potential secrets in `ENV` or `ARG`
- Remote script piped to shell
- `apt-get upgrade` during image build
- Missing `HEALTHCHECK`

### OSV Vulnerability Intelligence

- Checks pinned npm dependencies
- Checks pinned Python dependencies
- Detects known GHSA / OSV vulnerability IDs
- Generates vulnerability intelligence reports

---

## Core Features

| Feature | Description |
|---|---|
| CLI Scanner | Run repository scans directly from terminal |
| FastAPI Backend | Provides APIs for scans, reports, history, inventory, and OSV intelligence |
| Web Dashboard | Premium UI for security visualization |
| Risk Scoring | Calculates security score, risk level, and build gate status |
| Policy-as-Code | Enforces YAML security policy |
| SARIF Output | Integrates with GitHub Code Scanning |
| SBOM-lite Inventory | Extracts dependency inventory from npm and Python files |
| OSV Intelligence | Checks dependency versions against known vulnerability data |
| SQLite History | Stores scan history and risk trend data |
| Docker Deployment | Runs as a containerized dashboard |
| GitHub Actions | Automates scans, tests, reports, and SARIF upload |
| Automated Tests | Validates scanner, policy, dashboard, OSV, Docker, and reports |

---

## Technology Stack

| Area | Technology |
|---|---|
| Language | Python 3.13 |
| CLI | Typer |
| Terminal UI | Rich |
| Backend | FastAPI |
| Data Models | Pydantic |
| Storage | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Reports | JSON, Markdown, HTML, SARIF |
| CI/CD | GitHub Actions |
| Code Scanning | SARIF / GitHub Code Scanning |
| Vulnerability Intelligence | OSV |
| Deployment | Docker, Docker Compose |
| Testing | Pytest |

---

## Project Architecture

```text
BuildShield-CI
│
├── CLI Layer
│   └── scan, compare, inventory, vulncheck, dashboard
│
├── Scanner Core
│   ├── repository discovery
│   ├── analyzer orchestration
│   └── finding aggregation
│
├── Analyzer Layer
│   ├── npm analyzer
│   ├── Python analyzer
│   ├── GitHub Actions analyzer
│   └── Dockerfile analyzer
│
├── Risk and Policy Layer
│   ├── risk scoring engine
│   ├── category-wise risk profile
│   ├── top risk drivers
│   └── YAML policy-as-code gate
│
├── Intelligence Layer
│   ├── SBOM-lite dependency inventory
│   └── OSV vulnerability intelligence
│
├── Reporting Layer
│   ├── JSON reports
│   ├── Markdown reports
│   ├── HTML reports
│   ├── SARIF reports
│   ├── inventory reports
│   └── OSV intelligence reports
│
├── Dashboard Layer
│   ├── FastAPI backend
│   ├── premium frontend UI
│   ├── findings explorer
│   ├── policy view
│   ├── reports center
│   ├── vulnerability intelligence page
│   └── risk trend dashboard
│
├── Persistence Layer
│   └── SQLite scan history
│
└── Deployment Layer
    ├── Dockerfile
    ├── docker-compose.yml
    ├── health check
    └── persistent volumes
```

---

## Installation

### 1. Clone the Repository

```powershell
git clone https://github.com/rootmass56/buildshield-ci.git
cd buildshield-ci
```

### 2. Create Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install BuildShield-CI

```powershell
pip install -e .
```

### 4. Verify Installation

```powershell
buildshield version
```

Expected:

```text
BuildShield-CI version: 0.12.6
```

---

## CLI Usage

### Scan Vulnerable Repository

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --hide-files
```

Expected result:

- Multiple findings detected
- Policy failed
- Build gate failed
- Low security score

### Scan Secure Repository

```powershell
buildshield scan samples/secure-repo --policy buildshield-policy.yml --hide-files
```

Expected result:

- Policy passed
- Build gate passed
- Improved security score

### Compare Vulnerable and Secure Repositories

```powershell
buildshield compare samples/vulnerable-repo samples/secure-repo
```

Expected result:

- Score improvement
- Findings reduced
- Risk reduction percentage

### Generate SBOM-lite Inventory

```powershell
buildshield inventory samples/vulnerable-repo --hide-packages
```

### Run OSV Vulnerability Intelligence

Offline query plan:

```powershell
buildshield vulncheck samples/secure-repo --offline-plan
```

Online OSV lookup:

```powershell
buildshield vulncheck samples/secure-repo --online --timeout 15
```

---

## Report Generation

### JSON Report

```powershell
buildshield scan samples/vulnerable-repo --report-format json --output reports/vulnerable-scan.json
```

### Markdown Report

```powershell
buildshield scan samples/vulnerable-repo --report-format md --output reports/vulnerable-scan.md
```

### HTML Report

```powershell
buildshield scan samples/vulnerable-repo --report-format html --output reports/vulnerable-scan.html
```

### SARIF Report

```powershell
buildshield scan samples/vulnerable-repo --report-format sarif --output reports/buildshield-results.sarif
```

---

## Dashboard

Start the dashboard:

```powershell
buildshield dashboard --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

Dashboard pages:

- Overview
- Scanner
- SBOM Inventory
- Vulnerability Intel
- History & Trends
- Compare
- Findings
- Policy
- Reports
- CI/CD
- About

---

## Policy-as-Code

BuildShield-CI uses YAML policy rules to decide whether a repository should pass or fail a CI/CD security gate.

Example policy controls:

- Minimum score requirement
- Block critical findings
- Block high findings
- Require lockfiles
- Require pinned GitHub Actions
- Block secret echoing
- Block curl pipe shell
- Block dependency confusion

Policy file:

```text
buildshield-policy.yml
```

Example command:

```powershell
buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --fail-on-policy
```

---

## GitHub Actions Integration

BuildShield-CI includes a GitHub Actions workflow that:

- Installs the project
- Runs tests
- Runs repository scans
- Applies policy-as-code
- Generates reports
- Generates SARIF
- Uploads SARIF to GitHub Code Scanning
- Uploads reports as workflow artifacts

Workflow path:

```text
.github/workflows/buildshield-ci.yml
```

---

## GitHub Code Scanning

BuildShield-CI generates SARIF output and uploads it to GitHub Code Scanning.

This allows findings to appear inside:

```text
Security and quality -> Code scanning
```

---

## Docker Deployment

### Build Docker Image

```powershell
docker build -t buildshield-ci:latest .
```

### Run Container

```powershell
docker run -d --name buildshield-ci-test -p 8080:8080 buildshield-ci:latest
```

### Health Check

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

Expected:

```text
status  product         version
------  -------         -------
ok      BuildShield-CI  0.12.6
```

### Stop Container

```powershell
docker stop buildshield-ci-test
docker rm buildshield-ci-test
```

---

## Docker Compose

Start:

```powershell
docker compose up --build -d
```

Check:

```powershell
docker compose ps
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

Stop:

```powershell
docker compose down
```

Docker Compose uses persistent volumes for:

- Generated reports
- SQLite scan history
- Dashboard data
- OSV reports
- SBOM reports

---

## Testing

Run all tests:

```powershell
pytest -q
```

Current stable result:

```text
41 passed
```

Test coverage includes:

- CLI behavior
- Scanner engine
- npm analyzer
- Python analyzer
- GitHub Actions analyzer
- Dockerfile analyzer
- Policy engine
- Report generation
- Comparison engine
- Dashboard APIs
- SBOM-lite inventory
- OSV vulnerability intelligence
- Dashboard UI assets
- Deployment files

---

## Demo Repository Structure

```text
samples/
├── vulnerable-repo/
│   ├── package.json
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .github/workflows/build.yml
│
└── secure-repo/
    ├── package.json
    ├── package-lock.json
    ├── requirements.txt
    ├── pip.conf
    ├── Dockerfile
    └── .github/workflows/build.yml
```

The vulnerable repository is intentionally insecure for demonstration.

The secure repository demonstrates improved configuration and policy compliance.

---

## Documentation

Additional documentation is available in:

```text
docs/
├── architecture.md
├── deployment.md
├── demo-script.md
├── final-project-summary.md
├── final-submission-checklist.md
├── interview-explanation.md
├── research-log.md
└── resume-points.md
```

---

## Ethical Scope

BuildShield-CI performs passive static analysis only.

It does not:

- Exploit systems
- Execute malware
- Attack live targets
- Steal credentials
- Access unauthorized systems
- Perform destructive testing

The project is designed for defensive DevSecOps and educational cybersecurity use.

---

## Final Project Status

BuildShield-CI is complete as an advanced cybersecurity project with:

- CLI
- Backend
- Dashboard
- Static analyzers
- Risk scoring
- Policy gate
- SARIF integration
- GitHub Actions
- GitHub Code Scanning
- SBOM-lite inventory
- OSV intelligence
- SQLite history
- Docker deployment
- Automated tests
- Final documentation

---

## Author

Developed as an advanced cybersecurity and DevSecOps project for internship, placement, and portfolio demonstration.