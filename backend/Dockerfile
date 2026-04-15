# python:3.10-slim ships multi-arch manifests (amd64 + arm64).
# Docker Desktop on Apple Silicon pulls the arm64 variant automatically —
# no `platform: linux/amd64` override needed.
FROM python:3.10-slim

# ── System packages ────────────────────────────────────────────────────────
# build-essential + gcc + libpq-dev are required to compile psycopg2,
# cryptography wheels, and any other C-extension packages.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Python runtime flags ───────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # /app is the root of the backend package tree so that
    # `from common.models import ...` and `from apps.X import ...` resolve.
    PYTHONPATH=/app

WORKDIR /app

# ── Dependency layer (cached unless requirements.txt changes) ──────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application source ─────────────────────────────────────────────────────
# Everything inside backend/ lands at /app:
#   /app/main.py
#   /app/config.py
#   /app/common/
#   /app/apps/
#   /app/migrations/
#   /app/alembic.ini
COPY . .

# Port exposed by the FastAPI/uvicorn process
EXPOSE 8000

# Default command — overridden per-service in docker-compose.yml
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
