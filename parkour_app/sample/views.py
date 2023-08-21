import logging

from django.conf import settings
from library_sample_shared.views import LibrarySampleBaseViewSet
from rest_framework import viewsets

from .models import NucleicAcidType
from .serializers import NucleicAcidTypeSerializer, SampleSerializer

logger = logging.getLogger("db")


class NucleicAcidTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of nucleic acid types."""

    serializer_class = NucleicAcidTypeSerializer

    def get_queryset(self):
        return NucleicAcidType.objects.filter(archived=False).order_by(
            "type", "name"
        )


class SampleViewSet(LibrarySampleBaseViewSet):
    serializer_class = SampleSerializer
