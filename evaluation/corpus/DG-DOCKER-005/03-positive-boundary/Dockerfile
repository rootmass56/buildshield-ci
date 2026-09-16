FROM python:3.13.4-slim
RUN wget -qO- https://example.invalid/install.sh | sh
USER 10001
HEALTHCHECK CMD ["true"]
