#!/bin/bash
# Start script for FastAPI backend
# Uses uv to ensure correct virtual environment

cd "$(dirname "$0")"

# Set PYTHONPATH to include backend directory (required for Docker/container environments)
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"

uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

