# BuildShield-CI Research Collection Log

This file records the references used while designing and validating BuildShield-CI. The project uses AI only as an implementation assistant; all security claims and implementation decisions are validated using official documentation or credible security research.

| Date | Time | Source | Link | Used For |
|---|---:|---|---|---|
| 2026-07-04 | 18:00 IST | GitHub Docs - Workflow syntax | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax | Understanding GitHub Actions workflow structure, triggers, permissions, and jobs. |
| 2026-07-04 | 18:10 IST | GitHub Docs - Store and share data with workflow artifacts | https://docs.github.com/en/actions/tutorials/store-and-share-data | Designing report artifact upload in GitHub Actions. |
| 2026-07-04 | 18:20 IST | GitHub Docs - Uploading SARIF files | https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file | Implementing SARIF upload to GitHub Code Scanning. |
| 2026-07-04 | 18:35 IST | GitHub Docs - Secure use reference | https://docs.github.com/en/actions/reference/security/secure-use | Understanding GitHub Actions security hardening, secret handling, and risky workflow behavior. |
| 2026-07-04 | 18:50 IST | npm Docs - Scripts | https://docs.npmjs.com/cli/v10/using-npm/scripts/ | Understanding npm lifecycle scripts such as preinstall and postinstall. |
| 2026-07-04 | 19:05 IST | Python Packaging User Guide - Dependency specifiers | https://packaging.python.org/en/latest/specifications/dependency-specifiers/ | Understanding Python dependency version specifier formats. |
| 2026-07-04 | 19:20 IST | Alex Birsan - Dependency Confusion research | https://medium.com/@alex.birsan/dependency-confusion-4a5d60fec610 | Understanding dependency confusion attack model and risk scenarios. |
| 2026-07-04 | 19:35 IST | OWASP Top 10 CI/CD Security Risks | https://owasp.org/www-project-top-10-ci-cd-security-risks/ | Mapping CI/CD risks to practical detection categories. |
| 2026-07-05 | 00:30 IST | GitHub Code Scanning UI | https://github.com/rootmass56/buildshield-ci/security/code-scanning | Validating that SARIF findings appear inside GitHub Code Scanning. |
| 2026-07-05 | 00:45 IST | BuildShield-CI GitHub Actions run | https://github.com/rootmass56/buildshield-ci/actions | Validating CI/CD workflow execution, test execution, SARIF upload, and artifact generation. |

## Notes

- No fabricated references were used.
- No exploit code, malware, or unauthorized testing was performed.
- All sample vulnerabilities were created locally inside `samples/vulnerable-repo`.
- The project performs passive static analysis only.
- GitHub Code Scanning alerts are generated from the controlled vulnerable sample repository.