# Final deployment attempt with all permissions applied
# =============================================================================
# Django — Production Settings
# Responsibility: Cloud Run / Cloud SQL production overrides
# =============================================================================

from .base import *  # noqa: F401, F403
import os
from google.cloud.sql.connector import Connector, IPTypes

DEBUG = False

# Restrict to Cloud Run service URL
CLOUD_RUN_URL = os.environ.get("CLOUD_RUN_URL", "ssa-alumni-dev-685527496529.asia-south1.run.app")  # noqa: F405
ALLOWED_HOSTS = [CLOUD_RUN_URL, "localhost"] if CLOUD_RUN_URL else ["*"]

# CSRF — trust Cloud Run service URL
CSRF_TRUSTED_ORIGINS = [f"https://{CLOUD_RUN_URL}"] if CLOUD_RUN_URL else []

SECURE_SSL_REDIRECT     = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Cloud SQL IAM Authentication ---
# Initialize Cloud SQL Connector
connector = Connector()

def getconn():
    conn = connector.connect(
        os.environ.get("DB_HOST").replace("/cloudsql/", ""), # Connection name
        "psycopg2",
        user=os.environ.get("DB_USER"),
        db=os.environ.get("DB_NAME"),
        enable_iam_auth=True,
        ip_type=IPTypes.PUBLIC
    )
    return conn

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "CONN_MAX_AGE": 600,
    }
}

# Inject the connector's getconn function into Django's connection logic
# For pg8000, we use a slightly different injection or just use the connector natively
# Actually, the connector documentation recommends using the 'creator' argument in DATABASES
DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"
DATABASES["default"]["OPTIONS"] = {
    "sslmode": "disable",
}
# We use the 'creator' parameter to pass the getconn function
# However, Django's postgres backend doesn't support 'creator' directly in settings.
# So we stick to the monkeypatch but update it for pg8000.
from django.db.backends.postgresql.base import DatabaseWrapper
DatabaseWrapper.get_new_connection = lambda self, conn_params: getconn()


