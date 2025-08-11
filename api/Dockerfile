# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project metadata first (leverage Docker layer cache)
COPY pyproject.toml README.md /app/

# Install runtime deps
RUN pip install --upgrade pip && pip install . && pip install plotly pandas

# Copy source
COPY app /app/app

# Variável para escolher processo (api | ui)
ENV APP_MODE=api

EXPOSE 8000 8501

# Entry-point flexível
# CMD ["bash", "-c", "if [ \"$APP_MODE\" = \"ui\" ]; then streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0; else uvicorn app.main:app --host 0.0.0.0 --port 8000; fi"]
CMD [""]