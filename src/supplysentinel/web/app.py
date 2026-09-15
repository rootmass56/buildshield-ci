from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from supplysentinel import DESCRIPTION, PRODUCT_NAME, __version__
from supplysentinel.core.comparison import build_comparison_result
from supplysentinel.core.resource_budget import RepositoryResourceLimitError
from supplysentinel.core.scanner import scan_repository
from supplysentinel.intelligence.osv_client import (
    build_osv_vulnerability_report,
    generate_osv_report_json,
)
from supplysentinel.inventory.dependency_inventory import (
    build_dependency_inventory,
    generate_inventory_json,
)
from supplysentinel.policies.policy_engine import evaluate_policy
from supplysentinel.reporters.report_generator import (
    generate_comparison_report,
    generate_scan_report,
    write_report,
)
from supplysentinel.reporters.sarif_reporter import generate_scan_sarif
from supplysentinel.web.auth import (
    require_authenticated_session,
    router as auth_router,
)
from supplysentinel.web.audit import audit_event
from supplysentinel.web.error_handling import (
    safe_internal_error,
    safe_unhandled_exception_handler,
)
from supplysentinel.web.history import (
    get_recent_scan_history,
    get_risk_trend,
    save_scan_history,
)
from supplysentinel.web.path_security import (
    resolve_report_file,
    resolve_workspace_directory,
    resolve_workspace_file,
)
from supplysentinel.web.report_security import (
    enforce_report_retention,
    list_safe_reports,
    resolve_safe_report_download,
)
from supplysentinel.web.request_models import (
    CompareRequest,
    InventoryRequest,
    ScanRequest,
    VulnerabilityIntelligenceRequest,
)
from supplysentinel.web.resource_controls import (
    RequestBodyLimitMiddleware,
    require_expensive_operation_access,
)
from supplysentinel.web.logging_utils import (
    RequestCorrelationMiddleware,
    configure_structured_logging,
)


PROJECT_ROOT = Path.cwd()
REPORTS_ROOT = PROJECT_ROOT / "reports" / "dashboard"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST_DIR / "index.html"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

REPORTS_ROOT.mkdir(parents=True, exist_ok=True)


app = FastAPI(
    title=PRODUCT_NAME,
    description=DESCRIPTION,
    version=__version__,
)

configure_structured_logging()
app.include_router(auth_router)
app.add_middleware(RequestBodyLimitMiddleware)
app.add_middleware(RequestCorrelationMiddleware)
app.add_exception_handler(Exception, safe_unhandled_exception_handler)


CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self' data:",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
    ]
)


@app.middleware("http")
async def add_browser_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    content_type = response.headers.get("content-type", "")

    if request.url.path.startswith("/assets/") and response.status_code == 200:
        response.headers["Cache-Control"] = (
            "public, max-age=31536000, immutable"
        )
    elif request.url.path.startswith("/api/") or "text/html" in content_type:
        response.headers["Cache-Control"] = "no-store"

    return response


def timestamp_id(prefix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    random_suffix = uuid4().hex[:8]
    return f"{prefix}-{timestamp}-{random_suffix}"


def normalize_report_formats(
    formats: list[str],
    allowed_formats: set[str],
) -> list[str]:
    normalized: list[str] = []

    for item in formats:
        value = item.lower().strip()

        if value not in allowed_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported report format: {item}",
            )

        if value not in normalized:
            normalized.append(value)

    return normalized


def safe_report_file(run_id: str, filename: str) -> Path:
    return resolve_report_file(
        reports_root=REPORTS_ROOT,
        run_id=run_id,
        filename=filename,
    )


def model_to_json_safe(model: Any) -> Any:
    if model is None:
        return None

    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")

    return model


def build_report_link(run_id: str, path: Path) -> dict[str, str]:
    return {
        "run_id": run_id,
        "filename": path.name,
        "download_url": f"/api/reports/{run_id}/{path.name}",
    }


