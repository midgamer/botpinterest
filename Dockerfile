FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/app/data \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN grep -v '^from ' requirements.txt | grep -v '^import ' > /tmp/req_clean.txt \
    && mv /tmp/req_clean.txt requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs \
    /app/app/images/generated /app/app/images/charts

EXPOSE 3000

CMD ["python", "server.py"]
