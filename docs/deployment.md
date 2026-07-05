# BuildShield-CI Deployment Guide

BuildShield-CI can run locally as a Python CLI/dashboard application or as a containerized DevSecOps dashboard using Docker.

## Deployment Modes

BuildShield-CI supports:

1. Local development mode
2. Docker container mode
3. Docker Compose mode
4. Cloud-ready container deployment

## Local Dashboard

Run locally:

    pip install -e .
    buildshield dashboard --host 127.0.0.1 --port 8080

Open:

    http://127.0.0.1:8080

## Docker Build

Build the image using docker build:

    docker build -t buildshield-ci:latest .

Run the container:

    docker run --rm -p 8080:8080 buildshield-ci:latest

Open:

    http://127.0.0.1:8080

## Docker Compose

Start the platform using docker compose up:

    docker compose up --build

Run in background:

    docker compose up --build -d

Check running services:

    docker compose ps

Stop:

    docker compose down

Stop and remove persistent volumes:

    docker compose down -v

## Persistent Data

Docker Compose creates two named volumes:

- buildshield_reports
- buildshield_data

These store:

- Generated reports
- Dashboard scan history
- SQLite database
- OSV intelligence reports
- SBOM-lite reports

## Health Check

The container exposes a health endpoint:

    /health

Expected response:

    {
      "status": "ok",
      "product": "BuildShield-CI",
      "version": "0.12.6"
    }

## Security Notes

The container runs as a non-root user named:

    buildshield

The dashboard binds to:

    0.0.0.0:8080

The Dockerfile includes a health check and avoids running the application as root.

## Cloud Deployment Readiness

This image can be deployed to platforms that support container workloads, such as:

- Render
- Railway
- Fly.io
- AWS ECS
- Azure Container Apps
- Google Cloud Run
- Kubernetes

For cloud deployment, expose port:

    8080

Use command:

    buildshield dashboard --host 0.0.0.0 --port 8080

## Recommended Demo Flow

1. Start dashboard using Docker Compose.
2. Open the dashboard.
3. Run vulnerable repository scan.
4. Run secure repository scan.
5. View findings.
6. View policy evaluation.
7. View SBOM inventory.
8. Run OSV vulnerability intelligence.
9. View scan history and risk trends.
10. Download generated reports.
