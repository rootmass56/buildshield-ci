# BuildShield-CI Screenshots Checklist

Use this checklist for the final portfolio/submission/demo capture.

## CLI and Tests

- [ ] `buildshield --help`
- [ ] `buildshield version`
- [ ] `pytest -q` showing `57 passed`
- [ ] Vulnerable scan showing `22 findings`
- [ ] Vulnerable scan showing `5/100`, `CRITICAL`, `FAILED`
- [ ] Vulnerable severity counts: `4 Critical / 10 High / 7 Medium / 1 Low`
- [ ] Hardened scan showing `0 findings`
- [ ] Hardened scan showing `100/100`, `LOW`, `PASSED`
- [ ] Comparison showing `+95`
- [ ] Comparison showing `22 findings reduced`
- [ ] Comparison showing `100%` risk reduction

## Supply-Chain Intelligence

- [ ] SBOM-lite inventory
- [ ] OSV offline query plan
- [ ] OSV online result (do not rely on a fixed vulnerability count)

## Dashboard

- [ ] Overview
- [ ] Scanner
- [ ] Findings
- [ ] Policy
- [ ] Compare
- [ ] SBOM Inventory
- [ ] Vulnerability Intelligence
- [ ] History & Trends
- [ ] Reports
- [ ] CI/CD
- [ ] About

## Reports

- [ ] Vulnerable HTML report
- [ ] Hardened HTML report
- [ ] Comparison HTML report
- [ ] JSON report
- [ ] Markdown report
- [ ] SARIF preview showing version `2.1.0`

## GitHub

- [ ] Repository home
- [ ] SHA-pinned `.github/workflows/buildshield-ci.yml`
- [ ] Successful Actions workflow
- [ ] Pytest workflow step
- [ ] SARIF upload step
- [ ] Artifact upload step
- [ ] Workflow artifacts
- [ ] Code Scanning page
- [ ] Example controlled sample alert
- [ ] Self-scan of `.github` showing `0 findings`

Add a caption when showing Code Scanning: **alerts originating from `samples/vulnerable-repo` are intentionally generated demo findings.**

## Docker

- [ ] Successful image build
- [ ] Running container
- [ ] `/health` response
- [ ] Docker Compose service status
- [ ] Dashboard running from container

## Recommended Naming

```text
01-repository-home.png
02-cli-help.png
03-pytest-57-passed.png
04-vulnerable-scan.png
05-hardened-scan.png
06-comparison.png
07-inventory.png
08-osv.png
09-dashboard-overview.png
10-dashboard-findings.png
11-html-report.png
12-actions-success.png
13-code-scanning.png
14-workflow-sha-pinning.png
15-docker-health.png
```
