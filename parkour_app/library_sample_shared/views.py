import json
import logging

from common.utils import retrieve_group_items
from common.views import StandardResultsSetPagination
from django.apps import apps
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from .models import (
    ConcentrationMethod,
    IndexI5,
    IndexI7,
    IndexType,
    LibraryProtocol,
    LibraryType,
    Organism,
    ReadLength,
)
from .serializers import (
    ConcentrationMethodSerializer,
    IndexI5Serializer,
    IndexI7Serializer,
    IndexTypeSerializer,
    LibraryProtocolSerializer,
    LibraryTypeSerializer,
    OrganismSerializer,
    ReadLengthSerializer,
)

Request = apps.get_model("request", "Request")

logger = logging.getLogger("db")


class MoveOtherMixin:
    """Move the `Other` option to the end of the returning list."""

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(self._get_data(serializer))

        serializer = self.get_serializer(queryset, many=True)
        return Response(self._get_data(serializer))

    def _get_data(self, serializer):
        data = serializer.data

        # Move the 'Other' option to the end of the list
        other_options = sorted(
            (x for x in data if "Other" in x["name"]), key=lambda x: x["name"]
        )

        for other in other_options:
            index = data.index(other)
            data.append(data.pop(index))

        return data


class OrganismViewSet(MoveOtherMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of organisms."""

    queryset = Organism.objects.filter(archived=False).order_by("name")
    serializer_class = OrganismSerializer


class ReadLengthViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of read lengths."""

    serializer_class = ReadLengthSerializer

    def get_queryset(self):

        request_id = int(self.request.query_params.get("request_id", 0))
        pool_size_user_id = int(self.request.query_params.get("pool_size_user", 0))
        set_read_lengths = ReadLength.objects.none()

        try:

            if not (request_id or pool_size_user_id):
                raise Exception

            # Get reads that have already been added
            request = Request.objects.filter(id=request_id).first()
            if request:
                set_read_length_ids = set(list(request.libraries.values_list('read_length', flat=True)) +
                                        list(request.samples.values_list('read_length', flat=True)))
                set_read_lengths = ReadLength.objects.filter(id__in=set_read_length_ids)

            # Filter choices based on sequencing kit selected and lengths already present
            if pool_size_user_id:
                choices = ReadLength.objects.filter(pool_size__id=pool_size_user_id, archived=False)
            else:
                raise Exception

        except:

            choices = ReadLength.objects.filter(archived=False)
        
        return sorted((choices | set_read_lengths).distinct(), key= lambda e: [int(n) for n in e.name.split('x')])

class ReadLengthInvoicingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReadLength.objects.all().filter(archived=False)
    serializer_class = ReadLengthSerializer


class ConcentrationMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of concentration methods."""

    queryset = ConcentrationMethod.objects.order_by("name")
    serializer_class = ConcentrationMethodSerializer


class IndexTypeViewSet(MoveOtherMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of index types."""

    queryset = IndexType.objects.filter(archived=False).order_by("name")
    serializer_class = IndexTypeSerializer


class IndexViewSet(viewsets.ViewSet):
    def list(self, request):
        """Get the list of all indices."""
        index_i7_serializer = IndexI7Serializer(
            IndexI7.objects.all().filter(archived=False), many=True
        )
        index_i5_serializer = IndexI5Serializer(
            IndexI5.objects.all().filter(archived=False), many=True
        )
        indices = index_i7_serializer.data + index_i5_serializer.data
        data = sorted(indices, key=lambda x: x["index_id"])
        return Response(data)

    @action(methods=["get"], detail=False)
    def i7(self, request):
        """Get the list of indices i7."""
        data = self._get_sorted_indices(IndexI7, IndexI7Serializer)
        return Response(data)

    @action(methods=["get"], detail=False)
    def i5(self, request):
        """Get the list of indices i5."""
        data = self._get_sorted_indices(IndexI5, IndexI5Serializer)
        return Response(data)

    def _get_sorted_indices(self, model_class, serializer_model_class):
        queryset = self._get_index_queryset(model_class)
        serializer = serializer_model_class(queryset, many=True)
        return sorted(serializer.data, key=lambda x: x["index_id"])

    def _get_index_queryset(self, model_class):
        queryset = model_class.objects.all()
        index_type = self.request.query_params.get("index_type_id", None)
        if index_type is not None:
            try:
                queryset = queryset.filter(index_type=index_type)
            except ValueError:
                queryset = []
        return queryset


class LibraryProtocolViewSet(MoveOtherMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of library protocols."""

    serializer_class = LibraryProtocolSerializer

    def get_queryset(self):
        queryset = LibraryProtocol.objects.filter(archived=False).order_by("name")
        na_type = self.request.query_params.get("type", None)
        if na_type is not None:
            queryset = queryset.filter(type=na_type)
        queryset = queryset.filter(archived=False)
        return queryset


class LibraryProtocolInvoicingViewSet(MoveOtherMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of library protocols for invoicing."""

    serializer_class = LibraryProtocolSerializer

    def get_queryset(self):
        queryset = LibraryProtocol.objects.filter(archived=False).order_by("name")
        na_type = self.request.query_params.get("type", None)
        if na_type is not None:
            queryset = queryset.filter(type=na_type)

        return queryset


class LibraryTypeViewSet(MoveOtherMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of library types."""

    serializer_class = LibraryTypeSerializer

    def get_queryset(self):
        queryset = LibraryType.objects.filter(archived=False).order_by("name")
        library_protocol = self.request.query_params.get("library_protocol_id", None)
        if library_protocol is not None:
            try:
                queryset = queryset.filter(library_protocol__in=[library_protocol])
            except ValueError:
                queryset = []
        return queryset


class LibrarySampleBaseViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.get_serializer().Meta.model.objects.all()

    # TODO: add pagination
    def list(self, request):
        """Get the list of all libraries or samples."""
        
        data = []

        request_id = request.query_params.get("request_id", None)
        ids = json.loads(request.query_params.get("ids", "[]"))

        if request_id:
            request_queryset = Request.objects.all().filter(
                archived=False, pk=request_id
            )
        else:
            request_queryset = (
                Request.objects.all().filter(archived=False).order_by("-create_time")
            )

        if not (self.request.user.is_staff or self.request.user.member_of_bcf):
            if self.request.user.is_pi:
                request_queryset = request_queryset.filter(pi=self.request.user)
            else:
                request_queryset = request_queryset.filter(Q(user=self.request.user) | Q(bioinformatician=self.request.user)).distinct()

        for request_obj in request_queryset:
            # TODO: sort by item['barcode'][3:]
            records = getattr(request_obj, self._get_model_name_plural())
            if ids:
                try:
                    records = records.filter(pk__in=ids)
                except ValueError:
                    return Response(
                        {
                            "success": False,
                            "message": "Invalid payload.",
                        },
                        400,
                    )
            serializer = self.serializer_class(records, many=True)
            data += serializer.data

        return Response({"success": True, "data": data})

    def create(self, request):
        """Add new libraries/samples."""
        post_data = json.loads(request.POST.get("data", "[]"))

        if not post_data:
            return Response(
                {
                    "success": False,
                    "message": "Invalid payload.",
                },
                400,
            )

        serializer = self.serializer_class(data=post_data, many=True)
        if serializer.is_valid():
            objects = serializer.save()
            data = [
                {
                    "pk": obj.pk,
                    "record_type": obj.__class__.__name__,
                    "name": obj.name,
                    "barcode": obj.barcode,
                }
                for obj in objects
            ]
            return Response({"success": True, "data": data}, 201)

        else:
            # Try to create valid records
            valid_data = [
                item[1] for item in zip(serializer.errors, post_data) if not item[0]
            ]

            if any(valid_data):
                message = "Invalid payload. Some records cannot be added."
                objects = self._create_or_update_valid(valid_data)

                data = [
                    {
                        "pk": obj.pk,
                        "record_type": obj.__class__.__name__,
                        "name": obj.name,
                        "barcode": obj.barcode,
                    }
                    for obj in objects
                ]

                return Response(
                    {
                        "success": True,
                        "message": message,
                        "data": data,
                    },
                    201,
                )

            else:
                # logger.debug('POST DATA', post_data)
                # logger.debug('VALIDATION ERRORS', serializer.errors)
                return Response(
                    {
                        "success": False,
                        "message": "Invalid payload.",
                    },
                    400,
                )

    @action(methods=["post"], detail=False)
    def edit(self, request):
        """Update multiple libraries/samples."""
        post_data = json.loads(request.POST.get("data", "[]"))

        if not post_data:
            return Response(
                {
                    "success": False,
                    "message": "Invalid payload.",
                },
                400,
            )

        ids = [x["pk"] for x in post_data]
        objects = self._get_model().objects.filter(pk__in=ids)
        serializer = self.serializer_class(data=post_data, instance=objects, many=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"success": True})

        else:
            # Try to update valid records
            valid_data = [
                item[1] for item in zip(serializer.errors, post_data) if not item[0]
            ]

            if any(valid_data):
                message = "Invalid payload. Some records cannot be updated."
                ids = [x["pk"] for x in valid_data]
                self._create_or_update_valid(valid_data, ids)
                return Response({"success": True, "message": message}, 200)

            else:
                return Response(
                    {
                        "success": False,
                        "message": "Invalid payload.",
                    },
                    400,
                )

    def _create_or_update_valid(self, valid_data, ids=None):
        """Create or update valid objects."""
        if not ids:
            serializer = self.serializer_class(data=valid_data, many=True)
        else:
            objects = self._get_model().objects.filter(pk__in=ids)
            serializer = self.serializer_class(
                data=valid_data, instance=objects, many=True
            )
        serializer.is_valid()
        return serializer.save()

    def _get_model(self):
        return self.get_serializer().Meta.model

    def _get_model_name_plural(self):
        return self._get_model()._meta.verbose_name_plural.lower()

    def destroy(self, request, pk=None, *args, **kwargs):
        # A ripoff of https://stackoverflow.com/a/52700398/4222260

        try:
            super(LibrarySampleBaseViewSet, self).destroy(request, pk, *args, **kwargs)
            return Response({"success": True}, 200)
        except:
            return Response({"success": False, "message": 'The record could not be deleted.'}, 404)