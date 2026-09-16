from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_dockerfile_uses_multistage_frontend_and_python_builds():
    dockerfile = project_root() / "Dockerfile"

    assert dockerfile.exists()

    content = dockerfile.read_text(encoding="utf-8")

    assert "FROM node:22.23.2-bookworm-slim AS frontend-builder" in content
    assert "npm install --global npm@12.0.2 --no-audit --no-fund" in content
    assert "npm ci --ignore-scripts --no-audit --no-fund" in content
    assert "npm ls --all" in content
    assert "--legacy-peer-deps" not in content
    assert "npm run typecheck && npm run build" in content

    # H8C removes the H7 temporary native-package injection workaround.
    assert "npm pack" not in content
    assert "install_native_package" not in content
    assert "@typescript/typescript-linux-x64@7.0.2" not in content
    assert "@rolldown/binding-linux-x64-gnu@1.2.8" not in content
    assert "lightningcss-linux-x64-gnu@1.33.0" not in content
    assert "--pack-destination /tmp/native-packages" not in content
    assert "--package-lock=false" not in content

    assert "FROM python:3.13-slim AS python-builder" in content
    assert "COPY pyproject.toml README.md LICENSE ./" in content
    assert (
        "python -m pip wheel --no-deps --wheel-dir /wheels ."
        in content
    )
    assert "FROM python:3.13-slim AS runtime" in content
    assert (
        "COPY --from=frontend-builder /frontend/dist ./frontend/dist"
        in content
    )


def test_dockerfile_runtime_is_non_root_and_not_editable_install():
    content = (
        project_root() / "Dockerfile"
    ).read_text(encoding="utf-8")

    assert "USER 10001:10001" in content
    assert "--uid 10001" in content
    assert "--gid 10001" in content
    assert "--no-create-home" in content
    assert "--shell /usr/sbin/nologin" in content
    assert (
        "COPY requirements/runtime-py313-linux.lock.txt "
        "/tmp/runtime-py313-linux.lock.txt"
        in content
    )
    assert "--require-hashes" in content
    assert "-r /tmp/runtime-py313-linux.lock.txt" in content
    assert (
        "pip install --no-cache-dir --no-deps /wheels/*.whl"
        in content
    )
    assert "python -m pip check" in content
    assert "pip install --no-cache-dir -e ." not in content
    assert "pip install -e ." not in content
    assert "chown -R buildshield:buildshield /app" not in content


def test_dockerfile_limits_writable_application_directories():
    content = (
        project_root() / "Dockerfile"
    ).read_text(encoding="utf-8")

    assert "mkdir -p /app/reports/dashboard /app/data" in content
    assert "chown -R 10001:10001 /app/reports /app/data" in content
    assert "STOPSIGNAL SIGTERM" in content
    assert "EXPOSE 8080" in content
    assert "HEALTHCHECK" in content
    assert "http://127.0.0.1:8080/ready" in content
    assert "ENV BUILDSHIELD_WORKSPACE_ROOT=/app" in content
    assert 'CMD ["buildshield", "dashboard"' in content


def test_dockerignore_excludes_local_and_frontend_build_artifacts():
    dockerignore = project_root() / ".dockerignore"

    assert dockerignore.exists()

    content = dockerignore.read_text(encoding="utf-8")

    for expected in [
        ".venv",
        "reports",
        "data",
        "__pycache__",
        "frontend/node_modules",
        "frontend/dist",
        "frontend/coverage",
    ]:
        assert expected in content


def test_docker_compose_exists_with_persistent_volumes():
    compose_file = project_root() / "docker-compose.yml"

    assert compose_file.exists()

    content = compose_file.read_text(encoding="utf-8")

    assert "buildshield-ci" in content
    assert '127.0.0.1:${BUILDSHIELD_HOST_PORT:-8080}:8080' in content
    assert "buildshield_reports" in content
    assert "buildshield_data" in content
    assert "restart: unless-stopped" in content


def test_docker_compose_enforces_least_privilege_runtime():
    content = (
        project_root() / "docker-compose.yml"
    ).read_text(encoding="utf-8")

    assert 'user: "10001:10001"' in content
    assert "init: true" in content
    assert "read_only: true" in content
    assert "cap_drop:" in content
    assert "- ALL" in content
    assert "no-new-privileges:true" in content
    assert "pids_limit: 256" in content
    assert "stop_grace_period: 15s" in content


def test_docker_compose_limits_writable_runtime_paths():
    content = (
        project_root() / "docker-compose.yml"
    ).read_text(encoding="utf-8")

    assert "buildshield_reports:/app/reports:rw" in content
    assert "buildshield_data:/app/data:rw" in content
    assert "/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777" in content
    assert 'TMPDIR: "/tmp"' in content


def test_env_example_exists():
    env_example = project_root() / ".env.example"

    assert env_example.exists()

    content = env_example.read_text(encoding="utf-8")

    assert "BUILDSHIELD_HOST" in content
    assert "BUILDSHIELD_PORT" in content
    assert "BUILDSHIELD_ENV" in content


def test_deployment_documentation_matches_current_container_controls():
    deployment_doc = project_root() / "docs" / "deployment.md"

    assert deployment_doc.exists()

    content = deployment_doc.read_text(encoding="utf-8")

    assert "BuildShield-CI Deployment Guide" in content
    assert "docker build" in content
    assert "docker compose up" in content
    assert "Cloud Deployment Readiness" in content
    assert "multi-stage production build" in content
    assert "UID/GID `10001:10001`" in content
    assert "frontend production build" in content
    assert "non-editably with `--no-deps`" in content
    assert "Node 22.23.2" in content
    assert "npm 12.0.2" in content
    assert "hash-locked" in content
    assert "Node 22.15.0" not in content
    assert "@typescript/typescript-linux-x64@7.0.2" not in content


def test_h7c_compose_requires_runtime_auth_and_uses_readiness():
    content = (
        project_root() / "docker-compose.yml"
    ).read_text(encoding="utf-8")

    assert (
        'BUILDSHIELD_ADMIN_USERNAME: '
        '"${BUILDSHIELD_ADMIN_USERNAME:?Set BUILDSHIELD_ADMIN_USERNAME}"'
        in content
    )
    assert (
        'BUILDSHIELD_ADMIN_PASSWORD_HASH: '
        '"${BUILDSHIELD_ADMIN_PASSWORD_HASH:?Set '
        'BUILDSHIELD_ADMIN_PASSWORD_HASH}"'
        in content
    )
    assert (
        'BUILDSHIELD_COOKIE_SECURE: '
        '"${BUILDSHIELD_COOKIE_SECURE:-false}"'
        in content
    )
    assert 'BUILDSHIELD_WORKSPACE_ROOT: "/app"' in content
    assert "http://127.0.0.1:8080/ready" in content


def test_h7c_env_example_marks_runtime_security_boundary():
    content = (
        project_root() / ".env.example"
    ).read_text(encoding="utf-8")

    assert "BUILDSHIELD_HOST_PORT=8080" in content
    assert "BUILDSHIELD_WORKSPACE_ROOT=/app" in content
    assert "REPLACE_WITH_GENERATED_PBKDF2_HASH" in content
    assert "Never commit a real password or production hash." in content
