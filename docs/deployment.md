# BuildShield-CI Deployment Guide

BuildShield-CI supports local execution and controlled container deployment using Docker and Docker Compose.

## Deployment Modes

1. Local Python CLI/dashboard
2. Docker container
3. Docker Compose with persistent volumes
4. Container-platform deployment after environment-specific hardening

## Local Dashboard

```powershell
pip install -e ".[dev]"
buildshield dashboard --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080
```

## Docker

Build:

```powershell
docker build -t buildshield-ci:latest .
```

Run:

```powershell
docker run --rm -p 8080:8080 buildshield-ci:latest
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
```

## Docker Compose

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8080/health
docker compose down
```

Remove persistent volumes only when intentionally discarding local state:

```powershell
docker compose down -v
```

## Persistent Data

Compose defines:

- `buildshield_reports`
- `buildshield_data`

They are used for generated reports and application data such as SQLite history.

## Container Security Controls

The current Docker setup includes:

- Dedicated non-root `buildshield` user
- Port 8080
- Health check
- Reduced Docker build context through `.dockerignore`
- Persistent volumes through Compose

## Health Endpoint

Expected shape:

```json
{
  "status": "ok",
  "product": "BuildShield-CI",
  "version": "0.12.6"
}
```

The version will change when the maintenance release is finalized.

## Cloud Deployment Readiness

The image is suitable for controlled demonstrations, local lab deployment, and further platform integration.

It should not be described as fully enterprise production-hardened without additional controls. A real internet-facing or multi-user deployment should add, as appropriate:

- Authentication
- Authorization / RBAC
- TLS termination
- Secret management
- Network policy / firewalling
- Rate limiting
- Request-size/time limits
- Audit logging
- Centralized observability
- Backup and recovery
- Dependency/image lifecycle management
- Tenant/repository isolation
- Security monitoring and incident response procedures

With the required environment-specific hardening, the image can be adapted to container platforms such as AWS ECS, Azure Container Apps, Google Cloud Run, Kubernetes, and other OCI-compatible services.

No specific cloud platform is claimed as production-validated until tested in that environment.
