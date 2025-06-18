import logging
import operator
import json
from functools import reduce

from common.utils import retrieve_group_items
from django.apps import apps
from django.db.models import Prefetch, Q, Model, ManyToOneRel, ManyToManyRel
from django.utils import timezone
from django.forms.models import model_to_dict
from library_sample_shared.views import LibrarySampleBaseViewSet
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from .serializers import (
    LibrarySerializer,
    RequestChildrenNodesSerializer,
    RequestParentNodeSerializer,
)

Request = apps.get_model("request", "Request")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")

logger = logging.getLogger("db")


class LibrarySampleTree(viewsets.ViewSet):
    def filter_and_search(
        self,
        queryset,
        search_string=None,
        status_filter=None,
        library_protocol_filter=None,
    ):
        """Helper function for both get_queryset and list action"""
        if search_string:
            search_fields = [
                "name__icontains",
                "barcode__icontains",
                "request__name__icontains",
            ]
            search_filters = [Q(**{field: search_string}) for field in search_fields]
            queryset = queryset.filter(reduce(operator.or_, search_filters))

        if status_filter:
            queryset = queryset.filter(status=int(status_filter))

        if library_protocol_filter:
            queryset = queryset.filter(library_protocol=int(library_protocol_filter))

        return queryset

    def get_queryset(
        self,
        show_all=True,
        search_string=None,
        status_filter=None,
        library_protocol_filter=None,
    ):
        libraries_qs = Library.objects.all().only("sequencing_depth")
        samples_qs = Sample.objects.all().only("sequencing_depth")

        libraries_qs = self.filter_and_search(
            libraries_qs, search_string, status_filter, library_protocol_filter
        )
        samples_qs = self.filter_and_search(
            samples_qs, search_string, status_filter, library_protocol_filter
        )

        queryset = (
            Request.objects.filter(archived=False)
            .prefetch_related(
                Prefetch("libraries", queryset=libraries_qs),
                Prefetch("samples", queryset=samples_qs),
            )
            .only("name")
            .order_by("-create_time")
        )

        if not show_all:
            queryset = queryset.filter(sequenced=False)
        if not self.request.user.is_staff:
            if not self.request.user.is_pi:
                queryset = queryset.filter(user=self.request.user)
            else:
                queryset = retrieve_group_items(self.request, queryset)

        return queryset

    def list(self, request):
        """Optimized: Get all child libraries and samples across all requests."""

        request_ids = Request.objects.filter(archived=False).values_list(
            "id", flat=True
        )

        # Prefetch optimized related fields for Sample
        samples = Sample.objects.filter(request__id__in=request_ids).select_related(
            "nucleic_acid_type",
            "library_protocol",
            "library_type",
            "read_length",
            "organism",
        )

        # Prefetch optimized related fields for Library
        libraries = Library.objects.filter(request__id__in=request_ids).select_related(
            "library_protocol", "library_type", "read_length", "index_type", "organism"
        )

        # Serialize samples
        sample_data = []
        for sample in samples:
            sample_data.append(
                {
                    "id": sample.id,
                    "pk": sample.pk,
                    "name": sample.name,
                    "barcode": sample.barcode,
                    "status": sample.status,
                    "create_time": sample.create_time.isoformat(),
                }
            )

        # Serialize libraries
        library_data = []
        for lib in libraries:
            library_data.append(
                {
                    "id": lib.id,
                    "pk": lib.pk,
                    "name": lib.name,
                    "barcode": lib.barcode,
                    "status": lib.status,
                    "create_time": lib.create_time.isoformat(),
                }
            )

        combined_data = sample_data + library_data

        return Response({"success": True, "children": combined_data})


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
