import json
import time
import logging
import itertools

from django.apps import apps
from django.http import HttpResponse
from django.db.models import Q, Prefetch

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from xlwt import Workbook, XFStyle, Formula

from common.views import CsrfExemptSessionAuthentication
from common.mixins import LibrarySampleMultiEditMixin

from .models import Pooling

from .serializers import (
    PoolingLibrarySerializer,
    PoolingSampleSerializer,
    PoolSerializer,
)

Request = apps.get_model('request', 'Request')
IndexPair = apps.get_model('library_sample_shared', 'IndexPair')
Library = apps.get_model('library', 'Library')
Sample = apps.get_model('sample', 'Sample')
Pool = apps.get_model('index_generator', 'Pool')
LibraryPreparation = apps.get_model(
    'library_preparation', 'LibraryPreparation')

logger = logging.getLogger('db')


class PoolingViewSet(LibrarySampleMultiEditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    library_model = Library
    sample_model = Sample
    library_serializer = PoolingLibrarySerializer
    sample_serializer = PoolingSampleSerializer

    def get_queryset(self):
        libraries_qs = Library.objects.filter(
            Q(status=2) | Q(status=-2)
        ).select_related(
            'index_type',
        ).prefetch_related(
            'index_type__indices_i7',
            'index_type__indices_i5',
        ).only(
            'name',
            'barcode',
            'status',
            'index_type',
            'index_i7',
            'index_i5',
            'sequencing_depth',
            'mean_fragment_size',
            'concentration_facility'
        )

        samples_qs = Sample.objects.filter(
            Q(status=3) | Q(status=2) | Q(status=-2)
        ).select_related(
            'index_type',
        ).prefetch_related(
            'index_type__indices_i7',
            'index_type__indices_i5',
        ).only(
            'name',
            'barcode',
            'status',
            'index_type',
            'index_i7',
            'index_i5',
            'sequencing_depth',
            'is_converted',
        )

        return Pool.objects.select_related(
            'size'
        ).prefetch_related(
            Prefetch('libraries', queryset=libraries_qs),
            Prefetch('samples', queryset=samples_qs),
        )

    def get_context(self, queryset):
        library_ids = queryset.values_list('libraries', flat=True)
        sample_ids = queryset.values_list('samples', flat=True)

        # Get Requests in one query
        requests = Request.objects.filter(
            Q(libraries__in=library_ids) | Q(samples__in=sample_ids)
        ).prefetch_related(
            'libraries',
            'samples'
        ).values(
            'pk',
            'name',
            'libraries__id',
            'samples__id',
        ).distinct()

        requests_map = {}
        for item in requests:
            if item['libraries__id']:
                requests_map[item['libraries__id'], 'Library'] = {
                    'pk': item['pk'],
                    'name': item['name'],
                }
            if item['samples__id']:
                requests_map[item['samples__id'], 'Sample'] = {
                    'pk': item['pk'],
                    'name': item['name'],
                }

        # Get Library Preparation objects in one query
        preparation_objects = LibraryPreparation.objects.filter(
            sample__in=sample_ids
        ).select_related('sample').only(
            'sample__id',
            'mean_fragment_size',
            'concentration_library',
        )
        library_reparation_map = {x.sample.pk: x for x in preparation_objects}

        # Get Pooling objects in one query
        pooling_objects = Pooling.objects.select_related(
            'library', 'sample'
        ).filter(
            Q(library__in=library_ids) | Q(sample__in=sample_ids)
        ).only('library__id', 'sample__id', 'concentration_c1', 'create_time')
        pooling_map = {}
        for x in pooling_objects:
            if x.library:
                pooling_map[x.library.pk, 'Library'] = x
            elif x.sample:
                pooling_map[x.sample.pk, 'Sample'] = x

        # Get coordinates
        index_types1 = {
            l.index_type.pk
            for pool in queryset
            for l in pool.libraries.all()
            if l.index_type
        }
        index_types2 = {
            s.index_type.pk
            for pool in queryset
            for s in pool.samples.all()
            if s.index_type
        }
        index_types = index_types1 | index_types2
        index_pairs = IndexPair.objects.filter(
            index_type__pk__in=index_types,
        ).select_related('index_type', 'index1', 'index2').distinct()
        coordinates_map = {
            (
                ip.index_type.pk,
                ip.index1.index_id,
                ip.index2.index_id if ip.index2 else '',
            ): ip.coordinate
            for ip in index_pairs
        }

        return {
            'requests': requests_map,
            'library_preparation': library_reparation_map,
            'pooling': pooling_map,
            'coordinates': coordinates_map,
        }

    def list(self, request):
        """ Get the list of all pooling objects. """
        queryset = self.get_queryset()
        serializer = PoolSerializer(
            queryset, many=True, context=self.get_context(queryset))
        data = list(itertools.chain(*serializer.data))
        data = sorted(data, key=lambda x: x['barcode'][3:])
        return Response(data)

    @action(methods=['post'], detail=True)
    def edit_comment(self, request, pk=None):

        instance = Pool.objects.filter(pk=pk)

        post_data = self._get_post_data(request)
        newComment = post_data['newComment']

        instance.update(comment=newComment)
        return Response({'success': True})

    @action(methods=['post'], detail=False,
            authentication_classes=[CsrfExemptSessionAuthentication])
    def download_benchtop_protocol(self, request):
        """ Generate Benchtop Protocol as XLS file for selected records. """
        response = HttpResponse(content_type='application/ms-excel')
        libraries = json.loads(request.data.get('libraries', '[]'))
        samples = json.loads(request.data.get('samples', '[]'))
        bp = json.loads(request.data.get('bp','[]'))

        pool_id = request.POST.get('pool_id', '')
        pool = Pool.objects.get(pk=pool_id)

        records = list(itertools.chain(
            Library.objects.filter(pk__in=libraries),
            Sample.objects.filter(pk__in=samples),
        ))
        records = sorted(records, key=lambda x: x.barcode[3:])

        f_name = 'Pooling_Benchtop_Protocol.xls'
        response['Content-Disposition'] = 'attachment; filename="%s"' % f_name

        wb = Workbook(encoding='utf-8')

        # First sheet
        ws = wb.add_sheet('Pooling')
        col_letters = {
            0: 'A',   # Request ID
            1: 'B',   # Library
            2: 'C',   # Barcode
            3: 'D',   # Concentration Library
            4: 'E',   # Mean Fragment Size
            5: 'F',   # Library Concentration C1
            6: 'G',   # Sequencing Depth
            7: 'H',   # % library in Pool
            8: 'I',   # Normalized Library Concentration C2
            9: 'J',   # Volume to Pool
            10: 'K',  # µl library
            11: 'L',  # µl EB
        }

        header = ['Request ID', 'Library', 'Barcode',
                  'Concentration Library (ng/µl)', 'Mean Fragment Size (bp)',
                  'Library Concentration C1 (nM)', 'Sequencing Depth (M)',
                  '% library in Pool',
                  'Normalized Library Concentration C2 (nM)',
                  'Volume to Pool (µl)', 'µl library', 'µl EB']

        font_style = XFStyle()
        font_style.alignment.wrap = 1
        font_style_bold = XFStyle()
        font_style_bold.font.bold = True

        ws.write(0, 0, 'Pool ID', font_style_bold)               # A1
        ws.write(0, 1, pool.name, font_style_bold)               # B1
        ws.write(1, 0, 'Pool Volume', font_style_bold)           # A2
        ws.write(2, 0, 'Sum Sequencing Depth', font_style_bold)  # A3
        ws.write(3, 0, '', font_style)                           # A4

        row_num = 4

        for i, column in enumerate(header):
            ws.write(row_num, i, column, font_style_bold)
            ws.col(i).width = 7000  # Set column width

        lib_index = 0
        for index,record in enumerate(records):
            row_num += 1
            row_idx = str(row_num + 1)
            req = record.request.get()

            if isinstance(record, Library):
                concentration = record.concentration_facility
                #mean_fragment_size = record.mean_fragment_size
                #mean_fragment_size = bp[index]
                mean_fragment_size = bp[lib_index]
                lib_index += 1
            else:
                concentration = record.librarypreparation.concentration_library
                mean_fragment_size = \
                    record.librarypreparation.mean_fragment_size

            row = [
                req.name,            # Request ID
                record.name,         # Library
                record.barcode,      # Barcode
                concentration,       # Concentration Library
                mean_fragment_size,  # Mean Fragment Size
            ]

            # Library Concentration C1 =
            # (Library Concentration / Mean Fragment Size * 650) * 10^6
            col_library_concentration = col_letters[3]
            col_mean_fragment_size = col_letters[4]
            formula = '%s%s/(%s%s*650)*1000000' % (
                col_library_concentration, row_idx,
                col_mean_fragment_size, row_idx
            )
            row.append(Formula(formula))

            # Sequencing Depth
            row.append(record.sequencing_depth)

            # % library in Pool
            col_sequencing_depth = col_letters[6]
            formula = '%s%s/$B$3*100' % (col_sequencing_depth, row_idx)
            row.append(Formula(formula))

            row.append('')  # Concentration C2

            # Volume to Pool
            col_percentage = col_letters[7]
            formula = '$B$2*%s%s/100' % (col_percentage, row_idx)
            row.append(Formula(formula))

            # µl library
            col_volume_pool = col_letters[9]
            col_normalization_c2 = col_letters[8]
            col_concentration_c1 = col_letters[5]
            formula = '({}{}*{}{})/{}{}'.format(
                col_volume_pool, row_idx,
                col_normalization_c2, row_idx,
                col_concentration_c1, row_idx,
            )
            row.append(Formula(formula))

            # µl EB
            col_ul_library = col_letters[10]
            formula = '{}{}-{}{}'.format(
                col_volume_pool, row_idx,
                col_ul_library, row_idx,
            )
            row.append(Formula(formula))

            # Add rows to spreadsheet
            for i in range(len(row)):
                ws.write(row_num, i, row[i], font_style)
        lib_index = 0
        # Write Sum µl EB
        col_ul_eb = col_letters[11]
        formula = 'SUM({}{}:{}{})'.format(
            col_ul_eb, 6,
            col_ul_eb, row_idx
        )
        ws.write(int(row_idx), 11, Formula(formula), font_style)

        # Write Sum Sequencing Depth
        formula = 'SUM(%s%s:%s%s)' % (
            col_sequencing_depth, 6,
            col_sequencing_depth, str(row_num + 1)
        )
        ws.write(2, 1, Formula(formula), font_style)

        # Second sheet
        ws = wb.add_sheet('ng-ul to nM')
        ws.write(0, 0, 'Convert ng/µl to nM', font_style_bold)  # A1
        ws.write(2, 0,                                          # A3
                 'Concentration in nM = ((concentration ng/µl) / (650 ' + \
                 'g/mol x average library size bp)) x 10^6', font_style_bold)

        # Table 1
        ws.write(6, 0, 'Date', font_style_bold)                   # A7
        ws.write(6, 1, 'Operator', font_style_bold)               # B7
        ws.write(6, 2, 'Sample ID', font_style_bold)              # C7
        ws.write(6, 3, 'Concentration (ng/µl)', font_style_bold)  # D7
        ws.write(6, 4, 'Average bp', font_style_bold)             # E7
        ws.write(6, 5, 'nM', font_style_bold)                     # F7
        for i in range(40):
            row_idx = 7 + i
            for j in range(5):
                ws.write(row_idx, j, '', font_style)
            formula = f'D{row_idx + 1}/(650*E{row_idx + 1})*10^6'
            ws.write(row_idx, j + 1, Formula(formula), font_style)

        # Table 2
        ws.write(6, 11, 'Guidelines', font_style_bold)    # L7
        ws.write(6, 12, 'nM (optimal)', font_style_bold)  # M7
        ws.write(6, 13, 'possible', font_style_bold)      # N7
        ws.write(7, 11, 'HiSeq3000', font_style)          # L8
        ws.write(8, 11, 'HiSeq2500', font_style)          # L9
        ws.write(9, 11, 'NextSeq', font_style)            # L10
        ws.write(10, 11, 'MiSeq', font_style)             # L11
        ws.write(7, 12, 3, font_style)                    # M8
        ws.write(8, 12, 1, font_style)                    # M9
        ws.write(9, 12, '0.5 - 4', font_style)            # M10
        ws.write(10, 12, 4, font_style)                   # M11
        ws.write(10, 13, 4, font_style)                   # N11

        # Table 3
        ws.write(13, 8, 'Add V2 to samples to reach desired C2', font_style)
        ws.write(14, 8, 'V1', font_style_bold)   # I15
        ws.write(14, 9, 'C1', font_style_bold)   # J15
        ws.write(14, 10, 'V2', font_style_bold)  # K15
        ws.write(14, 11, 'C2', font_style_bold)  # L15
        for i in range(8):
            row_idx = 15 + i
            ws.write(row_idx, 8, '', font_style)                   # V1
            formula_c1 = f'F{8 + i}'
            ws.write(row_idx, 9, Formula(formula_c1), font_style)  # C1
            v2_idx = row_idx + 1
            formula_v2 = f'((I{v2_idx}*J{v2_idx})/L{v2_idx})-I{v2_idx}'
            ws.write(row_idx, 10, Formula(formula_v2), font_style)  # V2
            ws.write(row_idx, 11, 4 + i, font_style)  # C2

        wb.save(response)
        return response

    @action(methods=['post'], detail=False,
            authentication_classes=[CsrfExemptSessionAuthentication])
    def download_pooling_template(self, request):
        """ Generate Pooling Template as XLS file for selected records. """
        response = HttpResponse(content_type='application/ms-excel')
        libraries = json.loads(request.data.get('libraries', '[]'))
        samples = json.loads(request.data.get('samples', '[]'))

        records = list(itertools.chain(
            Library.objects.filter(pk__in=libraries),
            Sample.objects.filter(pk__in=samples),
        ))
        records = sorted(records, key=lambda x: x.barcode[3:])

        f_name = 'QC_Normalization_and_Pooling_Template.xls'
        response['Content-Disposition'] = 'attachment; filename="%s"' % f_name

        wb = Workbook(encoding='utf-8')
        ws = wb.add_sheet('QC Normalization and Pooling')
        col_letters = {
            0: 'A',   # Library
            1: 'B',   # Barcode
            2: 'C',   # ng/µl
            3: 'D',   # bp
            4: 'E',   # nM
            5: 'F',   # Date
            6: 'G',   # Comments
        }

        header = ['Library', 'Barcode', 'ng/µl', 'bp', 'nM', 'Date',
                  'Comments']
        row_num = 0

        font_style = XFStyle()
        font_style.font.bold = True

        for i, column in enumerate(header):
            ws.write(row_num, i, column, font_style)
            ws.col(i).width = 7000  # Set column width

        font_style = XFStyle()
        font_style.alignment.wrap = 1

        for record in records:
            row_num += 1
            row_idx = str(row_num + 1)

            if isinstance(record, Library):
                concentration = record.concentration_facility
                mean_fragment_size = record.mean_fragment_size
            else:
                concentration = record.librarypreparation.concentration_library
                mean_fragment_size = \
                    record.librarypreparation.mean_fragment_size

            row = [
                record.name,         # Library
                record.barcode,      # Barcode
                concentration,       # ng/µl
                mean_fragment_size,  # bp
            ]

            # nM = Library Concentration / ( Mean Fragment Size * 650 ) * 10^6
            col_concentration = col_letters[2]
            col_mean_fragment_size = col_letters[3]
            formula = '{}{}/({}{})*1000000'.format(
                col_concentration, row_idx,
                col_mean_fragment_size, row_idx
            )
            row.append(Formula(formula))

            row.extend([
                time.strftime('%d.%m.%Y'),  # Date
                record.comments,            # Comments
            ])

            for i in range(2):
                ws.write(row_num, i, row[i], font_style)

        wb.save(response)
        return response

    def _get_post_data(self, request):
        post_data = {}
        if request.is_ajax():
            post_data = request.data.get('data', {})
            if isinstance(post_data, str):
                post_data = json.loads(post_data)
        else:
            post_data = json.loads(request.data.get('data', '{}'))
        return post_data
