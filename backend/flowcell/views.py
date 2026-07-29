import csv
import itertools
import json
import logging
import unicodedata

from common.mixins import MultiEditMixin
from common.views import CsrfExemptSessionAuthentication
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.apps import apps
from django.db import transaction
from django.db.models import F, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
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
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
Pool = apps.get_model("index_generator", "Pool")
IndexI7 = apps.get_model("library_sample_shared", "IndexI7")
IndexI5 = apps.get_model("library_sample_shared", "IndexI5")

DELIVERED_STATUS = 6

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
        today = timezone.localtime()

        default_start_date = today - relativedelta(months=0)
        default_end_date = today

        start_date_param = self.request.query_params.get(
            "start", default_start_date.strftime("%Y-%m")
        )
        end_date_param = self.request.query_params.get(
            "end", default_end_date.strftime("%Y-%m")
        )

        start_date = datetime.strptime(start_date_param, "%Y-%m").replace(day=1)
        end_date = datetime.strptime(end_date_param, "%Y-%m").replace(day=1)
        end_date = end_date + relativedelta(months=1, seconds=-1)

        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date)
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date)

        libraries_qs = (
            Library.objects.filter(~Q(status=-1))
            .prefetch_related("read_length", "index_type")
            .only("read_length", "index_type")
        )

        samples_qs = (
            Sample.objects.filter(~Q(status=-1))
            .prefetch_related("read_length", "index_type")
            .only("read_length", "index_type")
        )

        lanes_qs = (
            Lane.objects.filter(completed=False)
            .prefetch_related(
                "pool",
                Prefetch("pool__libraries", queryset=libraries_qs),
                Prefetch("pool__samples", queryset=samples_qs),
            )
            .order_by("name")
        )

        queryset = (
            Flowcell.objects.filter(
                create_time__gte=start_date, create_time__lte=end_date, archived=False
            )
            .prefetch_related(
                "sequencer",
                Prefetch("lanes", queryset=lanes_qs),
            )
            .order_by("-create_time")
        )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

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
            response_data = {"success": True}
            pool_warnings = getattr(serializer, "pool_warnings", [])
            if pool_warnings:
                response_data["warnings"] = pool_warnings
            return Response(response_data, 201)

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
            .prefetch_related("read_length")
            .only("status", "read_length")
        )

        # Samples which have reached the Pooling step
        samples_qs = (
            Sample.objects.filter(status__gte=3)
            .prefetch_related("read_length")
            .only("status", "read_length")
        )

        queryset = (
            Pool.objects.prefetch_related(
                "size",
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

    @action(methods=["post"], detail=True)
    def destroy_flowcell(self, request, pk=None):
        flowcell = get_object_or_404(
            Flowcell.objects.prefetch_related(
                "lanes__pool__size",
                "lanes__pool__libraries",
                "lanes__pool__samples",
                "requests",
            ).filter(archived=False),
            pk=pk,
        )

        flowcell_pool_ids = list(
            flowcell.lanes.exclude(pool_id=None)
            .values_list("pool_id", flat=True)
            .distinct()
        )
        has_delivered_records = (
            Library.objects.filter(
                status=DELIVERED_STATUS,
                pool__id__in=flowcell_pool_ids,
            ).exists()
            or Sample.objects.filter(
                status=DELIVERED_STATUS,
                pool__id__in=flowcell_pool_ids,
            ).exists()
        )
        if has_delivered_records:
            return Response(
                {
                    "success": False,
                    "message": "This flowcell cannot be destroyed because it contains delivered libraries or samples.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            affected_pools = {}
            pool_unload_counts = {}
            requests_to_update = list(flowcell.requests.all())
            lanes = list(flowcell.lanes.select_related("pool", "pool__size").all())

            for lane in lanes:
                pool = lane.pool
                if pool:
                    affected_pools[pool.pk] = pool
                    pool_unload_counts[pool.pk] = pool_unload_counts.get(pool.pk, 0) + 1

                flowcell.lanes.remove(lane)
                lane.delete()

            for pool_pk, pool in affected_pools.items():
                unload_count = pool_unload_counts.get(pool_pk, 0)
                if unload_count:
                    pool.loaded = max(0, pool.loaded - unload_count)
                    pool.save(update_fields=["loaded"])

            for pool in affected_pools.values():
                pool_size = pool.size.multiplier if pool.size else None
                if pool_size is None or pool.loaded < pool_size:
                    pool.libraries.all().filter(status=5).update(status=4)
                    pool.samples.all().filter(status=5).update(status=4)

            for req in requests_to_update:
                has_other_flowcells = (
                    req.flowcell.filter(archived=False).exclude(pk=flowcell.pk).exists()
                )
                if not has_other_flowcells:
                    req.sequenced = False
                    req.flowcell_loaded_at = None
                    req.save(update_fields=["sequenced", "flowcell_loaded_at"])

            flowcell.delete()

        return Response({"success": True})

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
        """Generate SampleSheet as CSV file for selected lanes."""

        def create_row(lane, record, monolane, legacy=False):
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

            if not monolane:
                lane_name = lane.name.split()[1]
            else:
                lane_name = "1+2"

            if legacy:
                this_row = [
                    lane_name,  # Lane
                    record.barcode,  # Sample_ID
                    record.name,  # Sample_Name
                    "",  # Sample_Plate
                    "",  # Sample_Well
                    index_i7_id,  # I7_Index_ID
                    record.index_i7,  # index1
                    index_i5_id,  # I5_Index_ID
                    record.index_i5,  # index2
                    request_name,  # Sample_Project / Request ID
                    library_protocol,  # Description / Library Protocol
                ]
            else:
                i5 = (
                    record.index_i5.replace("A", "t")
                    .replace("C", "g")
                    .replace("T", "a")
                    .replace("G", "c")
                    .upper()[::-1]
                )
                this_row = [
                    record.barcode,  # Sample_ID, calling it 'Name' in RunManifest header
                    record.index_i7,  # index1
                    i5,  # index2 (reverse complement)
                    lane_name,  # Lane
                    request_name,  # Sample_Project / Request ID
                ]
            return this_row

        response = HttpResponse(content_type="text/csv")
        ids = json.loads(request.data.get("ids", "[]"))
        flowcell_id = request.data.get("flowcell_id", "")
        flowcell = Flowcell.objects.filter(archived=False).get(pk=flowcell_id)

        writer = csv.writer(response)

        if not "AVITI" in flowcell.sequencer.name:
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
            f_name = "%s_SampleSheet.csv" % flowcell.flowcell_id

        else:
            writer.writerow(["[SAMPLES]"] + [""] * 4)
            writer.writerow(
                [
                    "SampleName",
                    "Index1",
                    "Index2",
                    "Lane",
                    "Project",
                ]
            )
            f_name = "%s_RunManifest.csv" % flowcell.flowcell_id

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
                row = create_row(
                    lane,
                    record,
                    monolane=len(lanes) == 1,
                    legacy=not "AVITI" in flowcell.sequencer.name,
                )
                rows.append(row)

        if not "AVITI" in flowcell.sequencer.name:
            rows = sorted(rows, key=lambda x: (x[0], x[1][3:]))
        else:
            rows = sorted(rows, key=lambda x: x[0])

        for row in rows:
            writer.writerow(row)

        return response

    @action(methods=["get"], detail=False, permission_classes=[IsAdminUser])
    def retrieve_samplesheet(self, request):
        """Download SampleSheet for all lanes of a flowcell."""
        flowcell_id = request.query_params.get("flowcell_id", "")
        flowcell = get_object_or_404(Flowcell, flowcell_id=flowcell_id)
        lane_pks_list = list(flowcell.lanes.all().values_list("pk", flat=True))
        post_request = type("MockRequest", (), {})()
        post_request.data = {
            "ids": json.dumps(lane_pks_list),
            "flowcell_id": flowcell.pk,
        }
        return self.download_sample_sheet(post_request)

    @action(methods=["get"], detail=False, permission_classes=[IsAdminUser])
    def get_related_flowcells(self, request):
        """
        Get information about where each sample/library from requests is sequenced,
        organized by request.
        """
        flowcell_id = request.query_params.get("flowcell_id", "")
        original_flowcell = get_object_or_404(Flowcell, flowcell_id=flowcell_id)

        # Get all requests associated with this flowcell
        requests_on_flowcell = original_flowcell.requests.all()

        # Find all related flowcells (including the original)
        all_related_flowcells = (
            Flowcell.objects.filter(
                Q(lanes__pool__libraries__request__in=requests_on_flowcell)
                | Q(lanes__pool__samples__request__in=requests_on_flowcell)
            )
            .distinct()
            .prefetch_related(
                "lanes__pool__libraries__request",
                "lanes__pool__samples__request",
                "sequencer",
            )
        )

        # Prepare the response data - organized by request
        result = {"original_flowcell": flowcell_id, "requests": {}}

        # Initialize the request structure for all requests from original flowcell
        for req in requests_on_flowcell:
            result["requests"][req.name] = {"samples": {}, "libraries": {}}

        def process_records(records, record_type, flowcell_id, lane, sequencer_name):
            """
            Helper function to process libraries or samples

            Args:
                records: QuerySet of libraries or samples
                record_type: 'libraries' or 'samples'
                flowcell_id: ID of the current flowcell
                lane: The current lane
                sequencer_name: Name of the sequencer
            """
            for record in records:
                if hasattr(record, "request"):
                    record_requests = record.request.all()
                    for record_request in record_requests:
                        # Only include if it's from the original flowcell's requests
                        if record_request in requests_on_flowcell:
                            req_name = record_request.name
                            barcode = record.barcode

                            # Add record to the request structure if not already there
                            if barcode not in result["requests"][req_name][record_type]:
                                result["requests"][req_name][record_type][barcode] = {
                                    "name": record.name,
                                    "locations": [],
                                }

                            # Add this flowcell/lane location
                            result["requests"][req_name][record_type][barcode][
                                "locations"
                            ].append(
                                {
                                    "flowcell": flowcell_id,
                                    "lane": lane.name,
                                    "sequencer": sequencer_name,
                                }
                            )

        # Process each flowcell
        for flowcell in all_related_flowcells:
            fc_id = flowcell.flowcell_id
            sequencer_name = (
                flowcell.sequencer.name if flowcell.sequencer else "Unknown"
            )

            # Process each lane
            for lane in flowcell.lanes.all():
                if lane.pool:
                    # Process libraries in this pool
                    process_records(
                        lane.pool.libraries.all(),
                        "libraries",
                        fc_id,
                        lane,
                        sequencer_name,
                    )

                    # Process samples in this pool
                    process_records(
                        lane.pool.samples.all(), "samples", fc_id, lane, sequencer_name
                    )

        return Response(result)


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
                    [
                        item.organism.name,
                        item.organism.label,
                        item.organism.yaml,
                    ],
                    ind_type,
                    item.sequencing_depth,
                ]

        return Response(requests)
