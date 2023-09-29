import logging

from django.conf import settings
from library_sample_shared.views import LibrarySampleBaseViewSet
from rest_framework import viewsets
from django.db.models.functions import Lower

from .models import NucleicAcidType
from .serializers import NucleicAcidTypeSerializer, SampleSerializer

logger = logging.getLogger("db")


class NucleicAcidTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of nucleic acid types."""

    serializer_class = NucleicAcidTypeSerializer

    def get_queryset(self):
        return NucleicAcidType.objects.filter(status=settings.NON_OBSOLETE).order_by(
            "type", Lower("name") # Lower to make filtering case insensitive
        )


class SampleViewSet(LibrarySampleBaseViewSet):
    serializer_class = SampleSerializer
