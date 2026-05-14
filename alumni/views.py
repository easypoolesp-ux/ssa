"""
alumni/views.py
Responsibility: HTTP request/response handling ONLY.
                No business logic — models and serializers own that.
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import AlumniProfile, Event, RSVP
from .serializers import (
    AlumniProfileSerializer,
    EventListSerializer,
    EventDetailSerializer,
    RSVPSerializer,
)


# =============================================================================
# Permissions
# =============================================================================

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow profile owners to edit their own profile; everyone else read-only."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not hasattr(request.user, "uid"):
            return False
        return obj.firebase_uid == request.user.uid


# =============================================================================
# Alumni Profile ViewSet
# =============================================================================

class AlumniProfileViewSet(viewsets.ModelViewSet):
    """CRUD for alumni profiles. Owners can edit their own; admins can edit all."""

    queryset         = AlumniProfile.objects.all()
    serializer_class = AlumniProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    filter_backends   = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields  = ["batch", "is_verified", "is_active", "firebase_uid"]
    search_fields     = ["first_name", "last_name", "batch"]
    ordering_fields   = ["batch", "first_name", "last_name"]

    def perform_create(self, serializer):
        firebase_uid = getattr(self.request.user, "uid", None)
        if not firebase_uid:
            raise PermissionDenied("Authentication required to create a profile.")
        if AlumniProfile.objects.filter(firebase_uid=firebase_uid).exists():
            raise ValidationError({"detail": "A profile for this user already exists."})
        serializer.save(firebase_uid=firebase_uid)


from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

# =============================================================================
# Events
# =============================================================================

class EventListView(APIView):
    """
    GET /api/v1/events/
    Returns all published events ordered by date.
    Query params:
      upcoming=true  → only events from today onwards (default behaviour)
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        responses=EventListSerializer(many=True),
        parameters=[
            OpenApiParameter("upcoming", OpenApiTypes.BOOL, description="Filter for upcoming events only", default=True)
        ]
    )
    def get(self, request):
        from django.utils import timezone
        qs = Event.objects.filter(is_published=True)

        upcoming = request.query_params.get("upcoming", "true").lower()
        if upcoming == "true":
            qs = qs.filter(event_date__date__gte=timezone.localdate())

        serializer = EventListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class EventDetailView(APIView):
    """
    GET /api/v1/events/<pk>/
    Returns full event detail + the requesting alumni's RSVP status.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(responses=EventDetailSerializer)
    def get(self, request, pk):
        try:
            event = Event.objects.get(pk=pk, is_published=True)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = EventDetailSerializer(event, context={"request": request})
        return Response(serializer.data)


class RSVPView(APIView):
    """
    POST /api/v1/events/<pk>/rsvp/   → create or update RSVP
    DELETE /api/v1/events/<pk>/rsvp/ → remove RSVP

    The alumni record is resolved from the Firebase UID in the token.
    Alumni cannot RSVP as someone else.
    """

    permission_classes = [permissions.IsAuthenticated]

    def _get_alumni(self, request):
        uid = getattr(request.user, "uid", None)
        if not uid:
            raise PermissionDenied("Authentication required.")
        try:
            return AlumniProfile.objects.get(firebase_uid=uid)
        except AlumniProfile.DoesNotExist:
            raise PermissionDenied("You must have an alumni profile to RSVP.")

    def _get_event(self, pk):
        try:
            return Event.objects.get(pk=pk, is_published=True)
        except Event.DoesNotExist:
            raise ValidationError({"detail": "Event not found or not published."})

    @extend_schema(
        request=RSVPSerializer,
        responses={201: RSVPSerializer, 200: RSVPSerializer, 409: OpenApiTypes.OBJECT}
    )
    def post(self, request, pk):
        event  = self._get_event(pk)
        alumni = self._get_alumni(request)

        # Capacity check — only block on ATTENDING
        requested_status = request.data.get("status", RSVP.Status.ATTENDING)
        if requested_status == RSVP.Status.ATTENDING and event.is_full:
            return Response(
                {"detail": "Sorry, this event is at full capacity."},
                status=status.HTTP_409_CONFLICT,
            )

        rsvp, created = RSVP.objects.update_or_create(
            event=event,
            alumni=alumni,
            defaults={
                "status": requested_status,
                "notes":  request.data.get("notes", ""),
            },
        )
        serializer = RSVPSerializer(rsvp)
        http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=http_status)

    @extend_schema(responses={204: None, 404: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        event  = self._get_event(pk)
        alumni = self._get_alumni(request)
        deleted, _ = RSVP.objects.filter(event=event, alumni=alumni).delete()
        if not deleted:
            return Response({"detail": "No RSVP found to delete."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
