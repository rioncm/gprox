FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TMPDIR=/tmp

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | tee /etc/apt/keyrings/cloud.google.gpg > /dev/null && \
    echo "deb [signed-by=/etc/apt/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home --shell /usr/sbin/nologin gprox && \
    mkdir -p /etc/gprox && \
    mkdir -p /tmp && chmod 1777 /tmp && \
    chown -R gprox:gprox /app /etc/gprox /tmp

USER gprox

EXPOSE 8888

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8888", "--worker-tmp-dir", "/tmp", "app.main:app"]
