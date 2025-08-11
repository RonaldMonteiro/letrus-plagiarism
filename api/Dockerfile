FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/cache/huggingface

# copy uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID api && useradd -u $UID -g api -m -s /bin/bash api

USER api
WORKDIR /app

# copy project metadata first (leverage Docker layer cache)
COPY api/pyproject.toml .

# Create virtual environment in .venv
RUN uv venv .venv

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"

# install runtime deps
RUN uv sync

# copy source
COPY api ./api

ARG HOST
ARG PORT
ENV HOST=${HOST:-0.0.0.0}
ENV PORT=${PORT:-8000}

EXPOSE $PORT

CMD ["uvicorn", "api.main:app", "--host", "$HOST", "--port", "$PORT"]