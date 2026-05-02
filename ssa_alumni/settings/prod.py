# =============================================================================
# Django — Production Settings
# Responsibility: Cloud Run / Cloud SQL overrides ONLY.
#                 Passwordless IAM auth via Unix socket (Google standard pattern).
# =============================================================================

from .base import *  # noqa: F401, F403
import os

DEBUG = False

CLOUD_RUN_URL = os.environ.get("CLOUD_RUN_URL", "ssa-alumni-dev-685527496529.asia-south1.run.app")
ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    f"https://{CLOUD_RUN_URL}",
    "https://ssa-alumni-dev-685527496529.asia-south1.run.app",
    "https://ssa-alumni-dev-m5bdpqwnfq-el.a.run.app",
    "https://ssa-alumni.web.app",
]

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# GCS_BUCKET_NAME is read by base.py → defaults to "ssa-alumni-media"
# Override via Cloud Run env var: GCS_BUCKET_NAME=ssa-alumni-media

# ---------------------------------------------------------------------------
# Database — Cloud SQL via Unix socket + IAM passwordless auth
# DB_HOST = /cloudsql/<connection-name>  (directory; psycopg2 finds the socket)
# DB_USER = SA email without .gserviceaccount.com suffix
# Password  = short-lived IAM access token injected at connection time
# ---------------------------------------------------------------------------
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
from django.db.backends.postgresql.base import DatabaseWrapper as _PgWrapper

def _iam_token():
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/sqlservice.login"]
    )
    creds.refresh(GoogleAuthRequest())
    return creds.token

_orig_get_connection_params = _PgWrapper.get_connection_params

def _patched_get_connection_params(self):
    params = _orig_get_connection_params(self)
    params["password"] = _iam_token()
    return params

_PgWrapper.get_connection_params = _patched_get_connection_params

# ---------------------------------------------------------------------------
# Database config — Cloud SQL PostgreSQL
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "ssa_alumni_db"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": "",          # overridden at connect time by IAM token
        "HOST": os.environ.get("DB_HOST", ""),   # /cloudsql/<connection-name>
        "PORT": "",              # empty = use Unix socket (psycopg2 default)
        "CONN_MAX_AGE": 0,       # disable persistent connections (IAM tokens expire)
    }
}
