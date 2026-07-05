FROM python:3.11.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --requirement requirements.txt

COPY . .

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

USER appuser

HEALTHCHECK CMD python -c "print('healthy')" || exit 1

CMD ["python", "app.py"]
