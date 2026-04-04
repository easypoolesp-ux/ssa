# =============================================================================
# Django — Dev Settings
# Responsibility: Local development overrides (SQLite, DEBUG on)
# =============================================================================

from .base import *  # noqa: F401, F403

DEBUG = True

# Use SQLite locally — no Cloud SQL needed for local dev
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Override SECRET_KEY for local use (never commit a real key)
SECRET_KEY = "local-dev-secret-key-not-for-production"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]
