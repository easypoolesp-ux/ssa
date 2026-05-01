# =============================================================================
# Django — Production Settings
# Responsibility: Cloud Run / Cloud SQL overrides ONLY.
#                 Passwordless IAM auth, HTTPS enforcement.
# =============================================================================

from .base import *  # noqa: F401, F403
import os
from google.cloud.sql.connector import Connector, IPTypes

DEBUG = False

CLOUD_RUN_URL = os.environ.get("CLOUD_RUN_URL", "ssa-alumni-dev-m5bdpqwnfq-el.a.run.app")
ALLOWED_HOSTS = ["*"]  # Trust Cloud Run routing for now to avoid DisallowedHost error

CSRF_TRUSTED_ORIGINS = [f"https://{CLOUD_RUN_URL}"]

SECURE_SSL_REDIRECT     = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Cloud SQL — Passwordless IAM authentication via Unix socket
# ---------------------------------------------------------------------------
_connector = Connector()


def _get_cloud_sql_conn():
    """Return a psycopg connection via Cloud SQL IAM auth (no password)."""
    instance = os.environ["DB_HOST"].replace("/cloudsql/", "")
    return _connector.connect(
        instance,
        "psycopg2",
        user=os.environ["DB_USER"],
        db=os.environ["DB_NAME"],
        enable_iam_auth=True,
        ip_type=IPTypes.PRIVATE,
    )


# Override the base SQLite DB with Cloud SQL PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "ssa_alumni_db"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": "",  # Passwordless — IAM handles auth
        "HOST": "",
        "PORT": "",
        "CONN_MAX_AGE": 600,
    }
}

# Monkeypatch Django's PostgreSQL backend to use the connector
from django.db.backends.postgresql.base import DatabaseWrapper  # noqa: E402


def _patched_get_new_connection(self, conn_params):  # noqa: ANN001, ANN202
    return _get_cloud_sql_conn()


DatabaseWrapper.get_new_connection = _patched_get_new_connection
