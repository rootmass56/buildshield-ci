from fastapi.testclient import TestClient

from supplysentinel.web.app import app


client = TestClient(app)


def test_dashboard_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["product"] == "BuildShield-CI"
    assert "version" in data


def test_dashboard_homepage_loads():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_sample_repositories_endpoint():
    response = client.get("/api/sample-repositories")

    assert response.status_code == 200

    data = response.json()

    assert "repositories" in data
    assert data["default_policy"] == "buildshield-policy.yml"
    assert any(
        repo["path"] == "samples/vulnerable-repo"
        for repo in data["repositories"]
    )
    assert any(
        repo["path"] == "samples/secure-repo"
        for repo in data["repositories"]
    )


def test_dashboard_scan_secure_repo():
    response = client.post(
        "/api/scan",
        json={
            "target_path": "samples/secure-repo",
            "policy_path": "buildshield-policy.yml",
            "report_formats": ["json", "html"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["kind"] == "scan"
    assert data["summary"]["security_score"] == 100
    assert data["summary"]["findings_count"] == 0
    assert data["policy_evaluation"]["passed"] is True
    assert len(data["reports"]) == 2


def test_dashboard_scan_vulnerable_repo():
    response = client.post(
        "/api/scan",
        json={
            "target_path": "samples/vulnerable-repo",
            "policy_path": "buildshield-policy.yml",
            "report_formats": ["json", "sarif"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["kind"] == "scan"
    assert data["summary"]["security_score"] < 80
    assert data["summary"]["findings_count"] > 0
    assert data["policy_evaluation"]["passed"] is False
    assert len(data["reports"]) == 2


def test_dashboard_compare_endpoint():
    response = client.post(
        "/api/compare",
        json={
            "baseline_path": "samples/vulnerable-repo",
            "target_path": "samples/secure-repo",
            "baseline_label": "Vulnerable Repo",
            "target_label": "Secure Repo",
            "report_formats": ["json", "html"],
        },
    )

    assert response.status_code == 200

    data = response.json()
    comparison = data["comparison"]

    assert data["kind"] == "comparison"
    assert comparison["score_delta"] > 0
    assert comparison["findings_reduced"] > 0
    assert comparison["target"]["summary"]["security_score"] == 100
    assert len(data["reports"]) == 2


def test_reports_listing_endpoint():
    response = client.get("/api/reports")

    assert response.status_code == 200

    data = response.json()

    assert "reports" in data
    assert isinstance(data["reports"], list)