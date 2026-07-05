import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from supplysentinel.inventory.dependency_inventory import (
    DependencyInventory,
    DependencyRecord,
    build_dependency_inventory,
)


OSV_QUERYBATCH_URL = "https://api.osv.dev/v1/querybatch"

LookupStatus = Literal[
    "COMPLETED",
    "FAILED",
    "SKIPPED",
    "NO_QUERYABLE_DEPENDENCIES",
]


class OsvVulnerabilityRecord(BaseModel):
    vulnerability_id: str
    modified: str | None = None
    detail_url: str


class OsvPackageQuery(BaseModel):
    query_id: str
    ecosystem: str
    osv_ecosystem: str
    package_name: str
    version: str
    file_path: str
    line_number: int | None = None


class OsvPackageResult(BaseModel):
    ecosystem: str
    osv_ecosystem: str | None = None
    package_name: str
    version: str | None = None
    file_path: str
    line_number: int | None = None
    vulnerability_count: int = 0
    vulnerabilities: list[OsvVulnerabilityRecord] = Field(default_factory=list)
    skipped_reason: str | None = None


class OsvVulnerabilitySummary(BaseModel):
    target_path: str
    generated_at: str
    total_dependencies_seen: int
    queryable_dependencies: int
    skipped_dependencies: int
    vulnerable_dependencies: int
    total_vulnerabilities: int
    online_lookup_status: LookupStatus
    error_message: str | None = None


class OsvVulnerabilityReport(BaseModel):
    summary: OsvVulnerabilitySummary
    package_results: list[OsvPackageResult]


class OsvLookupError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_exact_npm_version(version: str | None) -> bool:
    if not version:
        return False

    normalized = version.strip()

    if any(
        token in normalized.lower()
        for token in ["^", "~", ">", "<", "*", "x", "latest", "workspace:", "file:", "git+", "http:", "https:"]
    ):
        return False

    return bool(re.match(r"^\d+\.\d+\.\d+([a-zA-Z0-9.\-_+]+)?$", normalized))


def extract_osv_version(dependency: DependencyRecord) -> str | None:
    declared_version = dependency.declared_version

    if not declared_version:
        return None

    version = declared_version.strip()

    if dependency.ecosystem == "python":
        if version.startswith("=="):
            cleaned = version.replace("==", "", 1).strip()
            return cleaned if cleaned else None

        return None

    if dependency.ecosystem == "npm":
        return version if is_exact_npm_version(version) else None

    return None


def osv_ecosystem_for_dependency(dependency: DependencyRecord) -> str | None:
    if dependency.ecosystem == "python":
        return "PyPI"

    if dependency.ecosystem == "npm":
        return "npm"

    return None


def build_query_id(index: int, dependency: DependencyRecord, version: str) -> str:
    return (
        f"{index}:{dependency.ecosystem}:"
        f"{dependency.name}:{version}:"
        f"{dependency.file_path}:{dependency.line_number or '-'}"
    )


def build_osv_queries_from_inventory(
    inventory: DependencyInventory,
) -> tuple[list[OsvPackageQuery], list[OsvPackageResult]]:
    queries: list[OsvPackageQuery] = []
    skipped_results: list[OsvPackageResult] = []

    for index, dependency in enumerate(inventory.dependencies, start=1):
        osv_ecosystem = osv_ecosystem_for_dependency(dependency)

        if osv_ecosystem is None:
            skipped_results.append(
                OsvPackageResult(
                    ecosystem=dependency.ecosystem,
                    package_name=dependency.name,
                    version=dependency.declared_version,
                    file_path=dependency.file_path,
                    line_number=dependency.line_number,
                    skipped_reason="UNSUPPORTED_ECOSYSTEM",
                )
            )
            continue

        version = extract_osv_version(dependency)

        if version is None:
            skipped_results.append(
                OsvPackageResult(
                    ecosystem=dependency.ecosystem,
                    osv_ecosystem=osv_ecosystem,
                    package_name=dependency.name,
                    version=dependency.declared_version,
                    file_path=dependency.file_path,
                    line_number=dependency.line_number,
                    skipped_reason="VERSION_NOT_EXACTLY_PINNED",
                )
            )
            continue

        queries.append(
            OsvPackageQuery(
                query_id=build_query_id(index, dependency, version),
                ecosystem=dependency.ecosystem,
                osv_ecosystem=osv_ecosystem,
                package_name=dependency.name,
                version=version,
                file_path=dependency.file_path,
                line_number=dependency.line_number,
            )
        )

    return queries, skipped_results


def build_osv_query_payload(queries: list[OsvPackageQuery]) -> dict[str, Any]:
    return {
        "queries": [
            {
                "package": {
                    "ecosystem": query.osv_ecosystem,
                    "name": query.package_name,
                },
                "version": query.version,
            }
            for query in queries
        ]
    }


def chunk_queries(
    queries: list[OsvPackageQuery],
    chunk_size: int = 100,
) -> list[list[OsvPackageQuery]]:
    return [
        queries[index:index + chunk_size]
        for index in range(0, len(queries), chunk_size)
    ]


