"""Alumni app — REST API views."""

from rest_framework import viewsets, permissions
from .models import AlumniProfile
from .serializers import AlumniProfileSerializer


class AlumniProfileViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for alumni profiles."""

    queryset           = AlumniProfile.objects.all()
    serializer_class   = AlumniProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        year = self.request.query_params.get("year")
        if year:
            qs = qs.filter(graduation_year=year)
        return qs
