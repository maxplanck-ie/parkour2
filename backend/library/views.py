import re
from collections import defaultdict
from datetime import datetime
from functools import reduce
from itertools import chain
from operator import or_

from django.apps import apps
from django.db.models import CharField, Count, Func, Max, Q, Value
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


INDEX_ID_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def parse_index_id(value):
    """Split an index ID like 'N701' into its ('N', 701) prefix/number parts."""
    match = INDEX_ID_RE.match(value)
    if not match:
        return None, None
    prefix, number = match.groups()
    return prefix, int(number)


class InvalidIndexRangeError(Exception):
    def __init__(self, field_label):
        self.field_label = field_label
        super().__init__(f"Invalid {field_label} range")


def build_index_id_filter(field, field_label, raw_value):
    """Build a Q object for an I7/I5 ID header-filter box, or None if empty.

    A single ID (e.g. "N701") is an exact match. Two IDs joined by "-"
    (e.g. "N701-N729") are a range: both must share a letter prefix and end
    in a number, so the range can be expanded into the literal IDs it covers
    (a plain string range would misorder IDs like RPI2..RPI10 lexically).
    Mismatched/unparsable prefixes raise InvalidIndexRangeError rather than
    silently returning a wrong subset.
    """
    value = (raw_value or "").strip()
    if not value:
        return None

    if "-" in value:
        from_val, _, to_val = value.partition("-")
        from_val = from_val.strip()
        to_val = to_val.strip()
        from_prefix, from_number = parse_index_id(from_val)
        to_prefix, to_number = parse_index_id(to_val)
        if from_prefix is None or to_prefix is None or from_prefix != to_prefix:
            raise InvalidIndexRangeError(field_label)
        lo, hi = sorted((from_number, to_number))
        candidates = [f"{from_prefix}{n}" for n in range(lo, hi + 1)]
        return Q(**{f"{field}__in": candidates})

    return Q(**{f"{field}__iexact": value})


def build_type_filter(raw_value):
    """S/L column: the record type lives in the 3rd character of the barcode."""
    value = (raw_value or "").strip()
    if not value:
        return None
    return Q(barcode__iregex=rf"^.{{2}}{re.escape(value)}")


def parse_status_filter(raw_value):
    """Parse a Status header-filter box value; None if empty/unparsable."""
    value = (raw_value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


GMO_TRUE_VALUES = {"y", "yes", "true", "1"}
GMO_FALSE_VALUES = {"n", "no", "false", "0"}


def parse_gmo_filter(raw_value):
    """Map a typed GMO header-filter value to True/False; None if unrecognized."""
    value = (raw_value or "").strip().lower()
    if value in GMO_TRUE_VALUES:
        return True
    if value in GMO_FALSE_VALUES:
        return False
    return None


class ToChar(Func):
    """Format a date/datetime column as text via Postgres' to_char()."""

    function = "to_char"
    output_field = CharField()


# Plain text columns filtered the same way (icontains) on both querysets.
SIMPLE_TEXT_FILTER_FIELDS = (
    "name",
    "barcode",
    "pool_names",
    "comment_input",
    "organism_name",
    "coordinate",
    "index_i7",
    "index_i5",
    "library_protocol_name",
    "analysis_type_name",
    "read_length_name",
)
# Only masked/exposed once a flowcell has reached sequencing (see
# apply_stage_data_visibility) -- gate the filter the same way the "search"
# box already does, so a filter can't reveal a pre-sequencing value.
SEQUENCING_GATED_TEXT_FILTER_FIELDS = ("flowcell_ids", "sequencer_names")


class LibrarySampleTree(viewsets.ViewSet):
    def list(self, request):
        search_string = request.GET.get("search")
        status_filter = request.GET.get("status")
        type_filter = request.GET.get("type")
        gmo_filter = request.GET.get("gmo")
        create_time_filter = request.GET.get("create_time")
        nucleic_acid_type_filter = request.GET.get("nucleic_acid_type_name")
        i7_id_filter = request.GET.get("i7_id")
        i5_id_filter = request.GET.get("i5_id")
        index_type_filter = request.GET.get("index_type")
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

        status_value = parse_status_filter(status_filter)
        if status_value is not None:
            library_queryset = library_queryset.filter(status=status_value)
            sample_queryset = sample_queryset.filter(status=status_value)

        type_q = build_type_filter(type_filter)
        if type_q is not None:
            library_queryset = library_queryset.filter(type_q)
            sample_queryset = sample_queryset.filter(type_q)

        if gmo_filter:
            gmo_value = parse_gmo_filter(gmo_filter)
            if gmo_value is not None:
                # gmo has no meaning for libraries (field doesn't exist on
                # CompleteLibraryData) -- exclude them rather than leaving
                # every library unfiltered while a GMO filter is active.
                library_queryset = library_queryset.none()
                sample_queryset = sample_queryset.filter(gmo=gmo_value)

        if nucleic_acid_type_filter:
            # Input Type likewise only exists on CompleteSampleData.
            library_queryset = library_queryset.none()
            sample_queryset = sample_queryset.filter(
                nucleic_acid_type_name__icontains=nucleic_acid_type_filter
            )

        if create_time_filter:
            library_queryset = library_queryset.annotate(
                create_time_display=ToChar("create_time", Value("DD.MM.YYYY"))
            ).filter(create_time_display__icontains=create_time_filter)
            sample_queryset = sample_queryset.annotate(
                create_time_display=ToChar("create_time", Value("DD.MM.YYYY"))
            ).filter(create_time_display__icontains=create_time_filter)

        for field in SIMPLE_TEXT_FILTER_FIELDS:
            value = request.GET.get(field)
            if value:
                library_queryset = library_queryset.filter(
                    **{f"{field}__icontains": value}
                )
                sample_queryset = sample_queryset.filter(
                    **{f"{field}__icontains": value}
                )

        for field in SEQUENCING_GATED_TEXT_FILTER_FIELDS:
            value = request.GET.get(field)
            if value:
                library_queryset = library_queryset.filter(
                    status__in=SEQUENCING_STATUSES, **{f"{field}__icontains": value}
                )
                sample_queryset = sample_queryset.filter(
                    status__in=SEQUENCING_STATUSES, **{f"{field}__icontains": value}
                )

        try:
            i7_id_q = build_index_id_filter("i7_id", "I7 ID", i7_id_filter)
            i5_id_q = build_index_id_filter("i5_id", "I5 ID", i5_id_filter)
        except InvalidIndexRangeError as exc:
            return Response(
                {
                    "success": False,
                    "error": (
                        f"{exc.field_label} range must share a prefix and end "
                        "in a number, e.g. N701-N729."
                    ),
                },
                status=400,
            )

        if i7_id_q is not None:
            library_queryset = library_queryset.filter(i7_id_q)
            sample_queryset = sample_queryset.filter(i7_id_q)

        if i5_id_q is not None:
            library_queryset = library_queryset.filter(i5_id_q)
            sample_queryset = sample_queryset.filter(i5_id_q)

        if index_type_filter:
            library_queryset = library_queryset.filter(
                index_type_name__icontains=index_type_filter
            )
            sample_queryset = sample_queryset.filter(
                index_type_name__icontains=index_type_filter
            )

        changed_ownership_filter = request.GET.get("changed_ownership")

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
