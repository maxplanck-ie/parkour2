from collections import defaultdict
from datetime import datetime
from functools import reduce
from itertools import chain
from operator import or_

from django.apps import apps
from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response

from request.models import Request
from request.serializers import RequestSerializer

from library_sample_shared.views import LibrarySampleBaseViewSet

from .serializers import LibrarySerializer
from .utils import get_accessible_requests

CompleteLibraryData = apps.get_model("library", "CompleteLibraryData")
CompleteSampleData = apps.get_model("sample", "CompleteSampleData")

FACILITY_INPUT_FIELDS = (
    "measured_value_facility",
    "measuring_unit_facility",
)
SAMPLE_PREPARATION_FIELDS = (
    "starting_amount",
    "pcr_cycles",
    "concentration_library",
    "average_fragment_size",
)
LIBRARY_MEASURE_FIELDS = ("concentration_library", "average_fragment_size")
SAMPLE_ONLY_FIELDS = ("starting_amount", "pcr_cycles")
SEQUENCING_FIELDS = ("flowcell_ids", "sequencer_ids", "sequencer_names")

POST_INCOMING_STATUSES = (-2, -1, 2, 3, 4, 5, 6)
POST_PREPARATION_STATUSES = (-1, 3, 4, 5, 6)
SEQUENCING_STATUSES = (5, 6)


def apply_stage_data_visibility(record, record_type):
    """Mask values until their workflow stage has completed."""
    try:
        status_value = int(record.get("status"))
    except (TypeError, ValueError):
        return record

    is_sample = record_type == "Sample"

    if status_value not in POST_INCOMING_STATUSES:
        for field in FACILITY_INPUT_FIELDS:
            if field in record:
                record[field] = None

    if is_sample:
        if status_value not in POST_PREPARATION_STATUSES:
            for field in SAMPLE_PREPARATION_FIELDS:
                if field in record:
                    record[field] = None
    else:
        for field in SAMPLE_ONLY_FIELDS:
            if field in record:
                record[field] = None
        if status_value not in POST_INCOMING_STATUSES:
            for field in LIBRARY_MEASURE_FIELDS:
                if field in record:
                    record[field] = None

    if status_value not in SEQUENCING_STATUSES:
        for field in SEQUENCING_FIELDS:
            if field in record:
                record[field] = None

    return record


def build_search_term_query(term):
    """Build a text-search query without exposing pre-sequencing flowcells."""
    search_fields = [
        "name__icontains",
        "comment_input__icontains",
        "organism_name__icontains",
        "barcode__icontains",
        "request_name__icontains",
        "pool_names__icontains",
        "index_type_name__icontains",
    ]
    field_queries = [Q(**{field: term}) for field in search_fields]
    field_queries.append(
        Q(status__in=SEQUENCING_STATUSES, flowcell_ids__icontains=term)
    )
    return reduce(or_, field_queries)


def filter_by_sequencer(queryset, sequencer_id):
    """Restrict sequencer filtering to records that reached sequencing."""
    return queryset.filter(
        status__in=SEQUENCING_STATUSES,
        sequencer_ids__contains=[sequencer_id],
    )


