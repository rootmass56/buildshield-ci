from pathlib import Path
import re
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


def _pyproject() -> dict:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


def test_h10b_freezes_python_package_version_at_1_0_0():
    data = _pyproject()

    assert data["project"]["version"] == "1.0.0"


def test_h8a_declares_required_python_quality_tools():
    data = _pyproject()
    dependencies = data["project"]["optional-dependencies"]["dev"]

    required_prefixes = (
        "build",
        "cyclonedx-bom",
        "mypy",
        "pytest-cov",
        "ruff",
    )

    for prefix in required_prefixes:
        assert any(
            dependency == prefix
            or dependency.startswith(f"{prefix}>")
            or dependency.startswith(f"{prefix}<")
            or dependency.startswith(f"{prefix}=")
            for dependency in dependencies
        )


def test_h8a_ruff_gate_targets_runtime_errors():
    data = _pyproject()

    assert data["tool"]["ruff"]["target-version"] == "py311"
    assert data["tool"]["ruff"]["lint"]["select"] == [
        "E9",
        "F63",
        "F7",
        "F82",
    ]


def test_h8a_mypy_baseline_checks_typed_code():
    data = _pyproject()
    config = data["tool"]["mypy"]

    assert config["python_version"] == "3.11"
    assert config["check_untyped_defs"] is True
    assert config["ignore_missing_imports"] is True
    assert config["warn_unused_configs"] is True


def test_h8a_coverage_uses_branch_measurement():
    data = _pyproject()
    coverage = data["tool"]["coverage"]

    assert coverage["run"]["branch"] is True
    assert coverage["run"]["source"] == ["supplysentinel"]
    assert coverage["report"]["show_missing"] is True

WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "buildshield-ci.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_h8d3_workflow_uses_job_scoped_least_privilege_permissions():
    content = _workflow_text()

    assert "\npermissions: {}\n" in content
    assert content.count("security-events: write") == 1
    assert content.count("actions: read") == 1
    assert content.count("contents: read") == 3
    assert "pull-requests: write" not in content
    assert "contents: write" not in content


def test_h8d3_workflow_actions_are_immutable_sha_pinned():
    content = _workflow_text()
    action_refs = re.findall(
        r"^\s*uses:\s*([^@\s]+)@([^\s#]+)",
        content,
        flags=re.MULTILINE,
    )

    assert len(action_refs) == 8
    assert {
        action
        for action, _ in action_refs
    } == {
        "actions/checkout",
        "actions/setup-python",
        "actions/setup-node",
        "github/codeql-action/upload-sarif",
        "actions/upload-artifact",
    }

    for _, ref in action_refs:
        assert re.fullmatch(r"[0-9a-f]{40}", ref)


def test_h8d3_workflow_consumes_hash_locked_python_environments():
    content = _workflow_text()

    assert (
        "--require-hashes \\\n"
        "            -r requirements/dev-py313-linux.lock.txt"
        in content
    )
    assert "requirements/runtime-py313-linux.lock.txt" in content
    assert "python -m build --wheel --sdist --outdir dist" in content
    assert "--no-deps" in content
    assert "pip check" in content
    assert 'pip install -e ".[dev]"' not in content
    assert "pip install --upgrade pip" not in content


def test_h8d3_workflow_runs_python_quality_coverage_and_fresh_wheel_gates():
    content = _workflow_text()

    for required in (
        "python -m ruff check src tests",
        "python -m mypy",
        "python -m pytest -q",
        "--cov=supplysentinel",
        "83.56708123842286",
        "buildshield-runtime",
        "expected installed wheel outside workspace",
    ):
        assert required in content


def test_h8d3_workflow_regenerates_and_validates_cyclonedx_graph():
    content = _workflow_text()

    assert content.count("cyclonedx-py environment") == 2
    assert "sbom/cyclonedx-python.json" in content
    assert "26 components" in content
    assert "27 dependency records" in content
    assert "6 root edges" in content
    assert "42 total edges" in content
    assert "0 unknown refs" in content


def test_h8d3_workflow_runs_supported_frontend_quality_stack():
    content = _workflow_text()

    assert "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020" in content
    assert 'node-version: "22.23.2"' in content
    assert "npm install --global npm@12.0.2 --no-audit --no-fund" in content
    assert "npm ci --ignore-scripts --no-audit --no-fund" in content
    assert "npm ls --all" in content
    assert "npm run lint" in content
    assert "npm run typecheck" in content
    assert "npm run test" in content
    assert "npm audit --audit-level=high" in content
    assert "npm run build" in content
    assert "--legacy-peer-deps" not in content


def test_h8d3_workflow_asserts_exact_controlled_benchmark():
    content = _workflow_text()

    for required in (
        'vulnerable_summary["findings_count"] != 22',
        'vulnerable_summary["critical_count"] != 4',
        'vulnerable_summary["high_count"] != 10',
        'vulnerable_summary["medium_count"] != 7',
        'vulnerable_summary["low_count"] != 1',
        'vulnerable_summary["security_score"] != 5',
        'secure_summary["findings_count"] != 0',
        'secure_summary["security_score"] != 100',
        'comparison["score_delta"] != 95',
        'comparison["findings_reduced"] != 22',
        '"SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED"',
    ):
        assert required in content


def test_post_release_workflow_runs_on_main_and_supports_manual_dispatch():
    content = _workflow_text()

    assert "- main" in content
    assert "- master" not in content
    assert "- upgrade/v0.13-security-hardening" not in content
    assert "pull_request:" in content
    assert "workflow_dispatch:" in content