def save_scan_reports(
    run_id: str,
    result,
    target_name: str,
    report_formats: list[str],
) -> list[dict[str, str]]:
    run_dir = REPORTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    generated_reports: list[dict[str, str]] = []

    for report_format in report_formats:
        extension = report_format
        output_path = run_dir / f"{target_name}-scan.{extension}"

        if report_format == "sarif":
            report_content = generate_scan_sarif(result)
        else:
            report_content = generate_scan_report(result, report_format)

        written_path = write_report(str(output_path), report_content)
        generated_reports.append(build_report_link(run_id, written_path))

    return generated_reports


def save_comparison_reports(
    run_id: str,
    comparison,
    report_formats: list[str],
) -> list[dict[str, str]]:
    run_dir = REPORTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    generated_reports: list[dict[str, str]] = []

    for report_format in report_formats:
        output_path = run_dir / f"comparison-report.{report_format}"
        report_content = generate_comparison_report(comparison, report_format)

        written_path = write_report(str(output_path), report_content)
        generated_reports.append(build_report_link(run_id, written_path))

    return generated_reports


def save_inventory_report(run_id: str, inventory) -> list[dict[str, str]]:
    run_dir = REPORTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    output_path = run_dir / "dependency-inventory.json"
    written_path = write_report(str(output_path), generate_inventory_json(inventory))

    return [build_report_link(run_id, written_path)]


def save_vulnerability_intelligence_report(run_id: str, report) -> list[dict[str, str]]:
    run_dir = REPORTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    output_path = run_dir / "osv-vulnerability-intelligence.json"
    written_path = write_report(str(output_path), generate_osv_report_json(report))

    return [build_report_link(run_id, written_path)]


def frontend_index_response() -> FileResponse | HTMLResponse:
    if FRONTEND_INDEX.is_file():
        return FileResponse(
            FRONTEND_INDEX,
            media_type="text/html",
        )

    return HTMLResponse(
        content=(
            "<!doctype html>"
            "<html lang=\"en\">"
            "<head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>BuildShield-CI</title></head>"
            "<body><main>"
            "<h1>BuildShield-CI</h1>"
            "<p>The React production build is not available yet.</p>"
            "<p>Run the frontend production build before launching the dashboard.</p>"
            "</main></body></html>"
        ),
        status_code=200,
    )


@app.get("/", response_model=None)
def dashboard() -> FileResponse | HTMLResponse:
    return frontend_index_response()


@app.get("/assets/{asset_path:path}", include_in_schema=False)
def frontend_asset(asset_path: str) -> FileResponse:
    if not asset_path or "\x00" in asset_path:
        raise HTTPException(status_code=404, detail="Frontend asset not found.")

    try:
        asset_root = FRONTEND_ASSETS_DIR.resolve()
        target = (asset_root / asset_path).resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=404,
            detail="Frontend asset not found.",
        ) from error

    if not target.is_relative_to(asset_root):
        raise HTTPException(status_code=404, detail="Frontend asset not found.")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Frontend asset not found.")

    return FileResponse(target)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "product": PRODUCT_NAME,
        "version": __version__,
    }


@app.get("/api/sample-repositories")
def sample_repositories(
    _session: object = Depends(require_authenticated_session),
) -> dict[str, Any]:
    return {
        "repositories": [
            {
                "label": "Vulnerable Demo Repository",
                "path": "samples/vulnerable-repo",
                "description": "Intentionally vulnerable sample used to demonstrate findings.",
            },
            {
                "label": "Secure Demo Repository",
                "path": "samples/secure-repo",
                "description": "Hardened sample repository expected to pass policy.",
            },
        ],
        "default_policy": "buildshield-policy.yml",
    }


