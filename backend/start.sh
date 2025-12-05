#!/bin/bash
# Start script for FastAPI backend
# Uses uv to ensure correct virtual environment

cd "$(dirname "$0")"
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

