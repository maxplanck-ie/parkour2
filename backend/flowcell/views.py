import csv
import itertools
import json
import logging
import unicodedata

from common.mixins import MultiEditMixin
from common.views import CsrfExemptSessionAuthentication
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.db.models import F, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from xlwt import Workbook, XFStyle

from .models import Flowcell, Lane, Sequencer
from .serializers import (
    FlowcellListSerializer,
    FlowcellSerializer,
    LaneSerializer,
    PoolInfoSerializer,
    PoolListSerializer,
    SequencerSerializer,
)

ReadLength = apps.get_model("library_sample_shared", "ReadLength")
IndexI7 = apps.get_model("library_sample_shared", "IndexI7")
IndexI5 = apps.get_model("library_sample_shared", "IndexI5")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
Pool = apps.get_model("index_generator", "Pool")

logger = logging.getLogger("db")


# def indices_present(libraries, samples):
#     count_total = libraries.count() + samples.count()
#     index_i7_count = 0
#     index_i5_count = 0
#     equal_representation_count = 0

#     for library in libraries:
#         if library.index_i7 != '':
#             index_i7_count += 1
#         if library.index_i5 != '':
#             index_i5_count += 1
#         if library.equal_representation_nucleotides:
#             equal_representation_count += 1

#     for sample in samples:
#         if sample.index_i7 != '':
#             index_i7_count += 1
#         if sample.index_i5 != '':
#             index_i5_count += 1
#         if sample.equal_representation_nucleotides:
#             equal_representation_count += 1

#     # If at least one Index I7/I5 is set
#     index_i7_show = 'Yes' if index_i7_count > 0 else 'No'
#     index_i5_show = 'Yes' if index_i5_count > 0 else 'No'

#     # If all Equal Representation are set
#     equal_representation = 'Yes' \
#         if equal_representation_count == count_total else 'No'

#     return index_i7_show, index_i5_show, equal_representation


class SequencerViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of sequencers."""

    queryset = Sequencer.objects.all().filter(archived=False)
    serializer_class = SequencerSerializer


class PoolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pool.objects.all().filter(archived=False)
    serializer_class = PoolInfoSerializer
    permission_classes = [IsAdminUser]

    def retrieve(self, request, pk=None):
        """Get libraries and samples for a pool with a given id."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data["records"])


