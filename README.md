# SupplySentinel

SupplySentinel is an advanced CI/CD supply-chain security platform that detects dependency confusion risks, insecure package registry configurations, unpinned dependencies, unsafe build scripts, and weak CI/CD workflow security controls.

## Core Objective

To help developers and security teams detect supply-chain risks before software reaches production by statically analyzing dependency manifests, registry configuration files, CI/CD workflows, and build scripts.

## Key Capabilities

- Repository intelligence and security-relevant file discovery
- Dependency confusion risk analysis
- Package registry misconfiguration detection
- CI/CD workflow security scanning
- GitHub Actions hardening checks
- Risk scoring engine
- Policy-as-code enforcement
- JSON, HTML, Markdown, and SARIF report generation
- CI/CD security gate integration

## Ethical Scope

SupplySentinel performs only static analysis. It does not download, execute, store, or interact with malware, exploit code, stolen data, credentials, or sensitive information.

## Current Status

Stage 1 completed:

- Professional project structure
- Installable Python package
- CLI command
- Repository discovery engine
- Structured data models
- Sample vulnerable repository

## Usage

```bash
supplysentinel scan samples/vulnerable-repo
```

## Project Architecture

Target Repository  
↓  
Repository Intelligence Engine  
↓  
File Classifier  
↓  
Analyzers  
↓  
Rule Engine  
↓  
Risk Scoring Engine  
↓  
Policy Evaluator  
↓  
Report Generator  
↓  
CLI / API / CI-CD Security Gate

## Assignment Alignment

This project is designed for the HCIC-SI2026 project assignment under the topic of static code scanning for CI/CD pipeline dependency confusion vulnerabilities.

The project follows the required ethical scope by using safe static analysis and synthetic demo repositories only.