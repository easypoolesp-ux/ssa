"""
alumni/migrations/0005_extended_profile_fields.py

Safe migration strategy for the full_name → first_name + last_name split:
  1. Add first_name / last_name as nullable (no NOT-NULL constraint yet)
  2. RunPython: copy-split every existing row's full_name into the two new cols
  3. Make first_name non-nullable (existing rows are already populated)
  4. RemoveField full_name
  5. Add all other new fields (all blank/null safe → zero risk to existing rows)
"""

from django.db import migrations, models


def split_full_name_forward(apps, schema_editor):
    AlumniProfile = apps.get_model("alumni", "AlumniProfile")
    for profile in AlumniProfile.objects.all():
        full = (profile.full_name or "").strip()
        parts = full.split(" ", 1)          # split on first space only
        profile.first_name = parts[0] if parts else ""
        profile.last_name  = parts[1] if len(parts) > 1 else ""
        profile.save(update_fields=["first_name", "last_name"])


def merge_names_backward(apps, schema_editor):
    """Reverse: reconstruct full_name from first_name + last_name."""
    AlumniProfile = apps.get_model("alumni", "AlumniProfile")
    for profile in AlumniProfile.objects.all():
        profile.full_name = f"{profile.first_name} {profile.last_name}".strip()
        profile.save(update_fields=["full_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("alumni", "0004_event_rsvp"),
    ]

    operations = [
        # ── Step 1: add first_name + last_name as nullable so existing rows are safe ──
        migrations.AddField(
            model_name="alumniprofile",
            name="first_name",
            field=models.CharField(max_length=100, null=True, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="last_name",
            field=models.CharField(max_length=100, blank=True, default=""),
        ),

        # ── Step 2: copy existing full_name data ──────────────────────────────
        migrations.RunPython(split_full_name_forward, reverse_code=merge_names_backward),

        # ── Step 3: tighten first_name to NOT NULL now data is populated ──────
        migrations.AlterField(
            model_name="alumniprofile",
            name="first_name",
            field=models.CharField(max_length=100),
        ),

        # ── Step 4: remove the old full_name column ───────────────────────────
        migrations.RemoveField(
            model_name="alumniprofile",
            name="full_name",
        ),

        # ── Step 5: member_type ───────────────────────────────────────────────
        migrations.AddField(
            model_name="alumniprofile",
            name="member_type",
            field=models.CharField(
                choices=[("student", "Student"), ("teacher", "Teacher")],
                default="student",
                help_text="Whether this member is a student alumni or a teacher",
                max_length=10,
            ),
        ),

        # ── Step 6: personal extras ───────────────────────────────────────────
        migrations.AddField(
            model_name="alumniprofile",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="instagram_url",
            field=models.URLField(blank=True),
        ),

        # ── Step 7: relax graduation_year + batch (allow null/blank) ─────────
        migrations.AlterField(
            model_name="alumniprofile",
            name="graduation_year",
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name="alumniprofile",
            name="batch",
            field=models.CharField(max_length=50, blank=True),
        ),

        # ── Step 8: education — 10+2 ─────────────────────────────────────────
        migrations.AddField(
            model_name="alumniprofile",
            name="edu_10_plus_2_stream",
            field=models.CharField(
                blank=True,
                choices=[
                    ("science", "Science"),
                    ("commerce", "Commerce"),
                    ("arts", "Arts"),
                    ("other", "Other"),
                ],
                help_text="10+2 stream (Science / Commerce / Arts / Other)",
                max_length=10,
            ),
        ),

        # ── Step 9: education — graduation ───────────────────────────────────
        migrations.AddField(
            model_name="alumniprofile",
            name="edu_graduation_course",
            field=models.CharField(
                blank=True, max_length=150, help_text="e.g. B.Tech, BBA, B.Sc"
            ),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="edu_graduation_college",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="edu_graduation_university",
            field=models.CharField(blank=True, max_length=200),
        ),

        # ── Step 10: education — post-graduation ──────────────────────────────
        migrations.AddField(
            model_name="alumniprofile",
            name="edu_postgrad_degree",
            field=models.CharField(
                blank=True, max_length=150, help_text="e.g. MBA, M.Tech"
            ),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="edu_postgrad_college",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="edu_postgrad_university",
            field=models.CharField(blank=True, max_length=200),
        ),

        # ── Step 11: professional extras ─────────────────────────────────────
        migrations.AddField(
            model_name="alumniprofile",
            name="employment_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("employed", "Employed"),
                    ("business", "Business / Self-employed"),
                    ("not_working", "Student / Not Working"),
                ],
                help_text="Current employment status",
                max_length=15,
            ),
        ),
        migrations.AlterField(
            model_name="alumniprofile",
            name="current_company",
            field=models.CharField(
                blank=True, max_length=200, help_text="Company / business name"
            ),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="designation",
            field=models.CharField(
                blank=True, max_length=200, help_text="Job designation / title"
            ),
        ),
        migrations.AddField(
            model_name="alumniprofile",
            name="business_details",
            field=models.TextField(
                blank=True,
                help_text="Description of business / self-employment",
            ),
        ),
    ]
