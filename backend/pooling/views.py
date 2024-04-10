import itertools
import json
import logging
import time

from common.mixins import LibrarySampleMultiEditMixin
from common.views import CsrfExemptSessionAuthentication
from django.apps import apps
from django.db.models import Prefetch, Q
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from xlwt import Formula, Workbook, XFStyle

from .models import Pooling
from .serializers import (
    PoolingLibrarySerializer,
    PoolingSampleSerializer,
    PoolSerializer,
)

Request = apps.get_model("request", "Request")
IndexPair = apps.get_model("library_sample_shared", "IndexPair")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
Pool = apps.get_model("index_generator", "Pool")
LibraryPreparation = apps.get_model("library_preparation", "LibraryPreparation")

logger = logging.getLogger("db")


class PoolingViewSet(LibrarySampleMultiEditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    library_model = Library
    sample_model = Sample
    library_serializer = PoolingLibrarySerializer
    sample_serializer = PoolingSampleSerializer

    def get_queryset(self):
        libraries_qs = (
            Library.objects.filter(Q(status=2) | Q(status=-2))
            .select_related(
                "index_type",
            )
            .prefetch_related(
                "index_type__indices_i7",
                "index_type__indices_i5",
            )
            .only(
                "name",
                "barcode",
                "status",
                "index_type",
                "index_i7",
                "index_i5",
                "sequencing_depth",
                "mean_fragment_size",
                "concentration_facility",
            )
        )

        samples_qs = (
            Sample.objects.filter(Q(status=3) | Q(status=2) | Q(status=-2))
            .select_related(
                "index_type",
            )
            .prefetch_related(
                "index_type__indices_i7",
                "index_type__indices_i5",
            )
            .only(
                "name",
                "barcode",
                "status",
                "index_type",
                "index_i7",
                "index_i5",
                "sequencing_depth",
                "is_converted",
            )
        )

        return (
            Pool.objects.select_related("size")
            .filter(archived=False)
            .prefetch_related(
                Prefetch("libraries", queryset=libraries_qs),
                Prefetch("samples", queryset=samples_qs),
            )
        )

    def get_context(self, queryset):
        library_ids = queryset.values_list("libraries", flat=True)
        sample_ids = queryset.values_list("samples", flat=True)

        # Get Requests in one query
        requests = (
            Request.objects.filter(
                Q(libraries__in=library_ids) | Q(samples__in=sample_ids), archived=False
            )
            .prefetch_related("libraries", "samples")
            .values(
                "pk",
                "name",
                "libraries__id",
                "samples__id",
            )
            .distinct()
        )

        requests_map = {}
        for item in requests:
            if item["libraries__id"]:
                requests_map[item["libraries__id"], "Library"] = {
                    "pk": item["pk"],
                    "name": item["name"],
                }
            if item["samples__id"]:
                requests_map[item["samples__id"], "Sample"] = {
                    "pk": item["pk"],
                    "name": item["name"],
                }

        # Get Library Preparation objects in one query
        preparation_objects = (
            LibraryPreparation.objects.filter(archived=False, sample__in=sample_ids)
            .select_related("sample")
            .only(
                "sample__id",
                "mean_fragment_size",
                "concentration_library",
            )
        )
        library_reparation_map = {x.sample.pk: x for x in preparation_objects}

        # Get Pooling objects in one query
        pooling_objects = (
            Pooling.objects.filter(archived=False)
            .select_related("library", "sample")
            .filter(Q(library__in=library_ids) | Q(sample__in=sample_ids))
            .only("library__id", "sample__id", "concentration_c1", "create_time")
        )
        pooling_map = {}
        for x in pooling_objects:
            if x.library:
                pooling_map[x.library.pk, "Library"] = x
            elif x.sample:
                pooling_map[x.sample.pk, "Sample"] = x

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
        index_pairs = (
            IndexPair.objects.filter(
                archived=False,
                index_type__pk__in=index_types,
            )
            .select_related("index_type", "index1", "index2")
            .distinct()
        )
        coordinates_map = {
            (
                ip.index_type.pk,
                ip.index1.index_id,
                ip.index2.index_id if ip.index2 else "",
            ): ip.coordinate
            for ip in index_pairs
        }

        return {
            "requests": requests_map,
            "library_preparation": library_reparation_map,
            "pooling": pooling_map,
            "coordinates": coordinates_map,
        }

    def list(self, request):
        """Get the list of all pooling objects."""
        queryset = self.get_queryset()
        serializer = PoolSerializer(
            queryset, many=True, context=self.get_context(queryset)
        )
        data = list(itertools.chain(*serializer.data))
        data = sorted(data, key=lambda x: x["barcode"][3:])
        return Response(data)

    @action(methods=["post"], detail=True)
    def edit_comment(self, request, pk=None):
        instance = Pool.objects.filter(archived=False, pk=pk)

        post_data = self._get_post_data(request)
        newComment = post_data["newComment"]

        instance.update(comment=newComment)
        return Response({"success": True})

    @action(
        methods=["post"],
        detail=False,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def download_benchtop_protocol(self, request):
        """Generate Benchtop Protocol as XLS file for selected records."""
        response = HttpResponse(content_type="application/ms-excel")
        libraries = json.loads(request.data.get("libraries", "[]"))
        samples = json.loads(request.data.get("samples", "[]"))
        bp = json.loads(request.data.get("bp", "[]"))

        pool_id = request.POST.get("pool_id", "")
        pool = Pool.objects.filter(archived=False).get(pk=pool_id)

        records = list(
            itertools.chain(
                Library.objects.filter(pk__in=libraries),
                Sample.objects.filter(pk__in=samples),
            )
        )
        records = sorted(records, key=lambda x: x.barcode[3:])

        f_name = f"{pool_id}_Pooling_Benchtop_Protocol.xls"
        response["Content-Disposition"] = 'attachment; filename="%s"' % f_name

        wb = Workbook(encoding="utf-8")

        font_style = XFStyle()
        font_style.alignment.wrap = 1
        font_style_bold = XFStyle()
        font_style_bold.font.bold = True

        # First sheet
        ws = wb.add_sheet("Smear Analysis")

        column_letters_smear_analysis = {
            0: "A",  # Request ID
            1: "B",  # Library
            2: "C",  # Barcode
            3: "D",  # Concentration Library (ng/µl)
            4: "E",  # Smear Analysis (% Total)
            5: "F",  # Adjusted Concentration Library (ng/µl)
        }

        headers_smear_analysis = [
            "Request ID",
            "Library",
            "Barcode",
            "Concentration Library (ng/µl)",
            "Smear Analysis (% Total)",
            "Adjusted Concentration Library (ng/µl)",
        ]

        row_num = 0

        for i, column in enumerate(headers_smear_analysis):
            ws.write(row_num, i, column, font_style_bold)
            ws.col(i).width = 7000  # Set column width

        lib_index = 0
        for index, record in enumerate(records):
            row_num += 1
            row_idx = str(row_num + 1)
            req = record.request.get()

            if isinstance(record, Library):
                concentration = record.concentration_facility
                smear_analysis = 100
                lib_index += 1
            else:
                concentration = record.librarypreparation.concentration_library
                smear_analysis = record.librarypreparation.smear_analysis

            row = [
                req.name,  # Request ID
                record.name,  # Library
                record.barcode,  # Barcode
                concentration,  # Concentration Library
                smear_analysis,  # Smear Analysis
            ]

            # Adjusted Concentration Library
            col_concentration_library = column_letters_smear_analysis[3]
            col_smear_analysis = column_letters_smear_analysis[4]
            formula = "{}{}*({}{}/100)".format(
                col_concentration_library,
                row_idx,
                col_smear_analysis,
                row_idx,
            )
            row.append(Formula(formula))

            # Writing row data to the sheet
            for i in range(len(row)):
                ws.write(row_num, i, row[i], font_style)

        # Second sheet
        ws = wb.add_sheet("Pooling")
        wb.active_sheet = 1

        column_letters_pooling = {
            0: "A",  # Request ID
            1: "B",  # Library
            2: "C",  # Barcode
            3: "D",  # Adjusted Concentration Library (ng/µl)
            4: "E",  # Dilution Factor
            5: "F",  # Remeasured Concentration, Diluted Adjusted (ng/µl)
            6: "G",  # Mean Fragment Size (bp)
            7: "H",  # Library Concentration C1 (nM)
            8: "I",  # Sequencing Depth (M)
            9: "J",  # % Library in Pool
            10: "K",  # Normalized Library Concentration C2 (nM)
            11: "L",  # Volume to Pool (µl)
            12: "M",  # µl Library
            13: "N",  # µl EB
        }

        headers_pooling = [
            "Request ID",
            "Library",
            "Barcode",
            "Adjusted Concentration Library (ng/µl)",
            "Dilution Factor",
            "Remeasured Concentration, Diluted Adjusted (ng/µl)",
            "Mean Fragment Size (bp)",
            "Library Concentration C1 (nM)",
            "Sequencing Depth (M)",
            "% Library in Pool",
            "Normalized Library Concentration C2 (nM)",
            "Volume to Pool (µl)",
            "µl Library",
            "µl EB",
        ]

        ws.write(0, 0, "Pool ID", font_style_bold)  # A1
        ws.write(0, 1, pool.name, font_style_bold)  # B1
        ws.write(1, 0, "Pool Volume", font_style_bold)  # A2
        ws.write(2, 0, "Sum Sequencing Depth", font_style_bold)  # A3
        ws.write(3, 0, "", font_style)  # A4

        row_num = 4

        for i, column in enumerate(headers_pooling):
            ws.write(row_num, i, column, font_style_bold)
            ws.col(i).width = 7000  # Set column width

        lib_index = 0
        for index, record in enumerate(records):
            row_num += 1
            row_idx = str(row_num + 1)
            req = record.request.get()

            if isinstance(record, Library):
                concentration = record.concentration_facility
                dilution_factor = record.dilution_factor
                mean_fragment_size = bp[lib_index]
                lib_index += 1
            else:
                concentration = record.librarypreparation.concentration_library
                dilution_factor = record.librarypreparation.dilution_factor
                mean_fragment_size = record.librarypreparation.mean_fragment_size

            row = [
                req.name,  # Request ID
                record.name,  # Library
                record.barcode,  # Barcode
            ]

            # Adjusted Concentration Library
            col_adjusted_concentration_library = column_letters_smear_analysis[5]
            formula = "'Smear Analysis'!{}{}".format(
                col_adjusted_concentration_library,
                int(row_idx) - 4,
            )
            row.append(Formula(formula))

            # Dilution Factor
            row.append(dilution_factor)

            # Remeasured Concentration, Diluted Adjusted
            col_remeasured_concentration_library = column_letters_pooling[3]
            col_dilution_factor = column_letters_pooling[4]
            formula = "{}{}/{}{}".format(
                col_remeasured_concentration_library,
                row_idx,
                col_dilution_factor,
                row_idx,
            )
            row.append(Formula(formula))

            # Mean Fragment Size
            row.append(mean_fragment_size)

            # Library Concentration C1 (nM)
            col_mean_fragment_size = column_letters_pooling[4]
            formula = "{}{}/({}{}*650)*1000000".format(
                col_adjusted_concentration_library,
                row_idx,
                col_mean_fragment_size,
                row_idx,
            )
            row.append(Formula(formula))

            # Sequencing Depth
            row.append(record.sequencing_depth)

            # % Library in Pool
            col_sequencing_depth = column_letters_pooling[6]
            formula = f"{col_sequencing_depth}{row_idx}/$B$3*100"
            row.append(Formula(formula))

            row.append("")  # Concentration C2

            # Volume to Pool
            col_percentage = column_letters_pooling[7]
            formula = f"$B$2*{col_percentage}{row_idx}/100"
            row.append(Formula(formula))

            # µl Library
            col_volume_pool = column_letters_pooling[9]
            col_normalization_c2 = column_letters_pooling[8]
            col_concentration_c1 = column_letters_pooling[5]
            formula = "({}{}*{}{})/{}{}".format(
                col_volume_pool,
                row_idx,
                col_normalization_c2,
                row_idx,
                col_concentration_c1,
                row_idx,
            )
            row.append(Formula(formula))

            # µl EB
            col_ul_library = column_letters_pooling[10]
            formula = "{}{}-{}{}".format(
                col_volume_pool,
                row_idx,
                col_ul_library,
                row_idx,
            )
            row.append(Formula(formula))

            # Writing row data to the sheet
            for i in range(len(row)):
                ws.write(row_num, i, row[i], font_style)

        # Write Sum µl EB
        lib_index = 0
        col_ul_eb = column_letters_pooling[11]
        formula = f"SUM({col_ul_eb}{6}:{col_ul_eb}{row_idx})"
        ws.write(int(row_idx), 11, Formula(formula), font_style)

        # Write Sum Sequencing Depth
        formula = "SUM({}{}:{}{})".format(
            col_sequencing_depth,
            6,
            col_sequencing_depth,
            str(row_num + 1),
        )
        ws.write(2, 1, Formula(formula), font_style)

        # Third sheet
        ws = wb.add_sheet("ng-ul to nM")
        ws.write(0, 0, "Convert ng/µl to nM", font_style_bold)  # A1
        ws.write(
            2,
            0,  # A3
            "Concentration in nM = ((concentration ng/µl) / (650 "
            + "g/mol x average library size bp)) x 10^6",
            font_style_bold,
        )

        # Table 1
        ws.write(6, 0, "Date", font_style_bold)  # A7
        ws.write(6, 1, "Operator", font_style_bold)  # B7
        ws.write(6, 2, "Sample ID", font_style_bold)  # C7
        ws.write(6, 3, "Concentration (ng/µl)", font_style_bold)  # D7
        ws.write(6, 4, "Smear Analysis (% Total)", font_style_bold)  # E7
        ws.write(6, 5, "Adjusted Concentration (ng/µl)", font_style_bold)  # F7
        ws.write(6, 6, "Average bp", font_style_bold)  # G7
        ws.write(6, 7, "nM", font_style_bold)  # H7

        for i in range(40):
            row_idx = 7 + i
            for j in range(5):
                ws.write(row_idx, j, "", font_style)
            formula = f"D{row_idx + 1}/(650*E{row_idx + 1})*10^6"
            ws.write(row_idx, j + 1, Formula(formula), font_style)

        # Table 2
        ws.write(5, 9, "Add V2 to samples, to reach desired C2", font_style)
        ws.write(6, 9, "V1", font_style_bold)  # J7
        ws.write(6, 10, "C1", font_style_bold)  # K7
        ws.write(6, 11, "V2", font_style_bold)  # L7
        ws.write(6, 12, "C2", font_style_bold)  # M7

        for i in range(8):
            row_idx = 7 + i
            ws.write(row_idx, 9, "", font_style)  # V1
            formula_c1 = f"F{9 + i}"
            ws.write(row_idx, 10, Formula(formula_c1), font_style)  # C1
            v2_idx = row_idx + 1
            formula_v2 = f"((I{v2_idx}*J{v2_idx})/L{v2_idx})-I{v2_idx}"
            ws.write(row_idx, 11, Formula(formula_v2), font_style)  # V2
            ws.write(row_idx, 12, 4 + i, font_style)  # C2

        wb.save(response)
        return response

    @action(
        methods=["post"],
        detail=False,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def download_pooling_template(self, request):
        """Generate Pooling Template as XLS file for selected records."""
        response = HttpResponse(content_type="application/ms-excel")
        libraries = json.loads(request.data.get("libraries", "[]"))
        samples = json.loads(request.data.get("samples", "[]"))

        records = list(
            itertools.chain(
                Library.objects.filter(pk__in=libraries),
                Sample.objects.filter(pk__in=samples),
            )
        )
        records = sorted(records, key=lambda x: x.barcode[3:])

        f_name = "QC_Normalization_and_Pooling_Template.xls"
        response["Content-Disposition"] = 'attachment; filename="%s"' % f_name

        wb = Workbook(encoding="utf-8")
        ws = wb.add_sheet("QC Normalization and Pooling")
        col_letters = {
            0: "A",  # Library
            1: "B",  # Barcode
            2: "C",  # ng/µl
            3: "D",  # bp
            4: "E",  # nM
            5: "F",  # Date
            6: "G",  # Comments
        }

        header = ["Library", "Barcode", "ng/µl", "bp", "nM", "Date", "Comments"]
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
                mean_fragment_size = record.librarypreparation.mean_fragment_size

            row = [
                record.name,  # Library
                record.barcode,  # Barcode
                concentration,  # ng/µl
                mean_fragment_size,  # bp
            ]

            # nM = Library Concentration / ( Mean Fragment Size * 650 ) * 10^6
            col_concentration = col_letters[2]
            col_mean_fragment_size = col_letters[3]
            formula = "{}{}/({}{})*1000000".format(
                col_concentration, row_idx, col_mean_fragment_size, row_idx
            )
            row.append(Formula(formula))

            row.extend(
                [
                    time.strftime("%d.%m.%Y"),  # Date
                    record.comments,  # Comments
                ]
            )

            for i in range(2):
                ws.write(row_num, i, row[i], font_style)

        wb.save(response)
        return response

    def _get_post_data(self, request):
        post_data = {}
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            post_data = request.data.get("data", {})
            if isinstance(post_data, str):
                post_data = json.loads(post_data)
        else:
            post_data = json.loads(request.data.get("data", "{}"))
        return post_data
