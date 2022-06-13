import logging
import itertools

from django.apps import apps
from django.db.models import Prefetch

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from common.mixins import LibrarySampleMultiEditMixin
from .serializers import RequestSerializer, LibrarySerializer, SampleSerializer

Request = apps.get_model('request', 'Request')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')

logger = logging.getLogger('db')


class IncomingLibrariesViewSet(LibrarySampleMultiEditMixin, viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    library_model = Library
    sample_model = Sample
    library_serializer = LibrarySerializer
    sample_serializer = SampleSerializer

    def list(self, request):
        """ Get the list of all incoming libraries and samples. """
        libraries_qs = Library.objects.select_related(
            'library_protocol',
            'concentration_method',
        ).filter(status=1)
        samples_qs = Sample.objects.select_related(
            'library_protocol',
            'concentration_method',
            'nucleic_acid_type',
        ).filter(status=1)

        queryset = Request.objects.prefetch_related(
            Prefetch('libraries', queryset=libraries_qs),
            Prefetch('samples', queryset=samples_qs),
        ).order_by('-create_time')

        serializer = RequestSerializer(queryset, many=True)
        data = list(itertools.chain(*serializer.data))

        data = sorted(data, key=lambda x: x['barcode'][3:])
        return Response(data)
