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

import google.auth
from google.auth.transport.requests import Request
from django.db.backends.postgresql.base import DatabaseWrapper as PostgresDatabaseWrapper

def _get_iam_token():
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/sqlservice.login"])
    credentials.refresh(Request())
    return credentials.token

_orig_get_connection_params = PostgresDatabaseWrapper.get_connection_params

def _patched_get_connection_params(self):
    params = _orig_get_connection_params(self)
    params["password"] = _get_iam_token()
    return params

PostgresDatabaseWrapper.get_connection_params = _patched_get_connection_params

# Override the base SQLite DB with Cloud SQL PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "ssa_alumni_db"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": "",  # Passwordless — IAM handles auth
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": "5432",
        "CONN_MAX_AGE": 600,
    }
}

# Monkeypatch Django's PostgreSQL backend to use the connector
from django.db.backends.postgresql.base import DatabaseWrapper  # noqa: E402


def _patched_get_new_connection(self, conn_params):  # noqa: ANN001, ANN202
    return _get_cloud_sql_conn()


DatabaseWrapper.get_new_connection = _patched_get_new_connection