@app.post("/api/scan")
def scan_repository_api(
    request: ScanRequest,
    _session: object = Depends(require_expensive_operation_access),
) -> dict[str, Any]:
    target_path = resolve_workspace_directory(request.target_path)

    policy_path: Path | None = None

    if request.policy_path:
        policy_path = resolve_workspace_file(request.policy_path)

    report_formats = normalize_report_formats(
        request.report_formats,
        allowed_formats={"json", "md", "html", "sarif"},
    )

    try:
        result = scan_repository(str(target_path))

        if policy_path is not None:
            policy_evaluation = evaluate_policy(
                result=result,
                policy_path=str(policy_path),
            )
            result = result.model_copy(
                update={"policy_evaluation": policy_evaluation}
            )

    except RepositoryResourceLimitError as error:
        audit_event(
            "resource.scanner_budget",
            outcome="blocked",
            actor=getattr(_session, "username", None),
            operation="scan",
            reason="scanner_budget_exceeded",
        )
        raise HTTPException(status_code=413, detail=str(error)) from error
    except Exception as error:
        raise safe_internal_error("scan", error) from error

    run_id = timestamp_id("scan")
    target_name = target_path.name or "repository"

    reports = save_scan_reports(
        run_id=run_id,
        result=result,
        target_name=target_name,
        report_formats=report_formats,
    )

    enforce_report_retention(
        REPORTS_ROOT,
        actor=getattr(_session, "username", None),
    )

    history_record = save_scan_history(
        run_id=run_id,
        kind="scan",
        target_path=request.target_path,
        summary=result.summary,
        risk_profile=result.risk_profile,
        policy_evaluation=result.policy_evaluation,
        reports=reports,
    )

    audit_event(
        "security.operation",
        outcome="success",
        actor=getattr(_session, "username", None),
        operation="scan",
        details={"reports_generated": len(reports)},
    )

    return {
        "run_id": run_id,
        "kind": "scan",
        "target_path": request.target_path,
        "summary": model_to_json_safe(result.summary),
        "risk_profile": model_to_json_safe(result.risk_profile),
        "policy_evaluation": model_to_json_safe(result.policy_evaluation),
        "findings": [model_to_json_safe(finding) for finding in result.findings],
        "reports": reports,
        "history_record": history_record,
    }


@app.post("/api/inventory")
def dependency_inventory_api(
    request: InventoryRequest,
    _session: object = Depends(require_expensive_operation_access),
) -> dict[str, Any]:
    target_path = resolve_workspace_directory(request.target_path)

    try:
        inventory = build_dependency_inventory(str(target_path))
    except Exception as error:
        raise safe_internal_error("inventory", error) from error

    run_id = timestamp_id("inventory")
    reports = save_inventory_report(run_id=run_id, inventory=inventory)

    enforce_report_retention(
        REPORTS_ROOT,
        actor=getattr(_session, "username", None),
    )

    audit_event(
        "security.operation",
        outcome="success",
        actor=getattr(_session, "username", None),
        operation="inventory",
        details={"reports_generated": len(reports)},
    )

    return {
        "run_id": run_id,
        "kind": "inventory",
        "target_path": request.target_path,
        "inventory": model_to_json_safe(inventory),
        "reports": reports,
    }


@app.post("/api/vulnerability-intelligence")
def vulnerability_intelligence_api(
    request: VulnerabilityIntelligenceRequest,
    _session: object = Depends(require_expensive_operation_access),
) -> dict[str, Any]:
    target_path = resolve_workspace_directory(request.target_path)

    try:
        report = build_osv_vulnerability_report(
            target=str(target_path),
            online_lookup=request.online_lookup,
            timeout_seconds=request.timeout_seconds,
        )
    except Exception as error:
        raise safe_internal_error("vulnerability_intelligence", error) from error

    run_id = timestamp_id("osv")
    reports = save_vulnerability_intelligence_report(
        run_id=run_id,
        report=report,
    )

    enforce_report_retention(
        REPORTS_ROOT,
        actor=getattr(_session, "username", None),
    )

    audit_event(
        "security.operation",
        outcome="success",
        actor=getattr(_session, "username", None),
        operation="vulnerability_intelligence",
        details={"reports_generated": len(reports)},
    )

    return {
        "run_id": run_id,
        "kind": "vulnerability_intelligence",
        "target_path": request.target_path,
        "vulnerability_report": model_to_json_safe(report),
        "reports": reports,
    }


