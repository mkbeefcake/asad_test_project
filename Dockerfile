# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps
RUN apt-get update -y && apt-get install -y --no-install-recommends \
	build-essential \
	libpq-dev \
	&& rm -rf /var/lib/apt/lists/*

# Install deps
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
	&& pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose port for Cloud Run (uses PORT env)
ENV PORT=8080

# Gunicorn config (threads for Cloud Run, single worker)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 wsgi:app

