"""Alumni app — Django models."""

from django.db import models


class AlumniProfile(models.Model):
    """Core alumni record for the school directory."""

    # Firebase Auth linking
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)

    # Personal
    full_name    = models.CharField(max_length=200)
    email        = models.EmailField(unique=True)
    phone        = models.CharField(max_length=20, blank=True)
    profile_pic  = models.URLField(blank=True)

    # School details
    graduation_year = models.PositiveIntegerField()
    batch           = models.CharField(max_length=50)

    # Professional
    current_company  = models.CharField(max_length=200, blank=True)
    current_role     = models.CharField(max_length=200, blank=True)
    linkedin_url     = models.URLField(blank=True)

    # Meta
    is_verified = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-graduation_year", "full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.graduation_year})"
