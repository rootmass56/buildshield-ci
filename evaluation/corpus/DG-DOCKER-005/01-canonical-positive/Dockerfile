FROM python:3.13.4-slim
RUN curl https://example.invalid/install.sh | bash
USER 10001
HEALTHCHECK CMD ["true"]
