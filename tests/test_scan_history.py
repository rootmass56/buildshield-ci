from supplysentinel.web.history import get_recent_scan_history, get_risk_trend


def test_scan_history_is_created_after_dashboard_scan(authenticated_client):
    client, csrf_token = authenticated_client

    response = client.post(
        "/api/scan",
        headers={"X-CSRF-Token": csrf_token},
        json={
            "target_path": "samples/secure-repo",
            "policy_path": "buildshield-policy.yml",
            "report_formats": ["json"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "history_record" in data
    assert data["history_record"]["target_path"] == "samples/secure-repo"
    assert data["history_record"]["security_score"] == 100
    assert data["history_record"]["policy_status"] == "PASSED"


def test_history_api_returns_recent_scans(authenticated_client):
    client, _ = authenticated_client

    response = client.get("/api/history")

    assert response.status_code == 200

    data = response.json()

    assert "history" in data
    assert isinstance(data["history"], list)
    assert len(data["history"]) >= 1


def test_trend_api_returns_score_trend(authenticated_client):
    client, _ = authenticated_client

    response = client.get("/api/history/trend")

    assert response.status_code == 200

    data = response.json()

    assert "trend" in data
    assert isinstance(data["trend"], list)
    assert len(data["trend"]) >= 1
    assert "security_score" in data["trend"][-1]


def test_history_storage_functions_return_lists():
    history = get_recent_scan_history(limit=5)
    trend = get_risk_trend(limit=5)

    assert isinstance(history, list)
    assert isinstance(trend, list)
