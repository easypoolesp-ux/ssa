"""
alumni/serializers.py
Responsibility: Transform model instances ↔ validated JSON.
                Each serializer class has one job (one model, one API shape).
"""

import datetime
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import AlumniProfile, Event, RSVP, WorkExperience, Education


# =============================================================================
# Stackable Profile Elements
# =============================================================================

class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = [
            "id", "company_name", "designation", "start_date",
            "end_date", "is_current", "location", "description",
            "company_website", "company_linkedin", "company_instagram",
        ]
        read_only_fields = ["id"]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            "id", "institution_name", "degree", "field_of_study",
            "start_year", "end_year", "description",
        ]
        read_only_fields = ["id"]


# =============================================================================
# AlumniProfile
# =============================================================================

class AlumniProfileSerializer(serializers.ModelSerializer):
    """Full profile serializer — used by directory and profile screens."""

    # Backward-compat computed field (not a DB column)
    full_name = serializers.SerializerMethodField(read_only=True)
    
    # Nested relations
    work_experiences = WorkExperienceSerializer(many=True, required=False)
    educations = EducationSerializer(many=True, required=False)

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
            "profile_pic", "bio", "instagram_url", "linkedin_url", "current_city",
            # school
            "batch",
            # nested
            "work_experiences", "educations",
            # access
            "is_verified", "is_active",
            # audit
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "firebase_uid", "is_verified", "is_active",
            "created_at", "updated_at",
        ]

    def _handle_nested(self, instance, validated_data):
        """Helper to create/update nested relations during save."""
        if "work_experiences" in validated_data:
            work_data = validated_data.pop("work_experiences")
            instance.work_experiences.all().delete()
            for w in work_data:
                WorkExperience.objects.create(profile=instance, **w)
                
        if "educations" in validated_data:
            edu_data = validated_data.pop("educations")
            instance.educations.all().delete()
            for e in edu_data:
                Education.objects.create(profile=instance, **e)

    def create(self, validated_data):
        work_data = validated_data.pop("work_experiences", [])
        edu_data = validated_data.pop("educations", [])
        instance = super().create(validated_data)
        for w in work_data:
            WorkExperience.objects.create(profile=instance, **w)
        for e in edu_data:
            Education.objects.create(profile=instance, **e)
        return instance

    def update(self, instance, validated_data):
        self._handle_nested(instance, validated_data)
        return super().update(instance, validated_data)



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


