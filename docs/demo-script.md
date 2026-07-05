# BuildShield-CI Final Demo Script

## Demo Goal

The goal of this demo is to show how BuildShield-CI detects CI/CD supply-chain risks, enforces security policy, generates reports, integrates with GitHub security tooling, and provides dashboard-based visibility.

## Demo Preparation

Before demo, run:

    pytest -q

Expected:

    41 passed

Check version:

    buildshield version

Expected:

    BuildShield-CI version: 0.12.6

## Demo Flow

### 1. Explain the Problem

Modern CI/CD pipelines depend on:

- npm packages
- Python packages
- private package registries
- GitHub Actions workflows
- Dockerfiles
- build scripts
- secrets
- dependency versions

Attackers can abuse weak configurations using dependency confusion, malicious packages, unpinned actions, leaked secrets, and vulnerable dependencies.

BuildShield-CI detects these risks before deployment.

### 2. Show Vulnerable Repository Scan

Command:

    buildshield scan samples/vulnerable-repo --policy buildshield-policy.yml --hide-files

Explain:

- This repository intentionally contains insecure examples.
- The scanner detects dependency, registry, CI/CD, secret, build script, and Dockerfile risks.
- Policy-as-code fails the build because risk is too high.

Expected points to show:

- Low security score
- Critical/high findings
- Policy failed
- Build gate failed
- Dependency confusion findings
- GitHub Actions findings
- Dockerfile findings

### 3. Show Secure Repository Scan

Command:

    buildshield scan samples/secure-repo --policy buildshield-policy.yml --hide-files

Explain:

- This repository has improved configuration.
- Dependencies are pinned.
- Private registry configuration exists.
- GitHub Actions permissions are limited.
- Dockerfile is hardened.

Expected points to show:

- High security score
- Policy passed
- Build gate passed
- No major configuration risk

### 4. Show Before/After Comparison

Command:

    buildshield compare samples/vulnerable-repo samples/secure-repo

Explain:

- This compares vulnerable and secure repositories.
- It proves measurable security improvement.

Expected points to show:

- Score improvement
- Findings reduced
- Risk reduction percentage
- Improved build gate posture

### 5. Show SBOM-lite Inventory

Command:

    buildshield inventory samples/vulnerable-repo --hide-packages

Explain:

- SBOM-lite inventory extracts dependencies.
- It identifies pinned, loose, internal candidate, and registry-risk packages.
- This helps understand software supply-chain exposure.

### 6. Show OSV Vulnerability Intelligence

Offline mode:

    buildshield vulncheck samples/secure-repo --offline-plan

Explain:

- Offline mode prepares the query plan without contacting OSV.
- It proves dependencies are queryable.

Online mode:

    buildshield vulncheck samples/secure-repo --online --timeout 15

Explain:

- Online mode checks OSV vulnerability data.
- It can return GHSA or OSV vulnerability IDs.

### 7. Show Dashboard

Start:

    buildshield dashboard --port 8080

Open:

    http://127.0.0.1:8080

Show pages:

1. Overview
2. Scanner
3. SBOM Inventory
4. Vulnerability Intel
5. History & Trends
6. Compare
7. Findings
8. Policy
9. Reports
10. CI/CD
11. About

Explain:

- The dashboard gives a central security command center.
- Scans can be run from UI.
- Reports can be downloaded.
- History and risk trends are stored in SQLite.

### 8. Show GitHub Actions

Open GitHub repository Actions tab.

Explain:

- GitHub Actions runs BuildShield-CI automatically.
- Tests are executed.
- Policy gate is applied.
- SARIF is generated.
- Reports are uploaded as artifacts.

### 9. Show GitHub Code Scanning

Open Security and quality -> Code scanning.

Explain:

- SARIF results are uploaded to GitHub Code Scanning.
- Findings become visible in GitHub security interface.

### 10. Show Docker Deployment

Run:

    docker build -t buildshield-ci:latest .

Run:

    docker run -d --name buildshield-ci-test -p 8080:8080 buildshield-ci:latest

Health check:

    Invoke-RestMethod http://127.0.0.1:8080/health

Explain:

- BuildShield-CI is containerized.
- It runs with a non-root user.
- It includes health check.
- It is cloud deployment ready.

Stop:

    docker stop buildshield-ci-test
    docker rm buildshield-ci-test

### 11. Show Docker Compose

Run:

    docker compose up --build -d

Health check:

    Invoke-RestMethod http://127.0.0.1:8080/health

Stop:

    docker compose down

Explain:

- Docker Compose creates persistent volumes for reports and SQLite history.
- This simulates production-style local deployment.

## Closing Explanation

BuildShield-CI is not just a scanner. It is a complete DevSecOps security platform with:

- Static security analysis
- Policy-as-code enforcement
- CI/CD integration
- SARIF GitHub Code Scanning
- Vulnerability intelligence
- Dashboard visualization
- Scan history and risk trends
- Docker deployment readiness

This project demonstrates practical cybersecurity engineering across application security, supply-chain security, DevSecOps, and secure software delivery.
