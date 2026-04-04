"""Alumni app — Django admin registration."""

from django.contrib import admin
from .models import AlumniProfile


@admin.register(AlumniProfile)
class AlumniProfileAdmin(admin.ModelAdmin):
    list_display   = ("full_name", "graduation_year", "batch", "email", "is_verified")
    list_filter    = ("graduation_year", "batch", "is_verified")
    search_fields  = ("full_name", "email", "current_company")
