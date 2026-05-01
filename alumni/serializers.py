"""Alumni app — DRF serializers."""

from rest_framework import serializers
from .models import AlumniProfile


class AlumniProfileSerializer(serializers.ModelSerializer):
    """Standard ModelSerializer for AlumniProfile."""
    
    class Meta:
        model = AlumniProfile
        fields = [
            "id",
            "firebase_uid",
            "full_name",
            "email",
            "phone",
            "profile_pic",
            "bio",
            "graduation_year",
            "batch",
            "current_company",
            "current_role",
            "linkedin_url",
            "current_city",
            "is_verified",
            "is_active",
            "created_at",
            "updated_at",
        ]
        # Only backend/admin can set these — never exposed as writable to users
        read_only_fields = ["id", "firebase_uid", "is_verified", "is_active", "created_at", "updated_at"]

    def validate_graduation_year(self, value):
        """Basic validation for year."""
        import datetime
        current_year = datetime.date.today().year
        if value < 1900 or value > current_year + 5:
            raise serializers.ValidationError("Please provide a valid graduation year.")
        return value
