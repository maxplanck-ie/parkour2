import json
import logging
import itertools

from django.apps import apps
from django.db.models import Prefetch, Q

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from common.mixins import LibrarySampleMultiEditMixin

from .models import Pool, PoolSize
from .index_generator import IndexGenerator
from .serializers import (
    PoolSizeSerializer,
    IndexGeneratorSerializer,
    IndexGeneratorLibrarySerializer,
    IndexGeneratorSampleSerializer,
)
from library_sample_shared.serializers import IndexTypeSerializer
from django.conf import settings

Request = apps.get_model('request', 'Request')
IndexI7 = apps.get_model('library_sample_shared', 'IndexI7')
IndexI5 = apps.get_model('library_sample_shared', 'IndexI5')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')
IndexType = apps.get_model('library_sample_shared','IndexType')

logger = logging.getLogger('db')


class MoveOtherMixin:
    """ Move the `Other` option to the end of the returning list. """

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(self._get_data(serializer))

        serializer = self.get_serializer(queryset, many=True)
        return Response(self._get_data(serializer))

    def _get_data(self, serializer):
        data = serializer.data

        # Move the 'Other' option to the end of the list
        other_options = sorted([
            x for x in data if 'Other' in x['name']
        ], key=lambda x: x['name'])

        for other in other_options:
            index = data.index(other)
            data.append(data.pop(index))

        return data

class GeneratorIndexTypeViewSet(MoveOtherMixin, viewsets.ReadOnlyModelViewSet):
    """ Get the list of index types. """
    queryset = IndexType.objects.order_by('name')
    serializer_class = IndexTypeSerializer



class PoolSizeViewSet(viewsets.ReadOnlyModelViewSet):
    """ Get the list of pool sizes. """
    queryset = PoolSize.objects.all().filter(obsolete=settings.NON_OBSOLETE)
    serializer_class = PoolSizeSerializer


class IndexGeneratorViewSet(viewsets.ViewSet, LibrarySampleMultiEditMixin):
    permission_classes = [IsAdminUser]
    library_model = Library
    sample_model = Sample
    library_serializer = IndexGeneratorLibrarySerializer
    sample_serializer = IndexGeneratorSampleSerializer

    def list(self, request):
        """ Get the list of libraries and samples ready for pooling. """

        libraries_qs = Library.objects.select_related(
            'library_protocol',
            'read_length',
            'index_type',
        ).prefetch_related(
            'index_type__indices_i7',
            'index_type__indices_i5',
        ).filter(
            Q(is_pooled=False) &
            Q(index_i7__isnull=False) &
            (Q(status=2) | Q(status=-2))
        ).only(
            'id',
            'name',
            'barcode',
            'index_i7',
            'index_i5',
            'sequencing_depth',
            'library_protocol__name',
            'read_length__id',
            'index_type__id',
            'index_type__format',
            'index_type__indices_i7',
            'index_type__indices_i5',
        )

        samples_qs = Sample.objects.select_related(
            'library_protocol',
            'read_length',
            'index_type',
        ).prefetch_related(
            'index_type__indices_i7',
            'index_type__indices_i5',
        ).filter(
            Q(is_pooled=False) & (Q(status=2) | Q(status=-2))
        ).only(
            'id',
            'name',
            'barcode',
            'index_i7',
            'index_i5',
            'sequencing_depth',
            'library_protocol__name',
            'read_length__id',
            'index_type__id',
            'index_type__format',
            'index_type__indices_i7',
            'index_type__indices_i5',
        )

        queryset = Request.objects.prefetch_related(
            Prefetch('libraries', queryset=libraries_qs),
            Prefetch('samples', queryset=samples_qs),
        )

        serializer = IndexGeneratorSerializer(queryset, many=True)
        data = list(itertools.chain(*serializer.data))
        data = sorted(data, key=lambda x: x['barcode'][3:])
        return Response(data)

    @action(methods=['post'], detail=False)
    def generate_indices(self, request):
        """ Generate indices for given libraries and samples. """
        libraries = json.loads(request.data.get('libraries', '[]'))
        samples = json.loads(request.data.get('samples', '[]'))
        start_coord = request.data.get('start_coord', None)
        direction = request.data.get('direction', None)

        try:
            index_generator = IndexGenerator(
                libraries,
                samples,
                start_coord,
                direction,
            )
            data = index_generator.generate()
        except Exception as e:
            return Response({'success': False, 'message': str(e)}, 400)
        return Response({'success': True, 'data': data})

    @action(methods=['post'], detail=False)
    def save_pool(self, request):
        """
        Create a pool after generating indices, add libraries and "converted"
        samples to it, update the pool size, and create a Library Preparation
        object and a Pooling object for each added library/sample.
        """
        pool_size_id = request.data.get('pool_size_id', None)
        libraries = json.loads(request.data.get('libraries', '[]'))
        samples = json.loads(request.data.get('samples', '[]'))

        try:
            if not any(libraries) and not any(samples):
                raise ValueError('No libraries nor samples have been provided')

            try:
                pool_size = PoolSize.objects.get(pk=pool_size_id)
            except (ValueError, PoolSize.DoesNotExist):
                raise ValueError('Invalid Pool Size id.')

            pool = Pool(user=request.user, size=pool_size)
            pool.save()

            library_ids = [x['pk'] for x in libraries]
            sample_ids = [x['pk'] for x in samples]

            # Check all indices on uniqueness
            pairs = list(map(
                lambda x: (x['index_i7'], x['index_i5']), libraries + samples))
            if len(pairs) != len(set(pairs)):
                raise ValueError('Some of the indices are not unique.')

            try:
                for s in samples:
                    sample = Sample.objects.get(pk=s['pk'])
                    dual = sample.index_type.is_dual
                    index_i7 = s['index_i7']
                    index_i5 = s['index_i5']

                    if index_i7 == '':
                        raise ValueError(
                            f'Index I7 is not set for "{sample.name}".')

                    if dual and index_i5 == '':
                        raise ValueError(
                            f'Index I5 is not set for "{sample.name}".')

                    # Update sample fields
                    sample.index_i7 = index_i7
                    sample.index_i5 = index_i5
                    sample.save(update_fields=['index_i7', 'index_i5'])

            except ValueError as e:
                pool.delete()
                raise e

        except Exception as e:
            return Response({'success': False, 'message': str(e)}, 400)

        pool.libraries.add(*library_ids)
        pool.samples.add(*sample_ids)

        return Response({'success': True})
