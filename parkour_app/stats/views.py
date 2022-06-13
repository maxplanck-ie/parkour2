import json
import itertools
from datetime import datetime

from django.apps import apps
from django.http import HttpResponse
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from xlwt import Workbook, XFStyle

from common.utils import get_date_range
from common.views import CsrfExemptSessionAuthentication

from .serializers import RunsSerializer, SequencesSerializer

Request = apps.get_model('request', 'Request')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')
Flowcell = apps.get_model('flowcell', 'Flowcell')
Lane = apps.get_model('flowcell', 'Lane')


class RunStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = RunsSerializer

    def get_queryset(self):
        request_qs = Request.objects.only('name')

        libraries_qs = Library.objects.filter(~Q(status=-1)).select_related(
            'read_length',
            'library_protocol',
            'library_type',
        ).prefetch_related(
            Prefetch('request', queryset=request_qs, to_attr='fetched_request')
        ).only(
            'read_length__name',
            'library_protocol__name',
            'library_type__name',
        )

        samples_qs = Sample.objects.filter(~Q(status=-1)).select_related(
            'read_length',
            'library_protocol',
            'library_type',
        ).prefetch_related(
            Prefetch('request', queryset=request_qs, to_attr='fetched_request')
        ).only(
            'read_length__name',
            'library_protocol__name',
            'library_type__name',
        )

        lanes_qs = Lane.objects.select_related('pool').prefetch_related(
            Prefetch(
                'pool__libraries',
                queryset=libraries_qs,
                to_attr='fetched_libraries',
            ),
            Prefetch(
                'pool__samples',
                queryset=samples_qs,
                to_attr='fetched_samples',
            ),
        ).only(
            'name',
            'phix',
            'loading_concentration',
            'pool__name',
            'pool__libraries',
            'pool__samples',
        )

        queryset = Flowcell.objects.exclude(
            matrix__isnull=True,
        ).select_related(
            'sequencer',
        ).prefetch_related(
            Prefetch('lanes', queryset=lanes_qs, to_attr='fetched_lanes'),
        ).order_by('-create_time')

        return queryset

    def list(self, request):
        now = datetime.now()
        start = request.query_params.get('start', now)
        end = request.query_params.get('end', now)
        start, end = get_date_range(start, end, '%Y-%m-%dT%H:%M:%S')

        queryset = self.filter_queryset(self.get_queryset()).filter(
            create_time__gte=start,
            create_time__lte=end,
        )

        serializer = self.get_serializer(queryset, many=True)
        data = list(itertools.chain(*serializer.data))
        return Response(data)

    @action(methods=['post'], detail=False)
    def upload(self, request):
        flowcell_id = request.data.get('flowcell_id', '')
        matrix = request.data.get('matrix', '')

        try:
            flowcell = Flowcell.objects.get(flowcell_id=flowcell_id)
        except (ValueError, Flowcell.DoesNotExist):
            return Response({
                'success': False,
                'message': f'Flowcell with id "{flowcell_id}" doesn\'t exist.',
            }, 400)

        try:
            matrix = json.loads(matrix)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid matrix data.',
            }, 400)

        # Update pre-existing information
        currentMatrix = list()
        if flowcell.matrix:
            currentMatrix = flowcell.matrix

        found = dict()
        for idx, entry in enumerate(currentMatrix):
            found[entry['name']] = idx
        for entry in matrix:
            if entry['name'] in found:
                currentMatrix[found[entry['name']]] = entry
            else:
                currentMatrix.append(entry)

        flowcell.matrix = currentMatrix
        flowcell.save(update_fields=['matrix'])
        return Response({'success': True})


class SequencesStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = SequencesSerializer

    def get_queryset(self):
        libraries_qs = Library.objects.filter(~Q(status=-1)).select_related(
            'library_protocol',
            'library_type',
        ).only(
            'name',
            'barcode',
            'library_protocol__name',
            'library_type__name',
        )

        samples_qs = Sample.objects.filter(~Q(status=-1)).select_related(
            'library_protocol',
            'library_type',
        ).only(
            'name',
            'barcode',
            'library_protocol__name',
            'library_type__name',
        )

        requests_qs = Request.objects.prefetch_related(
            Prefetch(
                'libraries',
                queryset=libraries_qs,
                to_attr='fetched_libraries',
            ),
            Prefetch(
                'samples',
                queryset=samples_qs,
                to_attr='fetched_samples',
            ),
        ).only(
            'name',
            'libraries',
            'samples',
        )

        lanes_qs = Lane.objects.select_related(
            'pool'
        ).prefetch_related(
            Prefetch(
                'pool__libraries',
                queryset=Library.objects.only('barcode'),
                to_attr='fetched_libraries',
            ),
            Prefetch(
                'pool__samples',
                queryset=Sample.objects.only('barcode'),
                to_attr='fetched_samples',
            ),
        ).only(
            'name',
            'pool__name',
            'pool__libraries',
            'pool__samples',
        ).order_by('name')

        queryset = Flowcell.objects.exclude(
            sequences__isnull=True,
        ).select_related(
            'sequencer',
        ).prefetch_related(
            Prefetch(
                'lanes',
                queryset=lanes_qs,
                to_attr='fetched_lanes',
            ),
            Prefetch(
                'requests',
                queryset=requests_qs,
                to_attr='fetched_requests',
            ),
        ).order_by('-create_time')

        return queryset

    def list(self, request):
        now = datetime.now()
        start = request.query_params.get('start', now)
        end = request.query_params.get('end', now)
        start, end = get_date_range(start, end, '%Y-%m-%dT%H:%M:%S')

        queryset = self.filter_queryset(self.get_queryset()).filter(
            create_time__gte=start,
            create_time__lte=end,
        )

        serializer = self.get_serializer(queryset, many=True)
        data = list(itertools.chain(*serializer.data))
        return Response(data)

    @action(methods=['post'], detail=False)
    def upload(self, request):
        flowcell_id = request.data.get('flowcell_id', '')
        sequences = request.data.get('sequences', '')
        flowcell = get_object_or_404(Flowcell, flowcell_id=flowcell_id)

        try:
            sequences = json.loads(sequences)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid sequences data.',
            }, 400)

        # Update pre-existing sequence information
        currentSequences = list()
        if flowcell.sequences:
            currentSequences = flowcell.sequences

        found = dict()
        for idx, entry in enumerate(currentSequences):
            found[entry['barcode']] = idx
        for entry in sequences:
            if entry['barcode'] in found:
                currentSequences[found[entry['barcode']]] = entry
            else:
                currentSequences.append(entry)

        flowcell.sequences = currentSequences
        flowcell.save(update_fields=['sequences'])
        return Response({'success': True})

    @action(methods=['post'], detail=False,
            authentication_classes=[CsrfExemptSessionAuthentication])
    def download_report(self, request):
        barcodes = json.loads(request.data.get('barcodes', '[]'))
        barcodes_map = {b: True for b in barcodes}

        filename = 'Sequences_Statistics_Report.xls'
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = list(itertools.chain(*serializer.data))

        font_style = XFStyle()
        font_style.alignment.wrap = 1
        font_style_bold = XFStyle()
        font_style_bold.font.bold = True

        wb = Workbook(encoding='utf-8')
        ws = wb.add_sheet('FC_Loading_Benchtop_Protocol')

        header = [
            'Request',
            'Barcode',
            'Name',
            'Lane',
            'Pool',
            'Library Protocol',
            'Library Type',
            'Reads PF (M), requested',
            'Reads PF (M), sequenced',
            'confident off-species reads',
            '% Optical Duplicates',
            '% dupped reads',
            '% mapped reads',
            'Insert Size',
        ]

        row_num = 0

        for i, column in enumerate(header):
            ws.write(row_num, i, column, font_style_bold)
            ws.col(i).width = 8000

        for item in data:
            if item['barcode'] in barcodes_map:
                row_num += 1

                reads_pf_sequenced = item.get('reads_pf_sequenced', '')
                if reads_pf_sequenced != '':
                    reads_pf_sequenced = round(
                        int(reads_pf_sequenced) / 1_000_000, 1)

                row = [
                    item['request'],
                    item['barcode'],
                    item['name'],
                    ','.join(item['lane']),
                    item['pool'],
                    item['library_protocol'],
                    item['library_type'],
                    item.get('reads_pf_requested', ''),
                    reads_pf_sequenced,
                    item.get('confident_reads', ''),
                    item.get('optical_duplicates', ''),
                    item.get('dupped_reads', ''),
                    item.get('mapped_reads', ''),
                    item.get('insert_size', ''),
                ]

                for i in range(len(row)):
                    ws.write(row_num, i, row[i], font_style)

        wb.save(response)
        return response
