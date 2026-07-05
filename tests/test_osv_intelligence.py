import json

from fastapi.testclient import TestClient

from supplysentinel.intelligence.osv_client import (
    build_osv_queries_from_inventory,
    build_osv_vulnerability_report,
    build_osv_query_payload,
    generate_osv_report_json,
)
from supplysentinel.inventory.dependency_inventory import build_dependency_inventory
from supplysentinel.web.app import app


client = TestClient(app)


def test_osv_query_planning_for_secure_repo(secure_repo):
    inventory = build_dependency_inventory(str(secure_repo))
    queries, skipped = build_osv_queries_from_inventory(inventory)

    assert inventory.summary.total_dependencies > 0
    assert len(queries) > 0

    package_names = {query.package_name for query in queries}

    assert "flask" in package_names
    assert "requests" in package_names


def test_osv_payload_generation_for_secure_repo(secure_repo):
    inventory = build_dependency_inventory(str(secure_repo))
    queries, _ = build_osv_queries_from_inventory(inventory)

    payload = build_osv_query_payload(queries)

    assert "queries" in payload
    assert len(payload["queries"]) == len(queries)
    assert payload["queries"][0]["package"]["ecosystem"] in {"npm", "PyPI"}
    assert "version" in payload["queries"][0]


def test_osv_report_offline_mode_is_stable(secure_repo):
    report = build_osv_vulnerability_report(
        target=str(secure_repo),
        online_lookup=False,
    )

    assert report.summary.online_lookup_status == "SKIPPED"
    assert report.summary.total_dependencies_seen > 0
    assert report.summary.queryable_dependencies > 0
    assert report.summary.total_vulnerabilities == 0


def test_osv_report_json_generation(secure_repo):
    report = build_osv_vulnerability_report(
        target=str(secure_repo),
        online_lookup=False,
    )

    report_json = generate_osv_report_json(report)
    data = json.loads(report_json)

    assert "summary" in data
    assert "package_results" in data
    assert data["summary"]["online_lookup_status"] == "SKIPPED"


def test_dashboard_vulnerability_intelligence_endpoint_offline():
    response = client.post(
        "/api/vulnerability-intelligence",
        json={
            "target_path": "samples/secure-repo",
            "online_lookup": False,
            "timeout_seconds": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["kind"] == "vulnerability_intelligence"
    assert data["target_path"] == "samples/secure-repo"
    assert data["vulnerability_report"]["summary"]["online_lookup_status"] == "SKIPPED"
    assert len(data["reports"]) == 1