@app.post("/api/compare")
def compare_repositories_api(
    request: CompareRequest,
    _session: object = Depends(require_expensive_operation_access),
) -> dict[str, Any]:
    baseline_path = resolve_workspace_directory(request.baseline_path)
    target_path = resolve_workspace_directory(request.target_path)

    report_formats = normalize_report_formats(
        request.report_formats,
        allowed_formats={"json", "md", "html"},
    )

    try:
        baseline_result = scan_repository(str(baseline_path))
        target_result = scan_repository(str(target_path))

        comparison = build_comparison_result(
            baseline=baseline_result,
            target=target_result,
            baseline_label=request.baseline_label,
            target_label=request.target_label,
        )

    except RepositoryResourceLimitError as error:
        audit_event(
            "resource.scanner_budget",
            outcome="blocked",
            actor=getattr(_session, "username", None),
            operation="compare",
            reason="scanner_budget_exceeded",
        )
        raise HTTPException(status_code=413, detail=str(error)) from error
    except Exception as error:
        raise safe_internal_error("compare", error) from error

    run_id = timestamp_id("compare")

    reports = save_comparison_reports(
        run_id=run_id,
        comparison=comparison,
        report_formats=report_formats,
    )

    enforce_report_retention(
        REPORTS_ROOT,
        actor=getattr(_session, "username", None),
    )

    audit_event(
        "security.operation",
        outcome="success",
        actor=getattr(_session, "username", None),
        operation="compare",
        details={"reports_generated": len(reports)},
    )

    return {
        "run_id": run_id,
        "kind": "comparison",
        "comparison": model_to_json_safe(comparison),
        "reports": reports,
    }


@app.get("/api/history")
def scan_history(
    limit: int = Query(default=20, ge=1, le=100),
    _session: object = Depends(require_authenticated_session),
) -> dict[str, Any]:
    return {
        "history": get_recent_scan_history(limit=limit),
    }


@app.get("/api/history/trend")
def risk_trend(
    limit: int = Query(default=20, ge=1, le=100),
    _session: object = Depends(require_authenticated_session),
) -> dict[str, Any]:
    return {
        "trend": get_risk_trend(limit=limit),
    }


@app.get("/api/reports")
def list_reports(
    _session: object = Depends(require_authenticated_session),
) -> dict[str, list[dict[str, Any]]]:
    return {
        "reports": list_safe_reports(REPORTS_ROOT),
    }


@app.get("/api/reports/{run_id}/{filename}")
def download_report(
    run_id: str,
    filename: str,
    _session: object = Depends(require_authenticated_session),
) -> FileResponse:
    report = resolve_safe_report_download(
        reports_root=REPORTS_ROOT,
        run_id=run_id,
        filename=filename,
    )

    audit_event(
        "report.download",
        outcome="success",
        actor=getattr(_session, "username", None),
        operation="report_download",
        details={
            "format": report.path.suffix.lower(),
            "size_bytes": report.size_bytes,
        },
    )

    return FileResponse(
        path=report.path,
        filename=report.path.name,
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-store",
        },
    )


@app.get(
    "/{full_path:path}",
    include_in_schema=False,
    response_model=None,
)
def react_spa_fallback(full_path: str) -> FileResponse | HTMLResponse:
    first_segment = full_path.split("/", 1)[0].lower()

    if first_segment in {"api", "assets", "static"} or full_path.lower() == "health":
        raise HTTPException(status_code=404, detail="Not found.")

    return frontend_index_response()
