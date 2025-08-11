# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface

# copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID ui && useradd -u $UID -g ui -m -s /bin/bash ui

USER ui
WORKDIR /app

# Copy project metadata first (leverage Docker layer cache)
COPY ui/pyproject.toml .

# Create virtual environment in .venv
RUN uv venv .venv

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Install runtime deps
RUN uv sync

# Copy source
COPY ./ui .

# Variável para escolher processo (api | ui)

ARG HOST
ARG PORT
ENV HOST=${HOST:-0.0.0.0}
ENV PORT=${PORT:-8501}

# Entry-point flexível
CMD ["streamlit", "run", "ui.app.py", "--server.port=$PORT", "--server.address=$HOST"]