def post_json(
    url: str,
    payload: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    encoded_payload = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=encoded_payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "BuildShield-CI-OSV-Client",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    except urllib.error.HTTPError as error:
        message = error.read().decode("utf-8", errors="ignore")
        raise OsvLookupError(
            f"OSV API returned HTTP {error.code}: {message}"
        ) from error

    except urllib.error.URLError as error:
        raise OsvLookupError(
            f"OSV API connection failed: {error.reason}"
        ) from error

    except TimeoutError as error:
        raise OsvLookupError("OSV API request timed out.") from error

    except json.JSONDecodeError as error:
        raise OsvLookupError("OSV API returned invalid JSON.") from error


def vulnerability_record_from_osv(vuln: dict[str, Any]) -> OsvVulnerabilityRecord:
    vulnerability_id = str(vuln.get("id", "UNKNOWN"))

    return OsvVulnerabilityRecord(
        vulnerability_id=vulnerability_id,
        modified=vuln.get("modified"),
        detail_url=f"https://osv.dev/vulnerability/{vulnerability_id}",
    )


def empty_result_for_query(query: OsvPackageQuery) -> OsvPackageResult:
    return OsvPackageResult(
        ecosystem=query.ecosystem,
        osv_ecosystem=query.osv_ecosystem,
        package_name=query.package_name,
        version=query.version,
        file_path=query.file_path,
        line_number=query.line_number,
        vulnerability_count=0,
        vulnerabilities=[],
    )


def query_osv_batch(
    queries: list[OsvPackageQuery],
    timeout_seconds: int = 10,
) -> list[OsvPackageResult]:
    all_results: list[OsvPackageResult] = []

    for query_chunk in chunk_queries(queries):
        payload = build_osv_query_payload(query_chunk)
        response_data = post_json(
            url=OSV_QUERYBATCH_URL,
            payload=payload,
            timeout_seconds=timeout_seconds,
        )

        response_results = response_data.get("results", [])

        for index, query in enumerate(query_chunk):
            raw_result = response_results[index] if index < len(response_results) else {}
            vulnerabilities = [
                vulnerability_record_from_osv(vuln)
                for vuln in raw_result.get("vulns", [])
                if isinstance(vuln, dict)
            ]

            all_results.append(
                OsvPackageResult(
                    ecosystem=query.ecosystem,
                    osv_ecosystem=query.osv_ecosystem,
                    package_name=query.package_name,
                    version=query.version,
                    file_path=query.file_path,
                    line_number=query.line_number,
                    vulnerability_count=len(vulnerabilities),
                    vulnerabilities=vulnerabilities,
                )
            )

    return all_results


def build_summary(
    target_path: str,
    total_dependencies_seen: int,
    queryable_dependencies: int,
    skipped_dependencies: int,
    package_results: list[OsvPackageResult],
    status: LookupStatus,
    error_message: str | None = None,
) -> OsvVulnerabilitySummary:
    vulnerable_dependencies = sum(
        1
        for result in package_results
        if result.vulnerability_count > 0
    )

    total_vulnerabilities = sum(
        result.vulnerability_count
        for result in package_results
    )

    return OsvVulnerabilitySummary(
        target_path=target_path,
        generated_at=utc_now(),
        total_dependencies_seen=total_dependencies_seen,
        queryable_dependencies=queryable_dependencies,
        skipped_dependencies=skipped_dependencies,
        vulnerable_dependencies=vulnerable_dependencies,
        total_vulnerabilities=total_vulnerabilities,
        online_lookup_status=status,
        error_message=error_message,
    )


def build_osv_vulnerability_report(
    target: str,
    online_lookup: bool = True,
    timeout_seconds: int = 10,
) -> OsvVulnerabilityReport:
    inventory = build_dependency_inventory(target)
    queries, skipped_results = build_osv_queries_from_inventory(inventory)

    if not queries:
        package_results = skipped_results

        return OsvVulnerabilityReport(
            summary=build_summary(
                target_path=target,
                total_dependencies_seen=inventory.summary.total_dependencies,
                queryable_dependencies=0,
                skipped_dependencies=len(skipped_results),
                package_results=package_results,
                status="NO_QUERYABLE_DEPENDENCIES",
            ),
            package_results=package_results,
        )

    placeholder_query_results = [
        empty_result_for_query(query)
        for query in queries
    ]

    if not online_lookup:
        package_results = placeholder_query_results + skipped_results

        return OsvVulnerabilityReport(
            summary=build_summary(
                target_path=target,
                total_dependencies_seen=inventory.summary.total_dependencies,
                queryable_dependencies=len(queries),
                skipped_dependencies=len(skipped_results),
                package_results=package_results,
                status="SKIPPED",
                error_message="Online OSV lookup was skipped by configuration.",
            ),
            package_results=package_results,
        )

    try:
        osv_results = query_osv_batch(
            queries=queries,
            timeout_seconds=timeout_seconds,
        )

        package_results = osv_results + skipped_results

        return OsvVulnerabilityReport(
            summary=build_summary(
                target_path=target,
                total_dependencies_seen=inventory.summary.total_dependencies,
                queryable_dependencies=len(queries),
                skipped_dependencies=len(skipped_results),
                package_results=package_results,
                status="COMPLETED",
            ),
            package_results=package_results,
        )

    except OsvLookupError as error:
        package_results = placeholder_query_results + skipped_results

        return OsvVulnerabilityReport(
            summary=build_summary(
                target_path=target,
                total_dependencies_seen=inventory.summary.total_dependencies,
                queryable_dependencies=len(queries),
                skipped_dependencies=len(skipped_results),
                package_results=package_results,
                status="FAILED",
                error_message=str(error),
            ),
            package_results=package_results,
        )


def generate_osv_report_json(report: OsvVulnerabilityReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2)


def write_osv_report_json(
    report: OsvVulnerabilityReport,
    output_path: str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_osv_report_json(report), encoding="utf-8")
    return path