from __future__ import annotations

import gc
import inspect
import warnings

from supplysentinel.web import history


class _SerializableModel:
    def __init__(self, **values: object) -> None:
        self.__dict__.update(values)

    def model_dump(self, *, mode: str = "python") -> dict[str, object]:
        assert mode == "json"
        return dict(self.__dict__)


def test_history_connections_use_explicit_closing():
    source = inspect.getsource(history)

    assert "with sqlite3.connect(" not in source
    assert "from contextlib import closing" in source
    assert source.count("with closing(_connect_database()) as connection:") == 7


def test_history_lifecycle_emits_no_resource_warning(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    database_path = data_dir / "history.db"

    monkeypatch.setattr(history, "DATA_DIR", data_dir)
    monkeypatch.setattr(history, "DATABASE_PATH", database_path)

    summary = _SerializableModel(
        security_score=100,
        risk_level="LOW",
        findings_count=0,
        critical_count=0,
        high_count=0,
        medium_count=0,
        low_count=0,
        info_count=0,
    )
    risk_profile = _SerializableModel(build_gate_status="PASSED")

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", ResourceWarning)

        history.ensure_database()
        saved = history.save_scan_history(
            run_id="h8d1-resource-lifecycle",
            kind="scan",
            target_path="samples/secure-repo",
            summary=summary,
            risk_profile=risk_profile,
            policy_evaluation=None,
            reports=[],
        )

        assert saved["run_id"] == "h8d1-resource-lifecycle"
        assert len(history.get_recent_scan_history()) == 1
        assert len(history.get_risk_trend()) == 1

        retention = history.apply_history_retention()
        assert retention["max_rows"] >= 1

        assert (
            history.clear_report_metadata_for_runs(
                ["h8d1-resource-lifecycle"]
            )
            == 1
        )
        assert history.clear_scan_history()["deleted_rows"] == 1

        gc.collect()

    resource_warnings = [
        warning
        for warning in captured
        if issubclass(warning.category, ResourceWarning)
    ]

    assert resource_warnings == []


def test_tests_do_not_use_sqlite_connection_as_transaction_only_context():
    import ast
    from pathlib import Path

    tests_root = Path(__file__).resolve().parent
    offenders: list[str] = []

    for path in sorted(tests_root.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for node in ast.walk(tree):
            if not isinstance(node, ast.With):
                continue

            for item in node.items:
                expression = item.context_expr
                if not isinstance(expression, ast.Call):
                    continue

                function = expression.func
                if (
                    isinstance(function, ast.Attribute)
                    and function.attr == "connect"
                    and isinstance(function.value, ast.Name)
                    and function.value.id == "sqlite3"
                ):
                    offenders.append(f"{path.name}:{node.lineno}")

    assert offenders == []
