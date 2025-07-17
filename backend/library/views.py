import logging
import json
from functools import reduce

from django.apps import apps
from django.db.models import Prefetch, Q, Model, ManyToOneRel, ManyToManyRel, Max
from library_sample_shared.views import LibrarySampleBaseViewSet
from django.http import JsonResponse
from collections import defaultdict
from operator import or_
from itertools import chain
from rest_framework import viewsets
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta

from .serializers import (
    LibrarySerializer,
    RequestChildrenNodesSerializer,
)

Request = apps.get_model("request", "Request")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
CompleteLibraryData = apps.get_model("library", "CompleteLibraryData")
CompleteSampleData = apps.get_model("sample", "CompleteSampleData")

logger = logging.getLogger("db")
class LibrarySampleTree(viewsets.ViewSet):
    def list(self, request):
        # Extract parameters
        search_string = request.GET.get("search")
        status_filter = request.GET.get("status")
        library_protocol_filter = request.GET.get("library_protocol")
        start_date_str = request.GET.get("start_date")
        end_date_str = request.GET.get("end_date")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("size", 300))

        # Initialize querysets
        library_queryset = CompleteLibraryData.objects.all()
        sample_queryset = CompleteSampleData.objects.all()

        # Apply date filter
        if start_date_str and end_date_str:
            try:
                start_date = timezone.make_aware(datetime.strptime(start_date_str, "%d.%m.%Y"))
                end_date = timezone.make_aware(datetime.strptime(end_date_str, "%d.%m.%Y"))
                end_date = end_date.replace(hour=23, minute=59, second=59)
                library_queryset = library_queryset.filter(create_time__range=(start_date, end_date))
                sample_queryset = sample_queryset.filter(create_time__range=(start_date, end_date))
            except ValueError as e:
                return Response({"success": False, "error": "Invalid date format. Use DD.MM.YYYY"}, status=400)

        # Apply search filter
        if search_string:
            search_fields = ["name__icontains", "barcode__icontains", "request_name__icontains"]
            search_q = [Q(**{field: search_string}) for field in search_fields]
            combined_search = reduce(or_, search_q)
            library_queryset = library_queryset.filter(combined_search)
            sample_queryset = sample_queryset.filter(combined_search)

        # Apply status filter (libraries only)
        if status_filter:
            library_queryset = library_queryset.filter(status=int(status_filter))

        # Apply library protocol filter (libraries only)
        if library_protocol_filter:
            library_queryset = library_queryset.filter(
                library_protocol_name__icontains=library_protocol_filter
            )

        # Get distinct requests with latest activity time
        library_requests = (
            library_queryset
            .values('request_name')
            .annotate(latest_time=Max('create_time'))
            .values_list('request_name', 'latest_time')
        )
        
        sample_requests = (
            sample_queryset
            .values('request_name')
            .annotate(latest_time=Max('create_time'))
            .values_list('request_name', 'latest_time')
        )

        # Combine and find latest time per request
        request_time_map = defaultdict(lambda: timezone.make_aware(datetime.min))
        for request_name, latest_time in chain(library_requests, sample_requests):
            if latest_time > request_time_map[request_name]:
                request_time_map[request_name] = latest_time

        # Sort requests by latest activity (newest first)
        sorted_requests = sorted(
            request_time_map.items(),
            key=lambda x: x[1],
            reverse=True
        )
        request_names = [req for req, _ in sorted_requests]
        total_requests = len(request_names)

        # Paginate requests
        total_pages = (total_requests + page_size - 1) // page_size
        offset = (page - 1) * page_size
        paginated_requests = request_names[offset:offset + page_size]

        # Fetch records for paginated requests
        libraries = (
            library_queryset
            .filter(request_name__in=paginated_requests)
            .order_by("-create_time")
            .values()
        )
        samples = (
            sample_queryset
            .filter(request_name__in=paginated_requests)
            .order_by("-create_time")
            .values()
        )

        # Prepare combined data with record_type
        combined_data = []
        for lib in libraries:
            lib['record_type'] = 'library'
            combined_data.append(lib)
            
        for sample in samples:
            sample['record_type'] = 'sample'
            combined_data.append(sample)

        # Sort combined data by create_time (newest first)
        combined_data.sort(key=lambda x: x['create_time'], reverse=True)

        return Response({
            "success": True,
            "total": total_requests,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "children": combined_data
        })


