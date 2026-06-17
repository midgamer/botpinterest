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

# DEBUG: проверяем структуру и импорт app
RUN echo "=== PY FILES ===" && ls /app/*.py && echo "=== APP DIR ===" && ls -la /app/app/ && echo "=== BOT DIR ===" && ls /app/app/bot/handlers/ && echo "=== TRY IMPORT ===" && python -c "import sys; sys.path.insert(0,'/app'); from app.bot.handlers import start; print('IMPORT OK')" 2>&1 || echo "IMPORT FAILED"

EXPOSE 3000

CMD ["python", "server.py"]
