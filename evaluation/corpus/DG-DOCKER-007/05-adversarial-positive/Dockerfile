FROM python:3.13.4-slim AS builder
HEALTHCHECK CMD test -f /tmp/builder-ready
RUN echo build
FROM python:3.13.4-slim
USER 10001