class LibrarySampleTree(viewsets.ViewSet):
    def list(self, request):
        search_string = request.GET.get("search")
        status_filter = request.GET.get("status")
        library_protocol_filter = request.GET.get("library_protocol")
        analysis_type_filter = request.GET.get("analysis_type")
        sequencer_filter = request.GET.get("sequencer")
        read_length_filter = request.GET.get("read_length")
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
        page = int(request.GET.get("page", 1))
        page_size_param = request.GET.get("size")
        page_size = int(page_size_param) if page_size_param else None

        library_queryset = CompleteLibraryData.objects.all()
        sample_queryset = CompleteSampleData.objects.all()

        accessible_requests = get_accessible_requests(request)
        accessible_request_ids = accessible_requests.values_list("id", flat=True)
        library_queryset = library_queryset.filter(
            request_id__in=accessible_request_ids
        )
        sample_queryset = sample_queryset.filter(request_id__in=accessible_request_ids)

        if start_date_str and end_date_str:
            try:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date_str, "%d.%m.%Y")
                )
                end_date = timezone.make_aware(
                    datetime.strptime(end_date_str, "%d.%m.%Y")
                )
                end_date = end_date.replace(hour=23, minute=59, second=59)
                library_queryset = library_queryset.filter(
                    create_time__range=(start_date, end_date)
                )
                sample_queryset = sample_queryset.filter(
                    create_time__range=(start_date, end_date)
                )
            except ValueError:
                return Response(
                    {"success": False, "error": "Invalid date format. Use DD.MM.YYYY"},
                    status=400,
                )

        if search_string:
            or_groups = [grp.strip() for grp in search_string.split(";") if grp.strip()]
            all_or_q = []

            for group in or_groups:
                terms = [term.strip() for term in group.split(",") if term.strip()]
                and_qs = []
                for term in terms:
                    and_qs.append(build_search_term_query(term))

                if and_qs:
                    combined_and_group = reduce(lambda a, b: a & b, and_qs)
                    all_or_q.append(combined_and_group)

            if all_or_q:
                final_search = reduce(or_, all_or_q)
                library_queryset = library_queryset.filter(final_search)
                sample_queryset = sample_queryset.filter(final_search)

        if status_filter:
            library_queryset = library_queryset.filter(status=int(status_filter))
            sample_queryset = sample_queryset.filter(status=int(status_filter))

        if library_protocol_filter:
            library_queryset = library_queryset.filter(
                library_protocol_id=int(library_protocol_filter)
            )
            sample_queryset = sample_queryset.filter(
                library_protocol_id=int(library_protocol_filter)
            )

        if analysis_type_filter:
            library_queryset = library_queryset.filter(
                analysis_type_id=int(analysis_type_filter)
            )
            sample_queryset = sample_queryset.filter(
                analysis_type_id=int(analysis_type_filter)
            )

        if sequencer_filter:
            seq_id = int(sequencer_filter)
            library_queryset = filter_by_sequencer(library_queryset, seq_id)
            sample_queryset = filter_by_sequencer(sample_queryset, seq_id)

        changed_ownership_filter = request.GET.get("changed_ownership")

        if read_length_filter:
            library_queryset = library_queryset.filter(
                read_length_id=int(read_length_filter)
            )
            sample_queryset = sample_queryset.filter(
                read_length_id=int(read_length_filter)
            )

        if changed_ownership_filter in ("true", "false"):
            changed_ids = (
                Request.history.values("id")
                .annotate(user_count=Count("user", distinct=True))
                .filter(user_count__gt=1)
                .values_list("id", flat=True)
            )
            if changed_ownership_filter == "true":
                library_queryset = library_queryset.filter(request_id__in=changed_ids)
                sample_queryset = sample_queryset.filter(request_id__in=changed_ids)
            else:
                library_queryset = library_queryset.exclude(request_id__in=changed_ids)
                sample_queryset = sample_queryset.exclude(request_id__in=changed_ids)

        library_requests = (
            library_queryset.values("request_name")
            .annotate(latest_time=Max("create_time"))
            .values_list("request_name", "latest_time")
        )

        sample_requests = (
            sample_queryset.values("request_name")
            .annotate(latest_time=Max("create_time"))
            .values_list("request_name", "latest_time")
        )

        request_time_map = defaultdict(lambda: timezone.make_aware(datetime.min))
        for request_name, latest_time in chain(library_requests, sample_requests):
            if latest_time > request_time_map[request_name]:
                request_time_map[request_name] = latest_time

        sorted_requests = sorted(
            request_time_map.items(), key=lambda x: x[1], reverse=True
        )
        request_names = [req for req, _ in sorted_requests]

        total_requests = len(request_names)

        if page_size:
            total_pages = (total_requests + page_size - 1) // page_size
            offset = (page - 1) * page_size
            paginated_requests = request_names[offset : offset + page_size]
        else:
            total_pages = 1
            paginated_requests = request_names

        libraries = (
            library_queryset.filter(request_name__in=paginated_requests)
            .order_by("-create_time")
            .values()
        )
        samples = (
            sample_queryset.filter(request_name__in=paginated_requests)
            .order_by("-create_time")
            .values()
        )

        combined_data = []
        for lib in libraries:
            apply_stage_data_visibility(lib, "Library")
            lib["record_type"] = "Library"
            combined_data.append(lib)

        for sample in samples:
            apply_stage_data_visibility(sample, "Sample")
            sample["record_type"] = "Sample"
            combined_data.append(sample)

        combined_data.sort(key=lambda x: x["create_time"], reverse=True)

        request_ids = {
            record.get("request_id")
            for record in combined_data
            if record.get("request_id") is not None
        }
        requests_meta = {}
        if request_ids:
            requests_qs = (
                Request.objects.filter(id__in=request_ids)
                .select_related("user", "cost_unit", "user__pi")
                .prefetch_related("files", "libraries", "samples")
            )
            serialized = RequestSerializer(requests_qs, many=True).data
            requests_meta = {item["pk"]: item for item in serialized}

        return Response(
            {
                "success": True,
                "total": total_requests,
                "page": page if page_size else 1,
                "page_size": page_size if page_size else total_requests,
                "total_pages": total_pages,
                "children": combined_data,
                "requests": requests_meta,
            }
        )


class LibraryViewSet(LibrarySampleBaseViewSet):
    serializer_class = LibrarySerializer
