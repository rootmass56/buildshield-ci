from __future__ import annotations

import json
from pathlib import Path

from supplysentinel.core.scanner import scan_repository


FULL_SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"


def _scan(tmp_path: Path, files: dict[str, str]):
    for relative_path, content in files.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    return scan_repository(str(tmp_path))


def _rule_ids(result) -> list[str]:
    return [finding.rule_id for finding in result.findings]


def _safe_docker(body: str) -> str:
    return (
        "FROM python:3.13.4-slim\n"
        f"{body.rstrip()}\n"
        "USER 10001\n"
        'HEALTHCHECK CMD ["true"]\n'
    )


def _workflow(run_line: str = 'echo "safe"') -> str:
    return (
        "name: h9d\n"
        "on:\n"
        "  pull_request:\n"
        "permissions:\n"
        "  contents: read\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        f"      - uses: actions/checkout@{FULL_SHA}\n"
        f"      - run: {run_line}\n"
    )


def test_h9d_docker_user_is_final_stage_aware(tmp_path: Path) -> None:
    result = _scan(
        tmp_path,
        {
            "Dockerfile": (
                "FROM python:3.13.4-slim AS builder\n"
                "USER app\n"
                "FROM python:3.13.4-slim\n"
                'HEALTHCHECK CMD ["true"]\n'
            ),
        },
    )

    assert "DG-DOCKER-002" in _rule_ids(result)


def test_h9d_docker_uid_gid_zero_is_root(tmp_path: Path) -> None:
    result = _scan(
        tmp_path,
        {
            "Dockerfile": (
                "FROM python:3.13.4-slim\n"
                "USER 0:0\n"
                'HEALTHCHECK CMD ["true"]\n'
            ),
        },
    )

    assert "DG-DOCKER-003" in _rule_ids(result)


def test_h9d_docker_secret_key_matching_avoids_policy_false_positive(
    tmp_path: Path,
) -> None:
    result = _scan(
        tmp_path,
        {
            "Dockerfile": _safe_docker(
                "ENV PASSWORD_POLICY=strict"
            ),
        },
    )

    assert "DG-DOCKER-004" not in _rule_ids(result)


def test_h9d_docker_shell_and_apt_variants_are_detected(
    tmp_path: Path,
) -> None:
    result = _scan(
        tmp_path,
        {
            "Dockerfile": _safe_docker(
                "RUN curl https://example.invalid/install.sh | /bin/sh\n"
                "RUN apt-get -y upgrade"
            ),
        },
    )

    rules = _rule_ids(result)
    assert "DG-DOCKER-005" in rules
    assert "DG-DOCKER-006" in rules


def test_h9d_healthcheck_is_final_stage_aware_and_none_disables_it(
    tmp_path: Path,
) -> None:
    first = _scan(
        tmp_path / "none",
        {
            "Dockerfile": (
                "FROM python:3.13.4-slim\n"
                "USER 10001\n"
                "HEALTHCHECK NONE\n"
            ),
        },
    )
    second = _scan(
        tmp_path / "multistage",
        {
            "Dockerfile": (
                "FROM python:3.13.4-slim AS builder\n"
                "HEALTHCHECK CMD true\n"
                "FROM python:3.13.4-slim\n"
                "USER 10001\n"
            ),
        },
    )

    assert "DG-DOCKER-007" in _rule_ids(first)
    assert "DG-DOCKER-007" in _rule_ids(second)


def test_h9d_github_quoted_write_all_is_detected(
    tmp_path: Path,
) -> None:
    result = _scan(
        tmp_path,
        {
            ".github/workflows/eval.yml": (
                "name: h9d\n"
                "on:\n"
                "  pull_request:\n"
                'permissions: "write-all"\n'
                "jobs:\n"
                "  test:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                f"      - uses: actions/checkout@{FULL_SHA}\n"
                '      - run: echo "safe"\n'
            ),
        },
    )

    assert "DG-GHA-002" in _rule_ids(result)


def test_h9d_github_shell_lexer_ignores_quoted_command_text(
    tmp_path: Path,
) -> None:
    result = _scan(
        tmp_path,
        {
            ".github/workflows/eval.yml": _workflow(
                'echo "curl https://example.invalid/x | bash"'
            ),
        },
    )

    assert "DG-GHA-003" not in _rule_ids(result)


def test_h9d_github_printf_secret_and_comments_are_handled(
    tmp_path: Path,
) -> None:
    workflow = _workflow(
        'printf "%s\\n" "${{ secrets.API_KEY }}"'
    ).replace(
        "permissions:\n",
        "# pull_request_target:\npermissions:\n",
    )
    result = _scan(
        tmp_path,
        {".github/workflows/eval.yml": workflow},
    )

    rules = _rule_ids(result)
    assert "DG-GHA-004" in rules
    assert "DG-GHA-005" not in rules


def test_h9d_npm_internal_name_matching_is_token_aware(
    tmp_path: Path,
) -> None:
    package = {
        "name": "h9d",
        "version": "1.0.0",
        "dependencies": {
            "oauth-client": "1.2.3",
        },
    }
    lock = {
        "name": "h9d",
        "version": "1.0.0",
        "lockfileVersion": 3,
        "packages": {
            "": {
                "name": "h9d",
                "version": "1.0.0",
            },
        },
    }

    result = _scan(
        tmp_path,
        {
            "package.json": json.dumps(package),
            "package-lock.json": json.dumps(lock),
        },
    )

    assert "DG-NPM-004" not in _rule_ids(result)


def test_h9d_python_extra_index_and_markers_preserve_confusion_safety(
    tmp_path: Path,
) -> None:
    confusion = _scan(
        tmp_path / "confusion",
        {
            "requirements.txt": (
                "--extra-index-url "
                "https://packages.company.invalid/simple\n"
                "internal-auth==1.2.3\n"
            ),
        },
    )
    marker = _scan(
        tmp_path / "marker",
        {
            "requirements.txt": (
                'requests==2.32.3; python_version >= "3.10"\n'
            ),
        },
    )

    assert "DG-PY-003" in _rule_ids(confusion)
    assert "DG-PY-001" not in _rule_ids(marker)
    assert "DG-PY-002" not in _rule_ids(marker)
