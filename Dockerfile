# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (uvicorn needs build base for some wheels occasionally)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy requirement files first (for caching)
COPY requirements.txt ./requirements.txt
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
RUN pip install uvicorn fastapi

# Copy source
COPY . .

# Ensure start script is executable
RUN chmod +x docker/start.sh

EXPOSE 8000
ENV HOST=0.0.0.0 PORT=8000

# Allow override via APP_MODULE, otherwise auto-detect in start_app.py
CMD ["bash", "docker/start.sh"]
