# =============================================================================
# Dockerfile — Multi-stage build for Django on Cloud Run
# Responsibility: Produce a lean production image
# =============================================================================

# ── Stage 1: dependency installer ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps for psycopg2 compilation (using binary avoids this, but kept for safety)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime image ──────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create non-root user for security
RUN useradd -m django-user && chown -R django-user:django-user /app
USER django-user

# Collect static files — use base settings (no DB/GCP auth needed at build time)
RUN SECRET_KEY=build-time-placeholder \
    DJANGO_SETTINGS_MODULE=ssa_alumni.settings.base \
    python manage.py collectstatic --noinput

EXPOSE 8080

# gunicorn: 2 workers per CPU, 1 thread, timeout 0 for Cloud Run
CMD exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers 2 \
    --threads 8 \
    --timeout 0 \
    ssa_alumni.wsgi:application
