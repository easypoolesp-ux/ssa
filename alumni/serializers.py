"""
alumni/serializers.py
Responsibility: Transform model instances ↔ validated JSON.
                Each serializer class has one job (one model, one API shape).
"""

import datetime
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import AlumniProfile, Event, RSVP


# =============================================================================
# AlumniProfile
# =============================================================================

class AlumniProfileSerializer(serializers.ModelSerializer):
    """Full profile serializer — used by directory and profile screens."""

    # Backward-compat computed field (not a DB column)
    full_name = serializers.SerializerMethodField(read_only=True)

    def get_full_name(self, obj):
        return obj.full_name

    class Meta:
        model  = AlumniProfile
        fields = [
            # identity
            "id", "firebase_uid", "member_type",
            # personal
            "first_name", "last_name", "full_name",
            "date_of_birth", "email", "phone",
            "profile_pic", "bio", "instagram_url", "linkedin_url",
            # school
            "graduation_year", "batch",
            # education — 10+2
            "edu_10_plus_2_stream",
            # education — graduation
            "edu_graduation_course", "edu_graduation_college", "edu_graduation_university",
            # education — post-graduation
            "edu_postgrad_degree", "edu_postgrad_college", "edu_postgrad_university",
            # professional
            "employment_type", "current_company", "current_role",
            "designation", "business_details", "current_city",
            # access
            "is_verified", "is_active",
            # audit
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "firebase_uid", "is_verified", "is_active",
            "created_at", "updated_at",
        ]

    def validate_graduation_year(self, value):
        if value is None:
            return value
        import datetime
        current_year = datetime.date.today().year
        if value < 1900 or value > current_year + 5:
            raise serializers.ValidationError("Please provide a valid graduation year.")
        return value


# =============================================================================
# Event — two shapes: lightweight list card vs. full detail
# =============================================================================

class EventListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the events list screen.
    Returns only what a card widget needs — keeps payload small.
    """

    is_free       = serializers.BooleanField(read_only=True)
    rsvp_count    = serializers.IntegerField(read_only=True)
    is_full       = serializers.BooleanField(read_only=True)
    banner_url    = serializers.CharField(read_only=True)
    banner_video_url = serializers.CharField(read_only=True)

    class Meta:
        model  = Event
        fields = [
            "id", "title", "event_type", "event_date", "end_date",
            "location", "is_online", "fee", "fee_currency",
            "banner_url", "banner_video_url",
            "is_free", "rsvp_count", "is_full", "is_published",
        ]


# =============================================================================
# RSVP
# =============================================================================

class RSVPSerializer(serializers.ModelSerializer):
    """
    Used for both reading an RSVP (in EventDetailSerializer)
    and writing one (POST/PUT from the app).
    """

    alumni_name = serializers.CharField(source="alumni.full_name", read_only=True)

    class Meta:
        model  = RSVP
        fields = [
            "id", "event", "alumni", "alumni_name",
            "status", "payment_status", "payment_ref",
            "notes", "rsvp_at",
        ]
        read_only_fields = [
            "id", "alumni", "alumni_name",
            "payment_status", "payment_ref", "rsvp_at",
        ]


class EventDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for the event detail screen.
    Includes description, online_link, and the requesting alumni's RSVP.
    `my_rsvp` is injected by the view — null if not RSVPd yet.
    """

    is_free          = serializers.BooleanField(read_only=True)
    rsvp_count       = serializers.IntegerField(read_only=True)
    is_full          = serializers.BooleanField(read_only=True)
    banner_url       = serializers.CharField(read_only=True)
    banner_video_url = serializers.CharField(read_only=True)
    my_rsvp          = serializers.SerializerMethodField()

    class Meta:
        model  = Event
        fields = [
            "id", "title", "description", "event_type",
            "event_date", "end_date",
            "location", "is_online", "online_link",
            "max_attendees", "fee", "fee_currency",
            "banner_url", "banner_video_url",
            "is_free", "rsvp_count", "is_full", "is_published",
            "my_rsvp",
        ]

    @extend_schema_field(RSVPSerializer)
    def get_my_rsvp(self, obj):
        """Return the requesting user's RSVP for this event, or None."""
        request = self.context.get("request")
        if not request or not hasattr(request.user, "uid"):
            return None
        try:
            alumni  = AlumniProfile.objects.get(firebase_uid=request.user.uid)
            rsvp    = RSVP.objects.get(event=obj, alumni=alumni)
            return RSVPSerializer(rsvp).data
        except (AlumniProfile.DoesNotExist, RSVP.DoesNotExist):
            return None


