from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from supplysentinel import DESCRIPTION, PRODUCT_NAME, __version__
from supplysentinel.core.comparison import build_comparison_result
from supplysentinel.core.scanner import scan_repository
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


PROJECT_ROOT = Path.cwd()
REPORTS_ROOT = PROJECT_ROOT / "reports" / "dashboard"
STATIC_DIR = Path(__file__).resolve().parent / "static"

REPORTS_ROOT.mkdir(parents=True, exist_ok=True)


class ScanRequest(BaseModel):
    target_path: str = Field(default="samples/vulnerable-repo")
    policy_path: str | None = Field(default="buildshield-policy.yml")
    report_formats: list[str] = Field(
        default_factory=lambda: ["json", "md", "html", "sarif"]
    )


class CompareRequest(BaseModel):
    baseline_path: str = Field(default="samples/vulnerable-repo")
    target_path: str = Field(default="samples/secure-repo")
    baseline_label: str = Field(default="Vulnerable Repo")
    target_label: str = Field(default="Secure Repo")
    report_formats: list[str] = Field(default_factory=lambda: ["json", "md", "html"])


class InventoryRequest(BaseModel):
    target_path: str = Field(default="samples/vulnerable-repo")


app = FastAPI(
    title=PRODUCT_NAME,
    description=DESCRIPTION,
    version=__version__,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def timestamp_id(prefix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    random_suffix = uuid4().hex[:8]
    return f"{prefix}-{timestamp}-{random_suffix}"


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    resolved = path.resolve()

    if not resolved.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Path does not exist: {path_value}",
        )

    return resolved


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
    reports_root = REPORTS_ROOT.resolve()
    target = (REPORTS_ROOT / run_id / filename).resolve()

    if not str(target).startswith(str(reports_root)):
        raise HTTPException(status_code=400, detail="Invalid report path.")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Report file not found.")

    return target


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


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "product": PRODUCT_NAME,
        "version": __version__,
    }


@app.get("/api/sample-repositories")
def sample_repositories() -> dict[str, Any]:
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
def scan_repository_api(request: ScanRequest) -> dict[str, Any]:
    target_path = resolve_project_path(request.target_path)

    if request.policy_path:
        resolve_project_path(request.policy_path)

    report_formats = normalize_report_formats(
        request.report_formats,
        allowed_formats={"json", "md", "html", "sarif"},
    )

    try:
        result = scan_repository(request.target_path)

        if request.policy_path:
            policy_evaluation = evaluate_policy(
                result=result,
                policy_path=request.policy_path,
            )
            result = result.model_copy(
                update={"policy_evaluation": policy_evaluation}
            )

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    run_id = timestamp_id("scan")
    target_name = target_path.name or "repository"

    reports = save_scan_reports(
        run_id=run_id,
        result=result,
        target_name=target_name,
        report_formats=report_formats,
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
    }


@app.post("/api/inventory")
def dependency_inventory_api(request: InventoryRequest) -> dict[str, Any]:
    resolve_project_path(request.target_path)

    try:
        inventory = build_dependency_inventory(request.target_path)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    run_id = timestamp_id("inventory")
    reports = save_inventory_report(run_id=run_id, inventory=inventory)

    return {
        "run_id": run_id,
        "kind": "inventory",
        "target_path": request.target_path,
        "inventory": model_to_json_safe(inventory),
        "reports": reports,
    }


@app.post("/api/compare")
def compare_repositories_api(request: CompareRequest) -> dict[str, Any]:
    resolve_project_path(request.baseline_path)
    resolve_project_path(request.target_path)

    report_formats = normalize_report_formats(
        request.report_formats,
        allowed_formats={"json", "md", "html"},
    )

    try:
        baseline_result = scan_repository(request.baseline_path)
        target_result = scan_repository(request.target_path)

        comparison = build_comparison_result(
            baseline=baseline_result,
            target=target_result,
            baseline_label=request.baseline_label,
            target_label=request.target_label,
        )

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    run_id = timestamp_id("compare")

    reports = save_comparison_reports(
        run_id=run_id,
        comparison=comparison,
        report_formats=report_formats,
    )

    return {
        "run_id": run_id,
        "kind": "comparison",
        "comparison": model_to_json_safe(comparison),
        "reports": reports,
    }


@app.get("/api/reports")
def list_reports() -> dict[str, list[dict[str, str]]]:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, str]] = []

    for run_dir in sorted(REPORTS_ROOT.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue

        for report_file in sorted(run_dir.iterdir()):
            if not report_file.is_file():
                continue

            reports.append(
                {
                    "run_id": run_dir.name,
                    "filename": report_file.name,
                    "download_url": f"/api/reports/{run_dir.name}/{report_file.name}",
                }
            )

    return {"reports": reports}


@app.get("/api/reports/{run_id}/{filename}")
def download_report(run_id: str, filename: str) -> FileResponse:
    report_file = safe_report_file(run_id, filename)

    return FileResponse(
        path=report_file,
        filename=report_file.name,
        media_type="application/octet-stream",
    )