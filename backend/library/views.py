import logging
import operator
from functools import reduce

from common.utils import retrieve_group_items
from django.apps import apps
from django.db.models import Prefetch, Q
from library_sample_shared.views import LibrarySampleBaseViewSet
from rest_framework import viewsets
from rest_framework.response import Response

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
        self, queryset, search_string, status_filter, library_protocol_filter
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


class LibraryViewSet(LibrarySampleBaseViewSet):
    serializer_class = LibrarySerializer