class FlowcellViewSet(MultiEditMixin, viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = LaneSerializer

    def get_queryset(self):
        libraries_qs = (
            Library.objects.filter(~Q(status=-1))
            .select_related("read_length", "index_type")
            .only("read_length", "index_type", "equal_representation_nucleotides")
        )

        samples_qs = (
            Sample.objects.filter(~Q(status=-1))
            .select_related("read_length", "index_type")
            .only("read_length", "index_type", "equal_representation_nucleotides")
        )

        lanes_qs = (
            Lane.objects.filter(completed=False)
            .select_related(
                "pool",
            )
            .prefetch_related(
                Prefetch("pool__libraries", queryset=libraries_qs),
                Prefetch("pool__samples", queryset=samples_qs),
            )
            .order_by("name")
        )

        queryset = (
            Flowcell.objects.select_related(
                "sequencer",
            )
            .filter(archived=False)
            .prefetch_related(
                Prefetch("lanes", queryset=lanes_qs),
            )
            .order_by("-create_time")
        )

        return queryset

    def list(self, request, *args, **kwargs):
        today = timezone.datetime.today()

        default_start_date = today - relativedelta(years=1)
        default_end_date = (
            today.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
        )

        start_date_param = request.query_params.get(
            "start", default_start_date.strftime("%d.%m.%Y")
        )
        end_date_param = request.query_params.get(
            "end", default_end_date.strftime("%d.%m.%Y")
        )

        start_date = timezone.datetime.strptime(start_date_param, "%d.%m.%Y")
        end_date = timezone.datetime.strptime(end_date_param, "%d.%m.%Y")

        queryset = self.get_queryset().filter(
            create_time__gte=start_date, create_time__lte=end_date
        )

        serializer = FlowcellListSerializer(queryset, many=True)
        data = list(itertools.chain(*serializer.data))
        return Response(data)

    def create(self, request):
        """Add a flowcell."""

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            post_data = request.data.get("data", [])
            if isinstance(post_data, str):
                post_data = json.loads(post_data)
        else:
            post_data = json.loads(request.data.get("data", "[]"))

        if not post_data:
            return Response(
                {
                    "success": False,
                    "message": "Invalid payload.",
                },
                400,
            )

        serializer = FlowcellSerializer(data=post_data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True}, 201)

        else:
            return Response(
                {
                    "success": False,
                    "message": "Invalid payload.",
                    "errors": serializer.errors,
                },
                400,
            )

    @action(methods=["get"], detail=False)
    def pool_list(self, request):
        data = []

        # Libraries which have reached the Pooling step
        libraries_qs = (
            Library.objects.filter(status__gte=2)
            .select_related("read_length")
            .only("status", "read_length")
        )

        # Samples which have reached the Pooling step
        samples_qs = (
            Sample.objects.filter(status__gte=3)
            .select_related("read_length")
            .only("status", "read_length")
        )

        queryset = (
            Pool.objects.select_related("size")
            .prefetch_related(
                Prefetch("libraries", queryset=libraries_qs),
                Prefetch("samples", queryset=samples_qs),
            )
            .filter(archived=False, size__multiplier__gt=F("loaded"))
            .order_by("pk")
        )

        serializer = PoolListSerializer(queryset, many=True)
        data = [x for x in serializer.data if x != {}]
        data = sorted(data, key=lambda x: x["ready"], reverse=True)

        return Response(data)

    @action(
        methods=["post"],
        detail=False,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def download_benchtop_protocol(self, request):
        """Generate Benchtop Protocol as XLS file for selected lanes."""
        ids = json.loads(request.data.get("ids", "[]"))

        filename = "FC_Loading_Benchtop_Protocol.xls"
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(lanes__pk__in=ids)
            .distinct()
        )

        serializer = FlowcellListSerializer(queryset, many=True)
        data = list(itertools.chain(*serializer.data))

        font_style = XFStyle()
        font_style.alignment.wrap = 1
        font_style_bold = XFStyle()
        font_style_bold.font.bold = True

        wb = Workbook(encoding="utf-8")
        ws = wb.add_sheet("FC_Loading_Benchtop_Protocol")

        header = [
            "Pool ID",
            "Flowcell ID",
            "Sequencer",
            "Lane",
            "Request",
            "I7 present",
            "I5 present",
            #'Equal Representation of Nucleotides',
            "Library protocol",
            "Read Length",
            "Loading Concentration",
            "PhiX %",
        ]

        row_num = 0

        for i, column in enumerate(header):
            ws.write(row_num, i, column, font_style_bold)
            ws.col(i).width = 8000

        for item in data:
            row_num += 1

            row = [
                item["pool_name"],
                item["flowcell_id"],
                item["sequencer_name"],
                item["name"],
                item["request"],
                item["index_i7_show"],
                item["index_i5_show"],
                # item['equal_representation'],
                item["protocol"],
                item["read_length_name"],
                item["loading_concentration"],
                item["phix"],
            ]

            for i in range(len(row)):
                ws.write(row_num, i, row[i], font_style)

        wb.save(response)

        return response

    @action(
        methods=["post"],
        detail=False,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def download_sample_sheet(self, request):
        """Generate Benchtop Protocol as XLS file for selected lanes."""

        def create_row(lane, record):
            index_i7 = IndexI7.objects.filter(
                archived=False, index=record.index_i7, index_type=record.index_type
            )
            index_i7_id = index_i7[0].index_id if index_i7 else ""

            index_i5 = IndexI5.objects.filter(
                archived=False, index=record.index_i5, index_type=record.index_type
            )
            index_i5_id = index_i5[0].index_id if index_i5 else ""

            request_name = unicodedata.normalize("NFKD", record.request.get().name)
            request_name = str(request_name.encode("ASCII", "ignore"), "utf-8")

            library_protocol = unicodedata.normalize(
                "NFKD", record.library_protocol.name
            )
            library_protocol = str(library_protocol.encode("ASCII", "ignore"), "utf-8")

            return [
                lane.name.split()[1],  # Lane
                record.barcode,  # Sample_ID
                record.name,  # Sample_Name
                "",  # Sample_Plate
                "",  # Sample_Well
                index_i7_id,  # I7_Index_ID
                record.index_i7,  # index
                index_i5_id,  # I5_Index_ID
                record.index_i5,  # index2
                request_name,  # Sample_Project / Request ID
                library_protocol,  # Description / Library Protocol
            ]

        response = HttpResponse(content_type="text/csv")
        ids = json.loads(request.data.get("ids", "[]"))
        flowcell_id = request.data.get("flowcell_id", "")

        writer = csv.writer(response)

        #        writer.writerow(['[Header]'] + [''] * 10)
        #        writer.writerow(['IEMFileVersion', '4'] + [''] * 9)
        #        writer.writerow(['Date', '11/3/2016'] + [''] * 9)
        #        writer.writerow(['Workflow', 'GenerateFASTQ'] + [''] * 9)
        #        writer.writerow(['Application', 'HiSeq FASTQ Only'] + ['' * 9])
        #        writer.writerow(['Assay', 'Nextera XT'] + [''] * 9)
        #        writer.writerow(['Description'] + [''] * 10)
        #        writer.writerow(['Chemistry', 'Amplicon'] + [''] * 9)
        #        writer.writerow([''] * 11)
        #        writer.writerow(['[Reads]'] + [''] * 10)
        #        writer.writerow(['75'] + [''] * 10)
        #        writer.writerow(['75'] + [''] * 10)
        #        writer.writerow([''] * 11)
        #        writer.writerow(['[Settings]'] + [''] * 10)
        #        writer.writerow(['ReverseComplement', '0'] + [''] * 9)
        #        writer.writerow(['Adapter', 'CTGTCTCTTATACACATCT'] + [''] * 9)
        #        writer.writerow([''] * 11)
        writer.writerow(["[Data]"] + [""] * 10)

        writer.writerow(
            [
                "Lane",
                "Sample_ID",
                "Sample_Name",
                "Sample_Plate",
                "Sample_Well",
                "I7_Index_ID",
                "index",
                "I5_Index_ID",
                "index2",
                "Sample_Project",
                "Description",
            ]
        )

        flowcell = Flowcell.objects.filter(archived=False).get(pk=flowcell_id)
        f_name = "%s_SampleSheet.csv" % flowcell.flowcell_id
        response["Content-Disposition"] = 'attachment; filename="%s"' % f_name

        lanes = Lane.objects.filter(pk__in=ids).order_by("name")

        rows = []
        for lane in lanes:
            records = list(
                itertools.chain(
                    lane.pool.libraries.all().filter(~Q(status=-1)),
                    lane.pool.samples.all().filter(~Q(status=-1)),
                )
            )

            for record in records:
                row = create_row(lane, record)
                rows.append(row)

        rows = sorted(rows, key=lambda x: (x[0], x[1][3:]))
        for row in rows:
            writer.writerow(row)

        return response


class FlowcellAnalysisViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(methods=["get"], detail=False)
    def analysis_list(self, request):
        """
        This returns a dictionary of the information required to run an automated
        analysis on the flow cell's contents
        The keys of the dictionary are projects. The values are then a dictionary
        dictionaries with library name keys and tuple values of (sample/library
        name, library type, library protocol type, organism).
        """
        flowcell_id = request.query_params.get("flowcell_id", "")
        flowcell = get_object_or_404(Flowcell, flowcell_id=flowcell_id)

        # Iterate over requests
        requests = dict()
        for request in flowcell.requests.all():
            rname = request.name
            requests[rname] = dict()
            records = list(
                itertools.chain(request.libraries.all(), request.samples.all())
            )
            for item in records:
                #               quick fix to deal with undefined index_type
                #               this can happen for failed samples
                if item.index_type is not None:
                    ind_type = item.index_type.name
                else:
                    ind_type = "NA"

                requests[rname][item.barcode] = [
                    item.name,
                    item.library_type.name,
                    item.library_protocol.name,
                    item.organism.name,
                    ind_type,
                    item.sequencing_depth,
                ]

        return Response(requests)
