# ============================================================
# AutoInvestor Intelligence System - Backend Dockerfile
# Multi-stage build for production
# ============================================================

# ── Stage 1: Build dependencies ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# System dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip wheel && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Labels
LABEL maintainer="AutoInvestor Team"
LABEL version="1.0.0"
LABEL description="AutoInvestor Intelligence System Backend"

# Create non-root user for security
RUN groupadd --gid 1000 autoinvestor && \
    useradd --uid 1000 --gid autoinvestor --shell /bin/bash --create-home autoinvestor

WORKDIR /app

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=autoinvestor:autoinvestor . .

# Create necessary directories
RUN mkdir -p /app/model_store /app/logs && \
    chown -R autoinvestor:autoinvestor /app

# Switch to non-root user
USER autoinvestor

# Environment variables (override with docker-compose or K8s secrets)
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    MODEL_STORE_PATH=/app/model_store

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop", "--http", "httptools"]
