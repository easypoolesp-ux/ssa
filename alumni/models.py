"""
alumni/models.py
Responsibility: Define all database schema for the alumni platform.
                Each model class has one job and one domain.
"""

from django.db import models
from django.contrib.auth import get_user_model

from .storage_backends import EventBannerStorage, EventVideoStorage

User = get_user_model()


# =============================================================================
# Alumni Profile
# =============================================================================

class AlumniProfile(models.Model):
    """Core alumni record for the school directory."""

    # Firebase Auth linking
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)

    # Personal
    full_name    = models.CharField(max_length=200)
    email        = models.EmailField(unique=True)
    phone        = models.CharField(max_length=20, blank=True)
    profile_pic  = models.URLField(blank=True)
    bio          = models.TextField(blank=True)

    # School details
    graduation_year = models.PositiveIntegerField()
    batch           = models.CharField(max_length=50)

    # Professional
    current_company  = models.CharField(max_length=200, blank=True)
    current_role     = models.CharField(max_length=200, blank=True)
    linkedin_url     = models.URLField(blank=True)
    current_city     = models.CharField(max_length=100, blank=True)

    # Access control
    is_verified = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=False)

    # Meta
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-graduation_year", "full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.graduation_year})"


# =============================================================================
# Events
# =============================================================================

class Event(models.Model):
    """
    A school alumni event.

    Banner media strategy:
      - banner       → static image (JPG / WebP / GIF).  GIF animates natively in Flutter.
      - banner_video → short looping video (MP4 / WebM ≤ 50 MB).
                       If set, the Flutter app plays it muted/looped as the header.
                       If not set, flutter shows the banner image with a parallax scroll.

    Both files are stored in Google Cloud Storage:
      gs://ssa-alumni-media/events/banners/<filename>
      gs://ssa-alumni-media/events/videos/<filename>
    """

    class EventType(models.TextChoices):
        REUNION   = "reunion",   "Reunion"
        WEBINAR   = "webinar",   "Webinar"
        SPORTS    = "sports",    "Sports"
        CULTURAL  = "cultural",  "Cultural"
        OTHER     = "other",     "Other"

    # Core info
    title       = models.CharField(max_length=300)
    description = models.TextField()
    event_type  = models.CharField(
        max_length=20, choices=EventType.choices, default=EventType.OTHER
    )

    # Scheduling
    event_date = models.DateTimeField(help_text="Event start date and time (IST)")
    end_date   = models.DateTimeField(
        null=True, blank=True,
        help_text="Optional end date/time for multi-day events"
    )

    # Location
    location     = models.CharField(max_length=300, blank=True)
    is_online    = models.BooleanField(default=False)
    online_link  = models.URLField(blank=True, help_text="Google Meet / Zoom link")

    # Capacity
    max_attendees = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Leave blank for unlimited capacity"
    )

    # Payment (payment processing logic deferred — structure is ready)
    fee          = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00,
        help_text="0.00 means free event"
    )
    fee_currency = models.CharField(max_length=5, default="INR")

    # Media — stored safely in GCS via named storage backends
    banner = models.ImageField(
        storage=EventBannerStorage(),
        null=True, blank=True,
        help_text="Event poster image (JPG / WebP / GIF). GIF animates in app."
    )
    banner_video = models.FileField(
        storage=EventVideoStorage(),
        null=True, blank=True,
        help_text="Optional looping video header (MP4 / WebM, max ~50 MB)."
    )

    # Visibility
    is_published = models.BooleanField(
        default=False,
        help_text="Only published events are visible in the app"
    )

    # Audit
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_events"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_date"]

    def __str__(self):
        return f"{self.title} ({self.event_date.strftime('%d %b %Y')})"

    @property
    def is_free(self) -> bool:
        return self.fee == 0

    @property
    def rsvp_count(self) -> int:
        """Number of alumni who said they are attending."""
        return self.rsvps.filter(status=RSVP.Status.ATTENDING).count()

    @property
    def is_full(self) -> bool:
        if self.max_attendees is None:
            return False
        return self.rsvp_count >= self.max_attendees

    @property
    def banner_url(self) -> str | None:
        """Absolute GCS URL for the banner image, or None."""
        return self.banner.url if self.banner else None

    @property
    def banner_video_url(self) -> str | None:
        """Absolute GCS URL for the banner video, or None."""
        return self.banner_video.url if self.banner_video else None


# =============================================================================
# RSVP
# =============================================================================

class RSVP(models.Model):
    """
    An alumni's attendance intention for a specific event.
    One row per (event, alumni) pair — enforced by unique_together.

    payment_status and payment_ref are wired up but unused until
    Razorpay integration is implemented.
    """

    class Status(models.TextChoices):
        ATTENDING     = "attending",     "Attending"
        NOT_ATTENDING = "not_attending", "Not Attending"
        MAYBE         = "maybe",         "Maybe"

    class PaymentStatus(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not Required"
        PENDING      = "pending",      "Payment Pending"
        PAID         = "paid",         "Paid"
        REFUNDED     = "refunded",     "Refunded"

    event  = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    alumni = models.ForeignKey(AlumniProfile, on_delete=models.CASCADE, related_name="rsvps")

    status          = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ATTENDING
    )
    payment_status  = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.NOT_REQUIRED
    )
    payment_ref     = models.CharField(
        max_length=200, blank=True,
        help_text="Razorpay order/payment ID — populated after payment integration"
    )
    notes           = models.TextField(blank=True, help_text="e.g. 'Bringing +1'")
    rsvp_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "alumni")
        ordering = ["rsvp_at"]

    def __str__(self):
        return f"{self.alumni.full_name} → {self.event.title} [{self.status}]"
