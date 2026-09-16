# BuildShield-CI Deployment Guide

BuildShield-CI supports local execution and controlled single-instance container deployment using Docker and Docker Compose.

## Deployment Modes

1. Local Python CLI/dashboard
2. Hardened Docker container
3. Docker Compose with persistent application state
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

Protected dashboard/API operations require the H2 authentication environment configuration at runtime. Real credentials or password hashes must not be baked into the image.

## H7A Container Image Security

The H7A image uses a **Multi-stage production image** design.

The frontend stage:
- uses Node 22.15.0 on a Debian/glibc builder image;
- installs the checked-in dependency graph with `npm ci`;
- retrieves all Linux x64 native packages currently omitted by the Windows-generated lockfile using exact pinned `npm pack` payloads: TypeScript `7.0.2`, Rolldown `1.2.8`, and Lightning CSS `1.33.0`;
- extracts those package payloads directly into their expected optional-dependency locations without a second dependency-tree install or lockfile mutation;
- ignores lifecycle scripts during dependency installation;
- verifies the native Linux TypeScript compiler and Rolldown binding before the TypeScript/Vite frontend production build;
- contributes only the generated `frontend/dist` output to the Python runtime image.

The Python build stage:
- builds BuildShield-CI and its Python dependencies as wheels;
- keeps build activity outside the final runtime stage.

The runtime stage:
- uses a dedicated unprivileged account with UID/GID `10001:10001`;
- uses `/nonexistent` as the account home and a non-login shell;
- performs a non-editable wheel installation;
- does not copy the project source tree into `/app/src`;
- copies only runtime project assets needed by the application;
- includes the frontend production build;
- pre-creates `/app/reports/dashboard` and `/app/data` as application-owned writable locations;
- leaves application code/assets root-owned and read-only to the application user under normal container permissions;
- disables Python bytecode generation;
- uses unbuffered Python output;
- includes a health check and `SIGTERM` stop signal.

The build context excludes local virtual environments, runtime data/reports, test files, frontend `node_modules`, local frontend build output, editor files, caches, and secrets such as `.env`.

## Docker Compose

The H7B Compose configuration hardens the controlled single-instance runtime.

```powershell
docker compose build --pull
docker compose up -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8080/health
docker compose down
```

Remove persistent volumes only when intentionally discarding local state:

```powershell
docker compose down -v
```

### H7B Compose Least-Privilege Controls

The Compose service now enforces:

- explicit runtime identity `10001:10001`;
- `read_only: true` for the container root filesystem;
- `cap_drop: ALL`;
- `no-new-privileges:true`;
- Docker init process handling with `init: true`;
- PID limit of 256;
- 15-second graceful-stop window;
- localhost-only port publication with default `127.0.0.1:8080`, while allowing `BUILDSHIELD_HOST_PORT` to select another localhost host port when 8080 is already occupied;
- writable named volumes only for `/app/reports` and `/app/data`;
- a bounded 64 MiB `/tmp` tmpfs with `noexec`, `nosuid`, and `nodev`;
- `TMPDIR=/tmp`.

The application can therefore persist reports/history while its code, installed packages, frontend assets, policy file, and other root-filesystem content remain read-only at runtime.

Publishing only to `127.0.0.1` is deliberate for the controlled deployment model. External access should be provided by an explicitly configured reverse proxy, ingress, tunnel, or container platform rather than exposing the development/demo service directly on every host interface.

The default host port remains `8080`. If that host port is already occupied, keep the unrelated local service untouched and override only the host-side Compose publication:

```powershell
$env:BUILDSHIELD_HOST_PORT = "18080"
docker compose up -d
Invoke-RestMethod http://127.0.0.1:18080/ready
```

The container still listens internally on port `8080`; only the localhost host-side publication changes.

CPU and memory ceilings remain environment-specific rather than hard-coded in the default Compose file. Application-level request/concurrency/scanner budgets remain enforced by H4, and platform-specific CPU/memory limits can be layered on for the target host or orchestrator.

## Persistent Data

Compose defines:

- `buildshield_reports`
- `buildshield_data`

They are used for generated reports and application data such as SQLite history.

## Health Endpoint

Expected shape:

```json
{
  "status": "ok",
  "product": "BuildShield-CI",
  "version": "1.0.0"
}
```

The health endpoint version is sourced from BuildShield-CI package metadata.

## Secret and Configuration Boundary

The container image contains no deployment password or session secret values.

Deployment-specific authentication and runtime configuration must be supplied at runtime, preferably through an orchestrator/platform secret mechanism where available.

The checked-in `.env.example` contains examples/placeholders only and is not a production secret store.

## Cloud Deployment Readiness

The image is intended for controlled demonstrations, lab deployment, and a controlled single-instance deployment model.

