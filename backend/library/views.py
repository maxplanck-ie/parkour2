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
        """Get the list of libraries and samples."""

        show_all = request.query_params.get("showAll") or False
        search_string = request.query_params.get("searchString")
        status_filter = request.query_params.get("statusFilter")
        library_protocol_filter = request.query_params.get("libraryProtocolFilter")
        request_id = request.query_params.get("node", None)

        if request_id and request_id != "root":
            libraries_qs = Library.objects.all().select_related(
                "library_protocol",
                "library_type",
                "read_length",
                "index_type",
                "organism",
            )
            samples_qs = Sample.objects.all().select_related(
                "nucleic_acid_type",
                "library_protocol",
                "library_type",
                "read_length",
                "organism",
            )

            libraries_qs = self.filter_and_search(
                libraries_qs, search_string, status_filter, library_protocol_filter
            )
            samples_qs = self.filter_and_search(
                samples_qs, search_string, status_filter, library_protocol_filter
            )

            queryset = (
                Request.objects.filter(archived=False, pk=request_id)
                .prefetch_related(
                    Prefetch("libraries", queryset=libraries_qs),
                    Prefetch("samples", queryset=samples_qs),
                )
                .only("name")
            )

            if not self.request.user.is_staff:
                if not self.request.user.is_pi:
                    queryset = queryset.filter(user=self.request.user)
                else:
                    queryset = retrieve_group_items(self.request, queryset)

            queryset = queryset.first()
            serializer = RequestChildrenNodesSerializer(queryset)

            try:
                return Response(
                    {
                        "success": True,
                        "children": serializer.data["children"],
                    }
                )
            except KeyError:
                return Response(
                    {
                        "success": False,
                        "children": [],
                    },
                    400,
                )
        else:
            queryset = self.get_queryset(
                show_all, search_string, status_filter, library_protocol_filter
            )
            serializer = RequestParentNodeSerializer(queryset, many=True)
            filtered_data = [
                item for item in serializer.data if item["total_records_count"] != 0
            ]  # omit rows (requests) that would be empty upon expanding (clicking plus sign)

            return Response({"success": True, "children": filtered_data})


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

    def list(self, request):
        library_ids = request.query_params.get("library_ids")
        sample_ids = request.query_params.get("sample_ids")
        request_ids = request.query_params.get("request_ids")
        barcodes = request.query_params.get("barcodes")

        ls_data = []
        request_data = []

        if sample_ids:
            samples = Sample.objects.select_related(
                "nucleic_acid_type",
                "library_protocol",
                "library_type",
                "read_length",
                "organism",
                "index_type",
                "librarypreparation",
                "pooling",
            ).filter(id__in=sample_ids)

            for sample in samples:
                ls_data.append(self.serialize_model_instance(sample))

        if library_ids:
            libraries = Library.objects.select_related(
                "library_protocol",
                "library_type",
                "read_length",
                "index_type",
                "organism",
                "test",
            ).filter(id__in=library_ids)

            for lib in libraries:
                ls_data.append(self.serialize_model_instance(lib))

        if request_ids:
            sample_req_matches = Sample.objects.select_related(
                "nucleic_acid_type",
                "library_protocol",
                "library_type",
                "read_length",
                "organism",
                "index_type",
                "librarypreparation",
                "pooling",
            ).filter(request_id__in=barcodes)

            for sample in sample_req_matches:
                ls_data.append(self.serialize_model_instance(sample))

            library_req_matches = Library.objects.select_related(
                "library_protocol",
                "library_type",
                "read_length",
                "index_type",
                "organism",
                "test",
            ).filter(request_id__in=barcodes)

            for lib in library_req_matches:
                ls_data.append(self.serialize_model_instance(lib))

        if barcodes:
            sample_bar_matches = Sample.objects.select_related(
                "nucleic_acid_type",
                "library_protocol",
                "library_type",
                "read_length",
                "organism",
                "index_type",
                "librarypreparation",
                "pooling",
            ).filter(barcode__in=barcodes)

            for sample in sample_bar_matches:
                ls_data.append(self.serialize_model_instance(sample))

            library_bar_matches = Library.objects.select_related(
                "library_protocol",
                "library_type",
                "read_length",
                "index_type",
                "organism",
                "test",
            ).filter(barcode__in=barcodes)

            for lib in library_bar_matches:
                ls_data.append(self.serialize_model_instance(lib))

        # request_qs = Request.objects.prefetch_related(
        #         Prefetch("samples", queryset=Sample.objects.filter(barcode__in=barcodes))
        #     )

        # for obj in request_qs:
        #     request_data.append(RequestChildrenNodesSerializer(obj).data)

        # request_qs = Request.objects.prefetch_related(
        #     # Prefetch("libraries", queryset=Library.objects.select_related(
        #     #         "library_protocol",
        #     #         "library_type",
        #     #         "read_length",
        #     #         "index_type",
        #     #         "organism",
        #     #     ).get(pk=library_id)),
        #         Prefetch("samples", queryset=Sample.objects.filter(barcode=barcode)))

        # obj = request_qs.first()  # or get(), depending
        # request_data = RequestChildrenNodesSerializer(obj).data

        if not ls_data:
            return Response(
                {"success": False, "message": "No matching library or sample found."},
                status=404,
            )

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

        # for item in data:
        #     item_id = f"#{item['record_type'].lower()}-{item['id']}"
        #     item_entity = {
        #         "@id": item_id,
        #         "@type": item["record_type"],
        #         "name": item["name"],
        #         "identifier": item["barcode"],
        #         "description": item["library_protocol_name"],
        #         "dateCreated": item["create_time"],
        #         "organism": item["organism_name"],
        #         "nucleicAcidType": item["nucleic_acid_type_name"],
        #         "libraryType": item["library_type_name"],
        #         "readLength": item["read_length_name"],
        #         "sequencingDepth": item["sequencing_depth"],
        #         "rnaQuality": item["rna_quality"],
        #         "isConverted": item["is_converted"],
        #         "recordType": item["record_type"],
        #     }
        #     dataset["hasPart"].append({"@id": item_id})
        #     ro_crate["@graph"].append(item_entity)

        ro_crate["@graph"].insert(0, ro_metadata)
        ro_crate["@graph"].insert(1, ro_dataset)
        ro_crate["@graph"].insert(2, ls_data)
        ro_crate["@graph"].insert(3, request_data)

        return JsonResponse(ro_crate, safe=False)


class LibraryViewSet(LibrarySampleBaseViewSet):
    serializer_class = LibrarySerializer
