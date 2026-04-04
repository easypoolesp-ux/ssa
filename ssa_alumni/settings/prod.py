# Triggering new deployment with updated IAM roles
# =============================================================================
# Django — Production Settings
# Responsibility: Cloud Run / Cloud SQL production overrides
# =============================================================================

from .base import *  # noqa: F401, F403
import os
from google.cloud.sql.connector import Connector, IPTypes

DEBUG = False

# Restrict to Cloud Run service URL
CLOUD_RUN_URL = os.environ.get("CLOUD_RUN_URL", "ssa-alumni-dev-m5bdpqwnfq-el.a.run.app")  # noqa: F405
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
        ip_type=IPTypes.PUBLIC # Cloud Run can reach public IP via IAM auth securely
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
from django.db.backends.postgresql.base import DatabaseWrapper
DatabaseWrapper.get_new_connection = lambda self, conn_params: getconn()

