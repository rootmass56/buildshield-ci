from typer.testing import CliRunner

from supplysentinel.cli import app


runner = CliRunner()


def test_cli_secure_repo_policy_passes(secure_repo, policy_file):
    result = runner.invoke(
        app,
        [
            "scan",
            str(secure_repo),
            "--policy",
            str(policy_file),
            "--fail-on-policy",
            "--hide-files",
        ],
    )

    assert result.exit_code == 0
    assert "Policy passed" in result.output


def test_cli_vulnerable_repo_policy_fails(vulnerable_repo, policy_file):
    result = runner.invoke(
        app,
        [
            "scan",
            str(vulnerable_repo),
            "--policy",
            str(policy_file),
            "--fail-on-policy",
            "--hide-files",
        ],
    )

    assert result.exit_code == 2
    assert "Policy failed" in result.output