"""Alumni app — REST API views."""

from rest_framework import viewsets, permissions, filters
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from .models import AlumniProfile
from .serializers import AlumniProfileSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a profile to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner.
        if not hasattr(request.user, 'uid'):
            return False
        return obj.firebase_uid == request.user.uid


class AlumniProfileViewSet(viewsets.ModelViewSet):
    """
    Standard out-of-the-box Django ModelViewSet for Alumni Profiles.
    Handles GET (list/detail), POST (create), PUT/PATCH (update), DELETE.
    """
    queryset = AlumniProfile.objects.all()
    serializer_class = AlumniProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['graduation_year', 'batch', 'is_verified', 'is_active', 'firebase_uid']
    search_fields = ['full_name', 'current_company', 'current_role']
    ordering_fields = ['graduation_year', 'full_name']

    def perform_create(self, serializer):
        # Check if user already has a profile
        firebase_uid = getattr(self.request.user, 'uid', None)
        if not firebase_uid:
            raise PermissionDenied("Authentication required to create a profile.")
            
        if AlumniProfile.objects.filter(firebase_uid=firebase_uid).exists():
            raise ValidationError({"detail": "A profile for this user already exists."})
            
        serializer.save(firebase_uid=firebase_uid)
