# =============================================================================
# Django — Base Settings
# Responsibility: Shared settings across ALL environments.
#                 One file = one responsibility (SOLID: SRP).
# =============================================================================

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "build-time-placeholder-secret-key")
DEBUG = False
ALLOWED_HOSTS = ["*"]  # Locked down per-environment in env-specific settings

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "storages",           # django-storages: GCS backend for media uploads
    # Project apps
    "alumni",
]

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ssa_alumni.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ssa_alumni.wsgi.application"
ASGI_APPLICATION  = "ssa_alumni.asgi.application"

# ---------------------------------------------------------------------------
# Database — overridden per environment
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "ssa_alumni.authentication.FirebaseAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ---------------------------------------------------------------------------
# drf-spectacular — OpenAPI schema generation
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "SSA Alumni API",
    "DESCRIPTION": (
        "REST API for the SSA Alumni school directory. "
        "Authentication via Firebase JWT (Bearer token)."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "CONTACT": {"name": "SSA Team"},
    "LICENSE": {"name": "Private"},
    "SERVERS": [
        {"url": "https://ssa-alumni-dev-m5bdpqwnfq-el.a.run.app", "description": "Dev"},
    ],
    "COMPONENT_SPLIT_REQUEST": True,  # Separate read/write schemas
}

# ---------------------------------------------------------------------------
# Firebase
# ---------------------------------------------------------------------------
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "ssa-alumni")

# ---------------------------------------------------------------------------
# CORS — allow Flutter web + local dev
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "https://ssa-alumni-dev-m5bdpqwnfq-el.a.run.app",
    "https://ssa-alumni.web.app",
]
CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL", "False") == "True"
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Asia/Kolkata"
USE_I18N      = True
USE_TZ        = True

# ---------------------------------------------------------------------------
# Static files — WhiteNoise serves from Cloud Run
# ---------------------------------------------------------------------------
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------------------
# Media / File Uploads — Google Cloud Storage
# ---------------------------------------------------------------------------
# Bucket layout:
#   ssa-alumni-media/
#   ├── events/banners/    ← poster images (JPG, WebP, GIF)
#   └── events/videos/     ← highlight videos (MP4, WebM)
#
# Auth: Cloud Run uses the attached service-account's ADC (no key file needed).
# In local dev, set GOOGLE_APPLICATION_CREDENTIALS to a service-account JSON.
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "ssa-alumni-media")

STORAGES = {
    # Model FileField / ImageField uploads go through the per-field
    # EventBannerStorage / EventVideoStorage backends in storage_backends.py
    # which always pass bucket_name explicitly.
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Public URL base for GCS objects (used by storage backends to build absolute URLs)
GS_BUCKET_NAME = GCS_BUCKET_NAME  # django-storages reads this key
MEDIA_URL      = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Logging — stdout/stderr captured by Cloud Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
}
