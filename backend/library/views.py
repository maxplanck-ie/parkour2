import logging
import operator
import json
from functools import reduce

from common.utils import retrieve_group_items
from django.apps import apps
from django.db.models import Prefetch, Q, Model, ManyToOneRel, ManyToManyRel
from django.forms.models import model_to_dict
from library_sample_shared.views import LibrarySampleBaseViewSet
from django.http import JsonResponse
from datetime import datetime
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
        self, queryset, search_string=None, status_filter=None, library_protocol_filter=None
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
                    result[field_name] = value if self.is_json_serializable(value) else str(value)
            except Exception:
                result[field_name] = None
        return result

    def get_library_or_sample_data(self, sample_id=None, library_id=None):
        if sample_id:
            try:
                sample = Sample.objects.select_related(
                    "nucleic_acid_type",
                    "library_protocol",
                    "library_type",
                    "read_length",
                    "organism",
                    "index_type",
                    "librarypreparation",
                    "pooling"
                ).get(pk=sample_id)

                sample_data = self.serialize_model_instance(sample)
                return sample_data
            except Sample.DoesNotExist:
                return None

        elif library_id:
            try:
                library = Library.objects.select_related(
                    "library_protocol",
                    "library_type",
                    "read_length",
                    "index_type",
                    "organism",
                ).get(pk=library_id)

                return [{
                    "id": library.id,
                    "name": library.name,
                    "barcode": library.barcode,
                    "library_protocol_name": library.library_protocol.name if library.library_protocol else "",
                    "create_time": library.create_time.isoformat() if library.create_time else "",
                    "organism_name": library.organism.name if library.organism else "",
                    "nucleic_acid_type_name": "",  # Libraries typically don't have this
                    "library_type_name": library.library_type.name if library.library_type else "",
                    "read_length_name": library.read_length.name if library.read_length else "",
                    "sequencing_depth": library.sequencing_depth,
                    "rna_quality": "",  # Optional field
                    "is_converted": "",  # Optional field
                    "record_type": "Library",
                    "request_name": library.request.name if library.request else "",
                    "request_id": library.request.id if library.request else ""
                }]
            except Library.DoesNotExist:
                return None
        return None

    def list(self, request):
        sample_id = request.query_params.get("sample_id")
        library_id = request.query_params.get("library_id")

        data = self.get_library_or_sample_data(sample_id=sample_id, library_id=library_id)

        if not data:
            return Response({"success": False, "message": "No sample or library found for given ID."}, status=404)

        ro_crate = {
            "@context": "https://w3id.org/ro/crate/1.1/context",
            "@graph": []
        }

        root_metadata = {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {
                "@id": "https://w3id.org/ro/crate/1.1"
            },
            "about": {
                "@id": "./"
            }
        }

        dataset = {
            "@id": "./",
            "@type": "Dataset",
            "name": "ISA Sample or Library Record",
            "datePublished": datetime.now().isoformat(),
            "hasPart": []
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

        ro_crate["@graph"].insert(0, root_metadata)
        ro_crate["@graph"].insert(1, dataset)
        ro_crate["@graph"].insert(2, data)

        return JsonResponse(ro_crate, safe=False)

class LibraryViewSet(LibrarySampleBaseViewSet):
    serializer_class = LibrarySerializer
