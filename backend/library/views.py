from collections import defaultdict
from datetime import datetime
from functools import reduce
from itertools import chain
from operator import or_

from django.apps import apps
from django.db.models import Max, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response

from library_sample_shared.views import LibrarySampleBaseViewSet

from .serializers import LibrarySerializer
from .utils import get_accessible_requests

CompleteLibraryData = apps.get_model("library", "CompleteLibraryData")
CompleteSampleData = apps.get_model("sample", "CompleteSampleData")


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
        library_queryset = library_queryset.filter(request_id__in=accessible_request_ids)
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
                    search_fields = [
                        "name__icontains",
                        "barcode__icontains",
                        "request_name__icontains",
                        "flowcell_ids__icontains",
                        "pool_names__icontains",
                    ]
                    field_qs = [Q(**{field: term}) for field in search_fields]
                    combined_or_for_term = reduce(or_, field_qs)
                    and_qs.append(combined_or_for_term)

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
            library_queryset = library_queryset.filter(sequencer_ids__contains=[seq_id])
            sample_queryset = sample_queryset.filter(sequencer_ids__contains=[seq_id])

        if read_length_filter:
            library_queryset = library_queryset.filter(
                read_length_id=int(read_length_filter)
            )
            sample_queryset = sample_queryset.filter(
                read_length_id=int(read_length_filter)
            )

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
            lib["record_type"] = "Library"
            combined_data.append(lib)

        for sample in samples:
            sample["record_type"] = "Sample"
            combined_data.append(sample)

        combined_data.sort(key=lambda x: x["create_time"], reverse=True)

        return Response(
            {
                "success": True,
                "total": total_requests,
                "page": page if page_size else 1,
                "page_size": page_size if page_size else total_requests,
                "total_pages": total_pages,
                "children": combined_data,
            }
        )


class LibraryViewSet(LibrarySampleBaseViewSet):
    serializer_class = LibrarySerializer
