from __future__ import annotations

import pytest
from pydantic import ValidationError

from supplysentinel.web.request_models import (
    CompareRequest,
    InventoryRequest,
    MAX_LABEL_LENGTH,
    MAX_OSV_TIMEOUT_SECONDS,
    MAX_PATH_LENGTH,
    ScanRequest,
    VulnerabilityIntelligenceRequest,
)


def _csrf_headers(token: str) -> dict[str, str]:
    return {"X-CSRF-Token": token}


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (ScanRequest, {"target_path": "samples/secure-repo", "unexpected": True}),
        (
            CompareRequest,
            {
                "baseline_path": "samples/vulnerable-repo",
                "target_path": "samples/secure-repo",
                "unexpected": True,
            },
        ),
        (InventoryRequest, {"target_path": "samples/secure-repo", "unexpected": True}),
        (
            VulnerabilityIntelligenceRequest,
            {"target_path": "samples/secure-repo", "unexpected": True},
        ),
    ],
)
def test_request_models_forbid_unknown_fields(model, payload):
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_scan_request_rejects_empty_long_nul_and_duplicate_values():
    invalid_payloads = [
        {"target_path": ""},
        {"target_path": "a" * (MAX_PATH_LENGTH + 1)},
        {"target_path": "samples/\x00repo"},
        {"policy_path": ""},
                {"report_formats": ["json", "json"]},
        {"report_formats": ["json", "xml"]},
    ]

    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            ScanRequest.model_validate(payload)


def test_empty_report_format_lists_remain_valid_for_no_report_execution():
    scan_request = ScanRequest.model_validate({"report_formats": []})
    compare_request = CompareRequest.model_validate({"report_formats": []})

    assert scan_request.report_formats == []
    assert compare_request.report_formats == []


def test_compare_request_rejects_unbounded_or_unsafe_labels():
    invalid_payloads = [
        {"baseline_label": "   "},
        {"target_label": "a" * (MAX_LABEL_LENGTH + 1)},
        {"baseline_label": "baseline\r\nInjected: value"},
        {"target_label": "secure\x00label"},
        {"report_formats": ["json", "json"]},
        {"report_formats": ["sarif"]},
    ]

    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            CompareRequest.model_validate(payload)


@pytest.mark.parametrize(
    "timeout_seconds",
    [0, -1, MAX_OSV_TIMEOUT_SECONDS + 1],
)
def test_osv_timeout_is_bounded(timeout_seconds):
    with pytest.raises(ValidationError):
        VulnerabilityIntelligenceRequest.model_validate(
            {"timeout_seconds": timeout_seconds}
        )


def test_api_rejects_extra_fields_before_scan_execution(authenticated_client):
    client, csrf_token = authenticated_client
    response = client.post(
        "/api/scan",
        json={"target_path": "samples/secure-repo", "unexpected": "not-allowed"},
        headers=_csrf_headers(csrf_token),
    )
    assert response.status_code == 422


def test_api_rejects_invalid_scan_format_before_execution(authenticated_client):
    client, csrf_token = authenticated_client
    response = client.post(
        "/api/scan",
        json={
            "target_path": "samples/secure-repo",
            "report_formats": ["json", "xml"],
        },
        headers=_csrf_headers(csrf_token),
    )
    assert response.status_code == 422


def test_api_rejects_oversized_inventory_path(authenticated_client):
    client, csrf_token = authenticated_client
    response = client.post(
        "/api/inventory",
        json={"target_path": "a" * (MAX_PATH_LENGTH + 1)},
        headers=_csrf_headers(csrf_token),
    )
    assert response.status_code == 422


def test_api_rejects_out_of_range_osv_timeout(authenticated_client):
    client, csrf_token = authenticated_client
    response = client.post(
        "/api/vulnerability-intelligence",
        json={
            "target_path": "samples/secure-repo",
            "online_lookup": False,
            "timeout_seconds": MAX_OSV_TIMEOUT_SECONDS + 1,
        },
        headers=_csrf_headers(csrf_token),
    )
    assert response.status_code == 422


@pytest.mark.parametrize("endpoint", ["/api/history", "/api/history/trend"])
@pytest.mark.parametrize("limit", [0, 101, -5])
def test_history_query_limit_is_bounded(authenticated_client, endpoint, limit):
    client, _csrf_token = authenticated_client
    response = client.get(endpoint, params={"limit": limit})
    assert response.status_code == 422


@pytest.mark.parametrize("endpoint", ["/api/history", "/api/history/trend"])
def test_history_query_limit_accepts_documented_boundary(
    authenticated_client,
    endpoint,
):
    client, _csrf_token = authenticated_client
    response = client.get(endpoint, params={"limit": 100})
    assert response.status_code == 200
