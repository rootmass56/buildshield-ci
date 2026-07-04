# BuildShield-CI Screenshots Checklist

Use this checklist while preparing the final submission/demo.

## Required Screenshots

### Local Tool Screenshots

- [ ] `buildshield --help`
- [ ] `buildshield version`
- [ ] Vulnerable repository scan output
- [ ] Secure repository scan output
- [ ] Vulnerable repository policy failure
- [ ] `echo $LASTEXITCODE` showing `2`
- [ ] Secure repository policy pass
- [ ] `echo $LASTEXITCODE` showing `0`
- [ ] Before vs after comparison output
- [ ] `pytest -q` showing `12 passed`

### Report Screenshots

- [ ] `reports/vulnerable-policy-report.html`
- [ ] `reports/secure-policy-report.html`
- [ ] `reports/comparison-report.html`
- [ ] SARIF file preview showing `"version": "2.1.0"`

### GitHub Screenshots

- [ ] GitHub repository home page
- [ ] `.github/workflows/buildshield-ci.yml`
- [ ] Successful GitHub Actions workflow
- [ ] Run automated test suite step
- [ ] Upload SARIF to GitHub code scanning step
- [ ] Upload BuildShield-CI reports artifact step
- [ ] Downloaded artifact contents
- [ ] GitHub Code Scanning alerts page
- [ ] Example code scanning alert details

## Recommended Naming

Save screenshots using names like:

```text
01-repository-home.png
02-cli-help.png
03-vulnerable-scan.png
04-secure-scan.png
05-policy-failed-exit-code.png
06-policy-passed-exit-code.png
07-comparison-output.png
08-html-report.png
09-pytest-passed.png
10-github-actions-success.png
11-code-scanning-alerts.png
12-artifacts.png
```

## Demo Tip

During presentation, show screenshots in this order:

1. Problem
2. Vulnerable scan
3. Secure scan
4. Policy gate
5. CI/CD workflow
6. Code scanning
7. Reports
8. Tests
9. Architecture
10. Future roadmap