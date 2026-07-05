from supplysentinel.core.scanner import scan_repository


def test_vulnerable_repo_detects_dockerfile_security_findings(vulnerable_repo):
    result = scan_repository(str(vulnerable_repo))

    rule_ids = {finding.rule_id for finding in result.findings}

    assert "DG-DOCKER-001" in rule_ids
    assert "DG-DOCKER-002" in rule_ids
    assert "DG-DOCKER-004" in rule_ids
    assert "DG-DOCKER-005" in rule_ids
    assert "DG-DOCKER-006" in rule_ids
    assert "DG-DOCKER-007" in rule_ids


def test_secure_repo_has_no_dockerfile_findings(secure_repo):
    result = scan_repository(str(secure_repo))

    docker_findings = [
        finding
        for finding in result.findings
        if finding.rule_id.startswith("DG-DOCKER")
    ]

    assert docker_findings == []


def test_dockerfile_is_discovered_as_security_relevant_file(vulnerable_repo):
    result = scan_repository(str(vulnerable_repo))

    discovered_paths = {
        repo_file.relative_path
        for repo_file in result.discovered_files
    }

    assert "Dockerfile" in discovered_paths