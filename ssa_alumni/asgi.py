"""SSA Alumni — ASGI entry point for async support."""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssa_alumni.settings.prod")

application = get_asgi_application()
