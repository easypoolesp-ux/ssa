# =============================================================================
# Django — Dev Settings
# Responsibility: Local development overrides ONLY.
#                 SQLite DB, DEBUG on, relaxed CORS.
# =============================================================================

from .base import *  # noqa: F401, F403
import os

DEBUG = True

# Override to a hardcoded key for local dev only
SECRET_KEY = os.environ.get("SECRET_KEY", "local-dev-secret-key-not-for-production")  # noqa: S105

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Local SQLite — no Cloud SQL connector needed
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Allow all origins locally
CORS_ALLOW_ALL_ORIGINS = True

# Bypass Firebase auth in dev — set SKIP_FIREBASE_AUTH=true env var
# (handled in FirebaseAuthentication class)
