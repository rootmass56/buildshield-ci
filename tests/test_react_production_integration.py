from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import supplysentinel.web.app as web_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]
client = TestClient(web_app.app)


def test_browser_security_headers_are_present():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cross-origin-opener-policy"] == "same-origin"
    assert response.headers["cross-origin-resource-policy"] == "same-origin"

    csp = response.headers["content-security-policy"]

    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "base-uri 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "'unsafe-eval'" not in csp

    script_directive = next(
        directive
        for directive in csp.split("; ")
        if directive.startswith("script-src ")
    )

    assert "'unsafe-inline'" not in script_directive


def test_spa_routes_return_html_shell():
    response = client.get("/app/scanner")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert response.headers["cache-control"] == "no-store"


def test_unknown_api_route_is_not_rewritten_to_spa():
    response = client.get("/api/route-that-does-not-exist")

    assert response.status_code == 404
    assert "application/json" in response.headers["content-type"]


def test_legacy_static_route_is_not_served():
    response = client.get("/static/app.js")

    assert response.status_code == 404


def test_frontend_asset_resolution_rejects_escape():
    with pytest.raises(HTTPException) as error:
        web_app.frontend_asset("../package.json")

    assert error.value.status_code == 404


def test_legacy_vanilla_frontend_files_are_removed():
    static_root = PROJECT_ROOT / "src" / "supplysentinel" / "web" / "static"

    legacy_files = [
        static_root / "index.html",
        static_root / "app.js",
        static_root / "styles.css",
        static_root / "vulnerability-intelligence.js",
    ]

    assert all(not path.exists() for path in legacy_files)
