FROM node:22.15.0-bookworm-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci --ignore-scripts --no-audit --no-fund && \
    mkdir -p /tmp/native-packages && \
    install_native_package() { \
        package_spec="$1"; \
        destination="$2"; \
        mkdir -p "$destination"; \
        archive="$(npm pack "$package_spec" \
            --pack-destination /tmp/native-packages \
            --silent)"; \
        tar -xzf "/tmp/native-packages/$archive" \
            --strip-components=1 \
            -C "$destination"; \
    }; \
    install_native_package \
        "@typescript/typescript-linux-x64@7.0.2" \
        "node_modules/@typescript/typescript-linux-x64"; \
    install_native_package \
        "@rolldown/binding-linux-x64-gnu@1.2.8" \
        "node_modules/@rolldown/binding-linux-x64-gnu"; \
    install_native_package \
        "lightningcss-linux-x64-gnu@1.33.0" \
        "node_modules/lightningcss-linux-x64-gnu"; \
    test -x node_modules/@typescript/typescript-linux-x64/lib/tsc && \
    test -d node_modules/@rolldown/binding-linux-x64-gnu && \
    test -d node_modules/lightningcss-linux-x64-gnu && \
    node -e "import('rolldown').then(() => console.log('ROLLDOWN NATIVE: PASS'))" && \
    rm -rf /tmp/native-packages

COPY frontend/ ./

RUN npm run build


FROM python:3.13-slim AS python-builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip wheel --wheel-dir /wheels .


FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV BUILDSHIELD_HOST=0.0.0.0
ENV BUILDSHIELD_PORT=8080
ENV BUILDSHIELD_ENV=production
ENV BUILDSHIELD_WORKSPACE_ROOT=/app

WORKDIR /app

RUN groupadd --gid 10001 buildshield && \
    useradd \
        --uid 10001 \
        --gid 10001 \
        --no-create-home \
        --home-dir /nonexistent \
        --shell /usr/sbin/nologin \
        buildshield && \
    mkdir -p /app/reports/dashboard /app/data && \
    chown -R 10001:10001 /app/reports /app/data

COPY --from=python-builder /wheels /wheels

RUN python -m pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

COPY buildshield-policy.yml ./
COPY samples ./samples
COPY docs ./docs
COPY --from=frontend-builder /frontend/dist ./frontend/dist

USER 10001:10001

EXPOSE 8080

STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/ready', timeout=3)"

CMD ["buildshield", "dashboard", "--host", "0.0.0.0", "--port", "8080"]