class GenerateROCrate(viewsets.ViewSet):
    def is_json_serializable(self, value):
        try:
            json.dumps(value)
            return True
        except (TypeError, OverflowError):
            return False

    def serialize_model_instance(self, obj):
        if not isinstance(obj, Model):
            return str(obj)

        result = {}
        for field in obj._meta.get_fields():
            if isinstance(field, (ManyToOneRel, ManyToManyRel)):
                continue
            field_name = field.name
            try:
                value = getattr(obj, field_name)
                if isinstance(value, Model):
                    result[field_name] = self.serialize_model_instance(value)
                else:
                    result[field_name] = (
                        value if self.is_json_serializable(value) else str(value)
                    )
            except Exception:
                result[field_name] = None
        return result

    def snake_to_camel_case(self, snake_str):
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def clean_data(self, data):
        keys_to_remove = {"id", "pk", "archived"}
        cleaned_data = {}

        for key, value in data.items():
            if key in keys_to_remove or key.startswith("removed_"):
                continue

            if isinstance(value, dict):
                if value.get("archived") is True:
                    continue
                value = self.clean_data(value)

            cleaned_key = self.snake_to_camel_case(key)
            cleaned_data[cleaned_key] = value

        return cleaned_data

    def process_data(self, data):
        return [self.clean_data(item) for item in data]

    def list(self, request):
        barcodes = request.query_params.get("barcodes")
        barcodes_list = barcodes.split(",")

        ls_data = []
        request_data = []
        merged_data = []

        if barcodes_list:
            library_bar_matches = Library.objects.select_related(
                "library_protocol",
                "library_type",
                "read_length",
                "index_type",
                "organism",
                "pooling",
            ).filter(barcode__in=barcodes_list)

            for lib in library_bar_matches:
                ls_data.append(self.serialize_model_instance(lib))

            sample_bar_matches = Sample.objects.select_related(
                "nucleic_acid_type",
                "library_protocol",
                "library_type",
                "read_length",
                "organism",
                "index_type",
                "librarypreparation",
                "pooling",
            ).filter(barcode__in=barcodes_list)

            for sample in sample_bar_matches:
                ls_data.append(self.serialize_model_instance(sample))

            request_qs = (
                Request.objects.filter(
                    Q(libraries__barcode__in=barcodes_list)
                    | Q(samples__barcode__in=barcodes_list)
                )
                .prefetch_related(
                    Prefetch("libraries", queryset=library_bar_matches),
                    Prefetch("samples", queryset=sample_bar_matches),
                )
                .distinct()
            )

            for obj in request_qs:
                request_data.append(RequestChildrenNodesSerializer(obj).data)

        if not ls_data:
            return Response(
                {"success": False, "message": "No matching library or sample found."},
                status=404,
            )

        ls_data = self.process_data(ls_data)
        request_data = self.process_data(
            request_data
        )  # Still doesn't process the children

        # barcode_to_child = {}
        # for request in request_data:
        #     for child in request.get("children", []):
        #         barcode = child.get("barcode")
        #         if barcode:
        #             barcode_to_child[barcode] = child

        # for item in ls_data:
        #     barcode = item.get("barcode")
        #     if barcode and barcode in barcode_to_child:
        #         merged = {**item, **barcode_to_child[barcode]}
        #     else:
        #         merged = item
        #     merged_data.append(merged)

        ro_crate = {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": []}

        ro_metadata = {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "about": {"@id": "./"},
        }

        ro_dataset = {
            "@id": "./",
            "@type": "Dataset",
            "name": "ISA Sample or Library Record",
            "datePublished": timezone.now().isoformat(),
            "hasPart": [],
        }

        ro_crate["@graph"].insert(0, ro_metadata)
        ro_crate["@graph"].insert(1, ro_dataset)
        ro_crate["@graph"].insert(2, ls_data)
        ro_crate["@graph"].insert(3, request_data)

        return JsonResponse(ro_crate, safe=False)


class LibraryViewSet(LibrarySampleBaseViewSet):
    serializer_class = LibrarySerializer
