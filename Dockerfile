FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BUILDSHIELD_HOST=0.0.0.0
ENV BUILDSHIELD_PORT=8080

WORKDIR /app

RUN addgroup --system buildshield && \
    adduser --system --ingroup buildshield buildshield

COPY pyproject.toml README.md ./
COPY src ./src
COPY docs ./docs
COPY samples ./samples
COPY buildshield-policy.yml ./

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -e .

RUN mkdir -p /app/reports /app/data && \
    chown -R buildshield:buildshield /app

USER buildshield

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"

CMD ["buildshield", "dashboard", "--host", "0.0.0.0", "--port", "8080"]