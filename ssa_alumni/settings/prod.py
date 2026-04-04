# =============================================================================
# Django — Production Settings
# Responsibility: Cloud Run / Cloud SQL production overrides
# =============================================================================

from .base import *  # noqa: F401, F403

DEBUG = False

# Restrict to Cloud Run service URL (set via env var after first deploy)
CLOUD_RUN_URL = os.environ.get("CLOUD_RUN_URL", "")  # noqa: F405
ALLOWED_HOSTS = [CLOUD_RUN_URL, "localhost"] if CLOUD_RUN_URL else ["*"]

# CSRF — trust Cloud Run service URL
CSRF_TRUSTED_ORIGINS = [f"https://{CLOUD_RUN_URL}"] if CLOUD_RUN_URL else []

SECURE_SSL_REDIRECT     = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
