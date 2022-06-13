import datetime
import calendar
import numpy as np
from dateutil.relativedelta import relativedelta

from django.apps import apps
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Prefetch, Min

from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from month import Month
from xlwt import Workbook, XFStyle

from common.views import CsrfExemptSessionAuthentication

from .models import (
    InvoicingReport,
    FixedCosts,
    LibraryPreparationCosts,
    SequencingCosts,
)
from .serializers import (
    InvoicingSerializer,
    FixedCostsSerializer,
    LibraryPreparationCostsSerializer,
    SequencingCostsSerializer,
)
from django.db import transaction
Request = apps.get_model('request', 'Request')
ReadLength = apps.get_model('library_sample_shared', 'ReadLength')
LibraryProtocol = apps.get_model('library_sample_shared', 'LibraryProtocol')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')
Flowcell = apps.get_model('flowcell', 'Flowcell')





class InvoicingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]

    serializer_class = InvoicingSerializer

    def get_serializer_context(self):
        today = datetime.date.today()
        year = self.request.query_params.get('year', today.year)
        month = self.request.query_params.get('month', today.month)
        ctx = {'curr_month': month, 'curr_year': year, 'today': today}
        return ctx

    def get_queryset(self):
        today = datetime.date.today()
        year = self.request.query_params.get('year', today.year)
        month = self.request.query_params.get('month', today.month)


        flowcell_qs = Flowcell.objects.select_related(
            'sequencer',
        ).order_by('flowcell_id')

        libraries_qs = Library.objects.filter(
            ~Q(pool=None)
        ).select_related(
            'read_length', 'library_protocol',
        ).only('read_length', 'library_protocol__name')
        samples_qs = Sample.objects.filter(
            ~Q(pool=None) & ~Q(status=-1)
        ).select_related(
            'read_length', 'library_protocol',
        ).only('read_length', 'library_protocol__name')

        queryset = Request.objects.filter(
            flowcell__create_time__year=year,
            flowcell__create_time__month=month,
            sequenced=True,
        ).select_related(
            'cost_unit',
        ).prefetch_related(
            Prefetch('flowcell', queryset=flowcell_qs),
            Prefetch('libraries', queryset=libraries_qs),
            Prefetch('samples', queryset=samples_qs),
        ).distinct().annotate(
            sequencing_date=Min('flowcell__create_time')
        ).only(
            'name',
            'cost_unit__name',
        ).order_by('sequencing_date', 'pk')



        return queryset


    def list(self,request):
        queryset = self.filter_queryset(self.get_queryset())

        today = datetime.date.today()
        year = self.request.query_params.get('year', today.year)
        month = self.request.query_params.get('month', today.month)
        ctx = {'curr_month': month, 'curr_year': year, 'today': today}
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


    @action(methods=['get'], detail=False)
    def billing_periods(self, request):
        flowcells = Flowcell.objects.all()
        data = []

        if flowcells.count() == 0:
            return Response(data)

        start_date = flowcells.first().create_time
        end_date = flowcells.last().create_time
        end_date = end_date + relativedelta(months=1)

        dates = np.arange(start_date, end_date, dtype='datetime64[M]').tolist()
        for dt in dates:
            try:
                report = InvoicingReport.objects.get(
                    month=dt.strftime('%Y-%m'))
                report_url = settings.MEDIA_URL + report.report.name
            except InvoicingReport.DoesNotExist:
                report_url = ''
            data.append({
                'name': dt.strftime('%B %Y'),
                'value': [dt.year, dt.month],
                'report_url': report_url,
            })

        return Response(data)

    @action(methods=['post'], detail=False,
            authentication_classes=[CsrfExemptSessionAuthentication])
    def upload(self, request):
        """ Upload Invoicing Report. """
        month = request.data.get('month', None)
        report = request.data.get('report', None)

        if not month or not report:
            return Response({
                'success': False,
                'error': 'Month or report is not set.',
            }, 400)

        try:
            report = InvoicingReport.objects.get(month=month)
            report.report = request.data.get('report')
        except InvoicingReport.DoesNotExist:
            report = InvoicingReport(
                month=Month.from_string(month),
                report=request.data.get('report')
            )
        finally:
            report.save()

        return JsonResponse({'success': True})

    @action(methods=['get'], detail=False)
    def download(self, request):
        """ Download Invoicing Report. """
        today = datetime.date.today()
        year = self.request.query_params.get('year', today.year)
        month = int(self.request.query_params.get('month', today.month))

        filename = f'Invoicing_Report_{calendar.month_name[month]}_{year}.xls'
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        queryset = self.filter_queryset(self.get_queryset())
        data = self.get_serializer(queryset, many=True).data

        wb = Workbook(encoding='utf-8')

        font_style = XFStyle()
        font_style.alignment.wrap = 1
        font_style_bold = XFStyle()
        font_style_bold.font.bold = True

        def write_header(ws, row_num, header):
            for i, column in enumerate(header):
                ws.write(row_num, i, column, font_style_bold)
                ws.col(i).width = 8000

        def write_row(ws, row_num, row):
            for i in range(len(row)):
                ws.write(row_num, i, row[i], font_style)

        # First sheet
        ws = wb.add_sheet('Invoicing')
        row_num = 0
        header = [
            'Request ID',
            'Cost Unit',
            'Sequencer',
            'Date + Flowcell ID',
            'Pool ID',
            '% of Lanes',
            'Read Length',
            '# of Libraries/Samples',
            'Library Preparation Protocol',
            'Fixed Costs',
            'Sequencing Costs',
            'Preparation Costs',
            'Variable Costs',
            'Total Costs',
        ]
        write_header(ws, row_num, header)

        for item in data:
            row_num += 1

            # cost_units = '; '.join(sorted(item['cost_unit']))
            sequencers = '; '.join(
                sorted(list({x['sequencer_name'] for x in item['sequencer']})))
            flowcells = '; '.join(item['flowcell'])
            pools = '; '.join(item['pool'])

            percentage = '; '.join(list(
                map(
                    lambda x: ', '.join([y['percentage'] for y in x['pools']]),
                    item['percentage']
                )
            ))

            read_lengths = '; '.join(ReadLength.objects.filter(
                pk__in=item['read_length']
            ).order_by('name').values_list('name', flat=True))

            protocol = LibraryProtocol.objects.get(pk=item['library_protocol'])

            row = [
                item['request'],
                item['cost_unit'],
                sequencers,
                flowcells,
                pools,
                percentage,
                read_lengths,
                item['num_libraries_samples'],
                protocol.name,
                item['fixed_costs'],
                item['sequencing_costs'],
                item['preparation_costs'],
                item['variable_costs'],
                item['total_costs'],
            ]
            write_row(ws, row_num, row)

        # Second sheet
        ws = wb.add_sheet('Fixed Costs')
        row_num = 0
        header = ['Sequencer', 'Price']
        write_header(ws, row_num, header)
        for item in FixedCosts.objects.all():
            row_num += 1
            row = [item.sequencer.name, item.price]
            write_row(ws, row_num, row)

        # Third sheet
        ws = wb.add_sheet('Preparation Costs')
        row_num = 0
        header = ['Library Protocol', 'Price']
        write_header(ws, row_num, header)
        for item in LibraryPreparationCosts.objects.all():
            row_num += 1
            row = [item.library_protocol.name, item.price]
            write_row(ws, row_num, row)

        # Fourth sheet
        ws = wb.add_sheet('Sequencing Costs')
        row_num = 0
        header = ['Sequencer + Read Length', 'Price']
        write_header(ws, row_num, header)
        for item in SequencingCosts.objects.all():
            row_num += 1
            row = [
                f'{item.sequencer.name} {item.read_length.name}',
                item.price,
            ]
            write_row(ws, row_num, row)

        wb.save(response)
        return response


class FixedCostsViewSet(mixins.UpdateModelMixin,
                        viewsets.ReadOnlyModelViewSet):
    """ Get the list of Fixed Costs. """
    permission_classes = [IsAdminUser]
    queryset = FixedCosts.objects.filter(sequencer__obsolete = settings.NON_OBSOLETE)
    serializer_class = FixedCostsSerializer


class LibraryPreparationCostsViewSet(mixins.UpdateModelMixin,
                                     viewsets.ReadOnlyModelViewSet):
    """ Get the list of Library Preparation Costs. """

    permission_classes = [IsAdminUser]
    queryset = LibraryPreparationCosts.objects.filter(library_protocol__obsolete=settings.NON_OBSOLETE)
    print(queryset.query)

    serializer_class = LibraryPreparationCostsSerializer



class SequencingCostsViewSet(mixins.UpdateModelMixin,
                             viewsets.ReadOnlyModelViewSet):
    """ Get the list of Sequencing Costs. """
    permission_classes = [IsAdminUser]
    queryset = SequencingCosts.objects.filter(sequencer__obsolete=settings.NON_OBSOLETE)
    serializer_class = SequencingCostsSerializer
