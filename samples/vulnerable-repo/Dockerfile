FROM python:latest

ARG API_TOKEN=super-secret-token
ENV AWS_SECRET_ACCESS_KEY=dummy-secret-value

WORKDIR /app

RUN apt-get update && apt-get upgrade -y
RUN curl http://example.com/install.sh | bash

COPY . .

CMD ["python", "app.py"]
