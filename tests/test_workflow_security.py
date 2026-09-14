from __future__ import annotations

import re
from pathlib import Path


FULL_SHA = re.compile(r"^[a-fA-F0-9]{40}$")


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def workflow_path() -> Path:
    return project_root() / ".github" / "workflows" / "buildshield-ci.yml"


def test_external_github_actions_are_pinned_to_full_commit_shas() -> None:
    path = workflow_path()
    assert path.exists(), f"Workflow not found: {path}"

    uses_lines: list[tuple[int, str]] = []

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(),
        start=1,
    ):
        stripped = raw_line.strip()

        if not stripped.startswith("uses:"):
            continue

        uses_value = stripped.removeprefix("uses:").strip()
        uses_lines.append((line_number, uses_value))

    assert uses_lines, "Expected at least one GitHub Action reference."

    violations: list[str] = []

    for line_number, uses_value in uses_lines:
        # Local repository actions do not require a remote commit SHA.
        if uses_value.startswith("./"):
            continue

        reference_without_comment = uses_value.split("#", maxsplit=1)[0].strip()

        if "@" not in reference_without_comment:
            violations.append(
                f"line {line_number}: missing @ref in '{uses_value}'"
            )
            continue

        action_name, action_ref = reference_without_comment.rsplit("@", maxsplit=1)

        if not action_name or not FULL_SHA.fullmatch(action_ref):
            violations.append(
                f"line {line_number}: external action is not pinned "
                f"to a full 40-character commit SHA: '{uses_value}'"
            )

    assert not violations, "\n".join(violations)
