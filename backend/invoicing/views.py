from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.db.models import Min, Prefetch, Q
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import (
    FixedCosts,
    LibraryPreparationCosts,
    SequencingCosts,
)
from .serializers import (
    FixedCostsSerializer,
    InvoicingSerializer,
    LibraryPreparationCostsSerializer,
    SequencingCostsSerializer,
)

Request = apps.get_model("request", "Request")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
Flowcell = apps.get_model("flowcell", "Flowcell")


class InvoicingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]

    serializer_class = InvoicingSerializer

    def get_start_end_dates(self):
        today = timezone.datetime.today()

        default_start_date = today - relativedelta(months=0)
        default_end_date = today

        start_date_param = self.request.query_params.get(
            "start", default_start_date.strftime("%Y-%m")
        )
        end_date_param = self.request.query_params.get(
            "end", default_end_date.strftime("%Y-%m")
        )

        start_date = timezone.datetime.strptime(start_date_param, "%Y-%m")
        end_date = timezone.datetime.strptime(end_date_param, "%Y-%m")

        start_date = start_date.replace(day=1)
        end_date = end_date.replace(day=1) + relativedelta(months=1, seconds=-1)

        return start_date, end_date

    def get_serializer_context(self):
        start_date, end_date = self.get_start_end_dates()
        today = timezone.datetime.today()
        ctx = {"start_date": start_date, "end_date": end_date, "today": today}

        return ctx

    def get_queryset(self):
        start_date, end_date = self.get_start_end_dates()

        flowcell_qs = (
            Flowcell.objects.select_related(
                "sequencer",
            )
            .filter(archived=False)
            .order_by("flowcell_id")
        )

        libraries_qs = (
            Library.objects.filter(~Q(pool=None) & ~Q(status=-1))
            .select_related(
                "read_length",
                "library_protocol",
            )
            .only("read_length", "library_protocol__name")
        )

        samples_qs = (
            Sample.objects.filter(~Q(pool=None) & ~Q(status=-1))
            .select_related(
                "read_length",
                "library_protocol",
            )
            .only("read_length", "library_protocol__name")
        )

        queryset = (
            Request.objects.filter(
                flowcell__create_time__gte=start_date,
                flowcell__create_time__lte=end_date,
                sequenced=True,
                archived=False,
            )
            .select_related(
                "cost_unit",
            )
            .prefetch_related(
                Prefetch("flowcell", queryset=flowcell_qs),
                Prefetch("libraries", queryset=libraries_qs),
                Prefetch("samples", queryset=samples_qs),
            )
            .distinct()
            .annotate(sequencing_date=Min("flowcell__create_time"))
            .only(
                "name",
                "cost_unit__name",
            )
            .order_by("sequencing_date", "pk")
        )

        return queryset

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class FixedCostsViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of Fixed Costs."""

    permission_classes = [IsAdminUser]
    queryset = FixedCosts.objects.filter(sequencer__archived=False)
    serializer_class = FixedCostsSerializer


class LibraryPreparationCostsViewSet(
    mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet
):
    """Get the list of Library Preparation Costs."""

    permission_classes = [IsAdminUser]
    queryset = LibraryPreparationCosts.objects.filter(
        archived=False, library_protocol__archived=False
    )
    # print(queryset.query)

    serializer_class = LibraryPreparationCostsSerializer


class SequencingCostsViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of Sequencing Costs."""

    permission_classes = [IsAdminUser]
    queryset = SequencingCosts.objects.filter(sequencer__archived=False)
    serializer_class = SequencingCostsSerializer
