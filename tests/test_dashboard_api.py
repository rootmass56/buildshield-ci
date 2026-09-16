import pytest
from fastapi.testclient import TestClient

from supplysentinel.web.app import app


public_client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def _close_public_client():
    yield
    public_client.close()


def test_dashboard_health_endpoint():
    response = public_client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["product"] == "BuildShield-CI"
    assert "version" in data


def test_dashboard_homepage_loads():
    response = public_client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_sample_repositories_endpoint(authenticated_client):
    client, _ = authenticated_client

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
        repo["path"] == "samples/realistic-repo"
        for repo in data["repositories"]
    )
    assert any(
        repo["path"] == "samples/secure-repo"
        for repo in data["repositories"]
    )


def test_dashboard_scan_secure_repo(authenticated_client):
    client, csrf_token = authenticated_client

    response = client.post(
        "/api/scan",
        headers={"X-CSRF-Token": csrf_token},
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


def test_dashboard_scan_vulnerable_repo(authenticated_client):
    client, csrf_token = authenticated_client

    response = client.post(
        "/api/scan",
        headers={"X-CSRF-Token": csrf_token},
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


def test_dashboard_scan_realistic_repo(authenticated_client):
    client, csrf_token = authenticated_client

    response = client.post(
        "/api/scan",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "target_path": "samples/realistic-repo",
            "policy_path": "buildshield-policy.yml",
            "report_formats": ["json", "html"],
        },
    )

    assert response.status_code == 200

    data = response.json()
    summary = data["summary"]

    assert data["kind"] == "scan"
    assert summary["security_score"] == 81
    assert summary["risk_level"] == "MEDIUM"
    assert summary["findings_count"] == 3
    assert summary["critical_count"] == 0
    assert summary["high_count"] == 0
    assert summary["medium_count"] == 2
    assert summary["low_count"] == 1
    assert data["risk_profile"]["build_gate_status"] == "WARNING"
    assert data["policy_evaluation"]["passed"] is True
    assert len(data["reports"]) == 2


def test_dashboard_compare_endpoint(authenticated_client):
    client, csrf_token = authenticated_client

    response = client.post(
        "/api/compare",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "baseline_path": "samples/vulnerable-repo",
            "target_path": "samples/realistic-repo",
            "baseline_label": "Vulnerable Benchmark Repository",
            "target_label": "Realistic Application Repository",
            "report_formats": ["json", "html"],
        },
    )

    assert response.status_code == 200

    data = response.json()
    comparison = data["comparison"]

    assert data["kind"] == "comparison"
    assert comparison["score_delta"] == 76
    assert comparison["findings_reduced"] == 19
    assert comparison["risk_reduction_percentage"] == 80.0
    assert comparison["target"]["summary"]["security_score"] == 81
    assert comparison["target"]["summary"]["findings_count"] == 3
    assert comparison["verdict"] == "SECURITY_POSTURE_PARTIALLY_IMPROVED"
    assert len(data["reports"]) == 2


def test_reports_listing_endpoint(authenticated_client):
    client, _ = authenticated_client

    response = client.get("/api/reports")

    assert response.status_code == 200

    data = response.json()

    assert "reports" in data
    assert isinstance(data["reports"], list)
