"""SSA Alumni — WSGI entry point for gunicorn."""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssa_alumni.settings.prod")

application = get_wsgi_application()
