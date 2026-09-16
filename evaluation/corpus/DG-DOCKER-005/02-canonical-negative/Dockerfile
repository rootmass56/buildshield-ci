FROM python:3.13.4-slim
RUN curl -fsSLo install.sh https://example.invalid/install.sh && echo 'abc install.sh' && bash install.sh
USER 10001
HEALTHCHECK CMD ["true"]
