"""
alumni/admin.py
Responsibility: Django Admin configuration for all models.
                Admins manage events and RSVPs here; alumni use the mobile app.
"""

import io
import openpyxl

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

from .models import AlumniProfile, Event, RSVP


# =============================================================================
# AlumniProfile Admin
# =============================================================================

@admin.register(AlumniProfile)
class AlumniProfileAdmin(admin.ModelAdmin):
    """Manage alumni accounts, activation, and verification."""

    list_display   = ("full_name", "batch", "email", "is_verified", "is_active")
    list_filter    = ("batch", "is_verified", "is_active")
    search_fields  = ("first_name", "last_name", "email")
    list_editable  = ("is_verified", "is_active")
    readonly_fields = ("firebase_uid", "created_at", "updated_at")


# =============================================================================
# Event Admin
# =============================================================================

def _export_event_rsvps_excel(modeladmin, request, queryset):
    """
    Admin action: export the full RSVP list for selected event(s) as .xlsx.
    Columns: Name | Email | Phone | Batch | Grad Year | RSVP Status | Payment Status | Notes
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RSVP Attendees"

    # Header row
    headers = [
        "Event", "Name", "Email", "Phone",
        "Batch",
        "RSVP Status", "Payment Status", "Notes", "RSVPd At",
    ]
    ws.append(headers)

    # Bold the header
    from openpyxl.styles import Font
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for event in queryset:
        for rsvp in event.rsvps.select_related("alumni").order_by("rsvp_at"):
            ws.append([
                event.title,
                rsvp.alumni.full_name,
                rsvp.alumni.email,
                rsvp.alumni.phone,
                rsvp.alumni.batch,
                rsvp.get_status_display(),
                rsvp.get_payment_status_display(),
                rsvp.notes,
                rsvp.rsvp_at.strftime("%d %b %Y %H:%M") if rsvp.rsvp_at else "",
            ])

    # Auto-size columns for readability
    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = max(max_len + 4, 12)

    # Stream as download
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="event_rsvps.xlsx"'
    return response


_export_event_rsvps_excel.short_description = "⬇ Export RSVP list as Excel (.xlsx)"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Create and manage alumni events. Upload banners/videos; track RSVPs."""

    list_display   = (
        "title", "event_type", "event_date", "is_published",
        "fee_display", "rsvp_count_display", "capacity_display",
    )
    list_filter    = ("event_type", "is_published", "is_online")
    search_fields  = ("title", "location")
    readonly_fields = (
        "created_by", "created_at", "updated_at",
        "rsvp_count_display", "banner_preview", "video_preview",
    )
    actions = [_export_event_rsvps_excel]

    fieldsets = (
        ("Event Info", {
            "fields": ("title", "description", "event_type", "is_published"),
        }),
        ("Date & Location", {
            "fields": ("event_date", "end_date", "location", "is_online", "online_link"),
        }),
        ("Capacity & Fees", {
            "fields": ("max_attendees", "fee", "fee_currency", "rsvp_count_display"),
        }),
        ("Media (stored in GCS)", {
            "description": (
                "Banner image: JPG / WebP / GIF (GIF animates in the app). "
                "Video: MP4 / WebM looping header — optional, max ~50 MB. "
                "Files are stored in: gs://ssa-alumni-media/events/"
            ),
            "fields": ("banner", "banner_preview", "banner_video", "video_preview"),
        }),
        ("Audit", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="Fee")
    def fee_display(self, obj):
        return "FREE" if obj.is_free else f"₹{obj.fee}"

    @admin.display(description="RSVPs")
    def rsvp_count_display(self, obj):
        if obj.pk:
            return obj.rsvp_count
        return "—"

    @admin.display(description="Capacity")
    def capacity_display(self, obj):
        if obj.max_attendees is None:
            return "Unlimited"
        return f"{obj.rsvp_count} / {obj.max_attendees}"

    @admin.display(description="Banner Preview")
    def banner_preview(self, obj):
        if obj.banner:
            return format_html(
                '<img src="{}" style="max-height:160px;border-radius:8px;" />', obj.banner.url
            )
        return "No banner uploaded"

    @admin.display(description="Video Preview")
    def video_preview(self, obj):
        if obj.banner_video:
            return format_html(
                '<video src="{}" controls style="max-height:160px;border-radius:8px;"></video>',
                obj.banner_video.url,
            )
        return "No video uploaded"


# =============================================================================
# RSVP Admin
# =============================================================================

@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    """Read-only view of RSVPs. Editing happens through EventAdmin export."""

    list_display   = ("alumni_name", "event", "status", "payment_status", "rsvp_at")
    list_filter    = ("status", "payment_status", "event")
    search_fields  = ("alumni__full_name", "alumni__email")
    readonly_fields = ("event", "alumni", "rsvp_at")

    @admin.display(description="Alumni")
    def alumni_name(self, obj):
        return obj.alumni.full_name
