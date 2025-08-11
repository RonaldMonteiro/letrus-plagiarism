FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID ui && useradd -u $UID -g ui -m -s /bin/bash ui

USER ui
WORKDIR /app

COPY ui/pyproject.toml .

RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

COPY ./ui .

ARG HOST
ARG PORT
ENV HOST=${HOST:-0.0.0.0}
ENV PORT=${PORT:-8501}

CMD streamlit run app.py --server.port="${PORT}" --server.address="${HOST}"