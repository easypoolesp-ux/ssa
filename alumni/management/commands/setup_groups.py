"""
alumni/management/commands/setup_groups.py
Responsibility: Idempotent command to create staff permission groups.
                Run once on first deploy: python manage.py setup_groups

Groups created:
  - Event Manager    → can add/change/view Events, view + export RSVPs
  - Member Verifier  → can change AlumniProfile is_verified/is_active only
  - Read Only Staff  → can view all models, change nothing
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from alumni.models import AlumniProfile, Event, RSVP


class Command(BaseCommand):
    help = "Create role-based staff permission groups for the alumni platform."

    def handle(self, *args, **kwargs):
        self._setup_event_manager()
        self._setup_member_verifier()
        self._setup_read_only_staff()
        self.stdout.write(self.style.SUCCESS("[OK] All staff groups created/updated successfully."))

    # ── Group 1: Event Manager ──────────────────────────────────────────────
    def _setup_event_manager(self):
        group, _ = Group.objects.get_or_create(name="Event Manager")
        event_ct = ContentType.objects.get_for_model(Event)
        rsvp_ct  = ContentType.objects.get_for_model(RSVP)

        perms = Permission.objects.filter(
            content_type__in=[event_ct, rsvp_ct],
            codename__in=[
                "add_event", "change_event", "view_event",
                "view_rsvp",
            ],
        )
        group.permissions.set(perms)
        self.stdout.write(f"  -> Event Manager: {perms.count()} permissions set")

    # ── Group 2: Member Verifier ────────────────────────────────────────────
    def _setup_member_verifier(self):
        group, _ = Group.objects.get_or_create(name="Member Verifier")
        profile_ct = ContentType.objects.get_for_model(AlumniProfile)

        # Django's built-in change permission covers is_verified and is_active fields.
        # The admin fieldsets limit what is editable in the UI.
        perms = Permission.objects.filter(
            content_type=profile_ct,
            codename__in=["view_alumniprofile", "change_alumniprofile"],
        )
        group.permissions.set(perms)
        self.stdout.write(f"  -> Member Verifier: {perms.count()} permissions set")

    # ── Group 3: Read Only Staff ────────────────────────────────────────────
    def _setup_read_only_staff(self):
        group, _ = Group.objects.get_or_create(name="Read Only Staff")
        for model in [AlumniProfile, Event, RSVP]:
            ct = ContentType.objects.get_for_model(model)
            model_name = model.__name__.lower()
            perm = Permission.objects.filter(
                content_type=ct, codename=f"view_{model_name}"
            ).first()
            if perm:
                group.permissions.add(perm)

        self.stdout.write("  -> Read Only Staff: view-only permissions set")
