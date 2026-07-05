from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_dockerfile_exists_and_uses_non_root_user():
    dockerfile = project_root() / "Dockerfile"

    assert dockerfile.exists()

    content = dockerfile.read_text(encoding="utf-8")

    assert "FROM python:3.13-slim" in content
    assert "USER buildshield" in content
    assert "EXPOSE 8080" in content
    assert "HEALTHCHECK" in content
    assert "buildshield" in content
    assert "dashboard" in content


def test_docker_compose_exists_with_persistent_volumes():
    compose_file = project_root() / "docker-compose.yml"

    assert compose_file.exists()

    content = compose_file.read_text(encoding="utf-8")

    assert "buildshield-ci" in content
    assert "8080:8080" in content
    assert "buildshield_reports" in content
    assert "buildshield_data" in content
    assert "restart: unless-stopped" in content


def test_dockerignore_excludes_local_runtime_artifacts():
    dockerignore = project_root() / ".dockerignore"

    assert dockerignore.exists()

    content = dockerignore.read_text(encoding="utf-8")

    assert ".venv" in content
    assert "reports" in content
    assert "data" in content
    assert "__pycache__" in content


def test_env_example_exists():
    env_example = project_root() / ".env.example"

    assert env_example.exists()

    content = env_example.read_text(encoding="utf-8")

    assert "BUILDSHIELD_HOST" in content
    assert "BUILDSHIELD_PORT" in content
    assert "BUILDSHIELD_ENV" in content


def test_deployment_documentation_exists():
    deployment_doc = project_root() / "docs" / "deployment.md"

    assert deployment_doc.exists()

    content = deployment_doc.read_text(encoding="utf-8")

    assert "BuildShield-CI Deployment Guide" in content
    assert "docker build" in content
    assert "docker compose up" in content
    assert "Cloud Deployment Readiness" in content
