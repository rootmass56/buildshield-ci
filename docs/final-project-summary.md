# BuildShield-CI Final Project Summary

## Project Title

BuildShield-CI: Advanced CI/CD Supply Chain Risk Analyzer and Dependency Confusion Defense Platform

## Executive Overview

BuildShield-CI is an advanced DevSecOps security platform designed to identify CI/CD supply-chain risks before deployment. It scans repositories for dependency confusion risks, insecure package configuration, weak GitHub Actions workflows, Dockerfile hardening issues, policy violations, and known vulnerable dependencies.

The project combines a command-line scanner, FastAPI backend, premium web dashboard, policy-as-code engine, SARIF output, GitHub Code Scanning integration, SQLite scan history, OSV vulnerability intelligence, Docker deployment, and automated test coverage.

## Problem Solved

Modern CI/CD pipelines depend on external packages, private packages, GitHub Actions workflows, container images, and automated build scripts. Misconfiguration in any of these areas can expose organizations to dependency confusion, secret leakage, malicious package installation, excessive CI permissions, and vulnerable dependency usage.

BuildShield-CI helps solve this problem by performing passive static analysis and producing actionable findings before code is deployed.

## Core Capabilities

1. Repository security scanning
2. npm dependency risk analysis
3. Python dependency risk analysis
4. Dependency confusion detection
5. GitHub Actions workflow security analysis
6. Dockerfile security analysis
7. Policy-as-code security gate
8. Advanced risk scoring
9. Secure vs vulnerable repository comparison
10. JSON, Markdown, HTML, and SARIF reports
11. GitHub Code Scanning integration
12. SBOM-lite dependency inventory
13. OSV vulnerability intelligence
14. SQLite scan history
15. Risk trend dashboard
16. Docker and Docker Compose deployment
17. Automated test suite

## Technical Architecture

BuildShield-CI is organized as a modular Python security platform.

Major components:

- CLI Layer: Typer-based command-line interface
- Scanner Core: repository file discovery and analyzer orchestration
- Analyzer Layer: npm, Python, GitHub Actions, Dockerfile analyzers
- Risk Engine: scoring, severity classification, risk profile, build gate decision
- Policy Engine: YAML policy-as-code enforcement
- Reporter Layer: JSON, Markdown, HTML, SARIF, OSV, and inventory reports
- FastAPI Backend: dashboard APIs and report downloads
- Web Dashboard: security command center, findings, policy, history, OSV, reports
- SQLite Storage: scan history and trend tracking
- CI/CD Layer: GitHub Actions workflow and Code Scanning upload
- Deployment Layer: Dockerfile, docker-compose, health checks, deployment guide

## Technology Stack

- Python 3.13
- Typer
- Rich
- FastAPI
- Pydantic
- SQLite
- HTML
- CSS
- JavaScript
- Docker
- Docker Compose
- GitHub Actions
- SARIF
- OSV vulnerability database
- Pytest

## Security Analysis Coverage

### npm Analysis

- Missing lockfile
- Loose dependency versions
- Risky lifecycle scripts
- Potential dependency confusion risk
- Missing private registry configuration

### Python Analysis

- Unpinned dependencies
- Loose dependency versions
- Internal package dependency confusion risk
- Missing private registry configuration

### GitHub Actions Analysis

- Actions not pinned to full commit SHA
- Over-permissive token permissions
- Remote script piped to shell
- Secret value printed in workflow
- pull_request_target risk

### Dockerfile Analysis

- Latest or unpinned base image
- Missing non-root user
- Secrets in ENV or ARG
- Remote script piped to shell
- apt-get upgrade during build
- Missing HEALTHCHECK

### OSV Vulnerability Intelligence

- Queryable pinned npm dependencies
- Queryable pinned Python dependencies
- GHSA / OSV vulnerability IDs
- Vulnerable package count
- Vulnerability intelligence JSON report

## Policy-as-Code

BuildShield-CI supports YAML policy enforcement. The policy can fail builds based on:

- Minimum security score
- Critical findings
- High findings
- Lockfile requirement
- Pinned GitHub Actions
- Secret echo prevention
- curl pipe shell prevention
- dependency confusion prevention

This allows BuildShield-CI to work as a real CI/CD security gate.

## Dashboard Features

The dashboard includes:

- Overview command center
- Repository scanner
- SBOM-lite inventory page
- Vulnerability intelligence page
- History and trend dashboard
- Findings explorer
- Policy evaluation view
- Reports center
- CI/CD flow view
- About/capability page

## Reports Generated

BuildShield-CI can generate:

- JSON scan reports
- Markdown scan reports
- HTML scan reports
- SARIF reports
- Comparison reports
- SBOM-lite dependency inventory reports
- OSV vulnerability intelligence reports

## CI/CD Integration

The GitHub Actions workflow:

- Installs BuildShield-CI
- Runs tests
- Scans secure and vulnerable samples
- Applies policy gate
- Generates reports
- Generates SARIF
- Uploads SARIF to GitHub Code Scanning
- Uploads reports as workflow artifacts

## Deployment

BuildShield-CI supports:

- Local Python execution
- Docker image build
- Docker runtime
- Docker Compose
- Persistent report volume
- Persistent SQLite data volume
- Health check endpoint
- Cloud-ready container deployment

## Testing

The project includes automated tests for:

- CLI behavior
- Scanner engine
- Policy engine
- Report generation
- Comparison engine
- Dashboard API
- SBOM-lite inventory
- Dockerfile analyzer
- OSV intelligence
- Vulnerability intelligence UI assets
- Deployment files

Current stable test count:

41 passing tests

## Final Outcome

BuildShield-CI is a complete advanced cybersecurity project suitable for:

- Internship demonstration
- Placement resume
- Final-year/major project
- DevSecOps portfolio
- Application security interview discussion
- CI/CD security learning

The project demonstrates practical knowledge of software supply-chain security, DevSecOps automation, secure CI/CD design, risk scoring, vulnerability intelligence, dashboard development, and deployment readiness.