It should not be described as enterprise multi-tenant SaaS or as universally production-hardened. Internet-facing deployment still requires environment-specific controls such as TLS termination, platform secret management, ingress/network policy, centralized observability, backup/recovery, image lifecycle management, and incident-response procedures.

With suitable environment-specific controls, the OCI image can be adapted to managed container platforms. No specific cloud platform is claimed as production-validated until it has been tested in that environment.

### H7A TypeScript 7 Linux builder note

The checked-in frontend lockfile was generated on Windows and currently omits the Linux x64 optional package required by TypeScript 7. The first H7A Linux build therefore failed when `tsc` could not resolve `@typescript/typescript-linux-x64`.

A follow-up attempt used a second `npm install` after `npm ci`, but npm 10.9.2 failed internally while rebuilding the dependency graph (`edgesOut`). H7A therefore does not perform a second install. The builder uses `npm pack` for the exact platform package and extracts the verified package payload into TypeScript's expected optional-dependency path. This is a builder-only compatibility measure.

H8 remains responsible for normalizing/regenerating the frontend lockfile for cross-platform reproducibility.

### H7A complete Linux-native optional-dependency repair

The latest Docker failure confirmed that the Windows-generated lockfile problem is broader than TypeScript. TypeScript successfully reached the Vite phase, after which Rolldown failed because `@rolldown/binding-linux-x64-gnu` was absent. The checked-in lockfile records the Windows Rolldown binding while Rolldown itself declares the Linux x64 GNU binding at the same `1.2.8` version. The lockfile likewise contains the Windows Lightning CSS binding while declaring `lightningcss-linux-x64-gnu` at `1.33.0`.

H7A therefore installs the complete set of Linux x64 native optional packages currently required by this frontend build using exact package versions already implied by the dependency graph:

- `@typescript/typescript-linux-x64@7.0.2`
- `@rolldown/binding-linux-x64-gnu@1.2.8`
- `lightningcss-linux-x64-gnu@1.33.0`

These are retrieved with `npm pack` and extracted directly. No second `npm install` is used, so the npm 10.9.2 `edgesOut` failure path is avoided. H8 will replace this compatibility measure with a normalized cross-platform lockfile.


## H7C Runtime Configuration and Readiness

H7C separates process liveness from deployment readiness:

- `/health` is a lightweight liveness endpoint.
- `/ready` is the production readiness endpoint. In production it validates authentication configuration, workspace root, React production assets, and writable report/data locations.

The Dockerfile and Compose health checks use `/ready`, not `/health`.

### Fail-Closed Production Startup

When `BUILDSHIELD_ENV=production`, startup requires:

- `BUILDSHIELD_ADMIN_USERNAME`
- `BUILDSHIELD_ADMIN_PASSWORD_HASH`
- `BUILDSHIELD_COOKIE_SECURE`
- `BUILDSHIELD_WORKSPACE_ROOT`

The password hash must satisfy the existing H2 PBKDF2 contract. Missing or invalid production authentication configuration prevents the service from becoming ready.

Compose also requires administrator username and password hash interpolation, so deployment cannot silently start without administrator credentials.

### Generate an Administrator Password Hash

```powershell
python -c "from supplysentinel.web.auth import hash_password; import getpass; print(hash_password(getpass.getpass('Admin password: ')))"
```

Then provide the values through the runtime environment or deployment secret-management layer:

```powershell
$env:BUILDSHIELD_ADMIN_USERNAME = "admin"
$env:BUILDSHIELD_ADMIN_PASSWORD_HASH = "<generated PBKDF2 hash>"
```

For the localhost HTTP demonstration profile:

```powershell
$env:BUILDSHIELD_COOKIE_SECURE = "false"
```

For browser access over HTTPS/TLS termination:

```powershell
$env:BUILDSHIELD_COOKIE_SECURE = "true"
```

Do not commit a real administrator password or password hash into `.env.example`, Compose YAML, Dockerfile, source code, or documentation.

### Workspace Boundary

The production container explicitly fixes `BUILDSHIELD_WORKSPACE_ROOT=/app`, making H1's workspace trust boundary independent of the process working directory.

### Restart and Shutdown

Compose retains `init: true`, `SIGTERM`, and a 15-second stop grace period. H7C validation performs a real restart, verifies readiness recovery, then performs a bounded graceful stop and verifies a clean exit.

The H7 checkpoint is created only after H7D.

### H7C port-preservation correction

H7C must preserve H7B's configurable localhost host-port behavior. An intermediate H7C candidate accidentally restored a fixed `127.0.0.1:8080:8080` mapping while the H7C validation script correctly selected port 18080 because 8080 was occupied. That mismatch caused Docker to attempt binding 8080 anyway.

The corrected H7C Compose file uses `127.0.0.1:${BUILDSHIELD_HOST_PORT:-8080}:8080`, so the validated free localhost port is the port Docker actually publishes. The correction does not weaken H7B's localhost-only exposure boundary.
