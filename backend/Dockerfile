# Multi-stage Dockerfile for FastAPI Backend
# syntax=docker/dockerfile:1

# Stage 1: Base with Python and uv
FROM python:3.12-slim AS base

# Install system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Stage 2: Dependencies
FROM base AS deps

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with cache mount
# Note: PyTorch pulls in CUDA libraries (~2GB) even for CPU usage
# This is because chronos-forecasting and darts require full PyTorch
# Build tools (gcc, g++) are only in this stage, not in final image
# Using cache mount to persist downloads between builds
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev

# Stage 3: Production
FROM python:3.12-slim AS runner

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    postgresql-client \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment directly from deps (skip intermediate builder stage)
# This saves disk space by avoiding duplicate .venv copy
COPY --from=deps --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Copy and set permissions for entrypoint and setup scripts
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
COPY --chown=appuser:appuser setup.sh /app/
RUN dos2unix /app/docker-entrypoint.sh /app/setup.sh && \
    chmod +x /app/docker-entrypoint.sh /app/setup.sh

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Start the application using entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
