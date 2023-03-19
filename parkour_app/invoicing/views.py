import calendar

import pandas as pd
from common.views import CsrfExemptSessionAuthentication
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.db.models import Min, Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from month import Month
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from xlwt import Workbook, XFStyle
from common.models import Organization

from .models import (
    FixedCosts,
    InvoicingReport,
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
ReadLength = apps.get_model("library_sample_shared", "ReadLength")
LibraryProtocol = apps.get_model("library_sample_shared", "LibraryProtocol")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
Flowcell = apps.get_model("flowcell", "Flowcell")


class InvoicingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]

    serializer_class = InvoicingSerializer

    def get_serializer_context(self):
        today = timezone.datetime.today()
        year = self.request.query_params.get("year", today.year)
        month = self.request.query_params.get("month", today.month)
        organization_id = self.request.query_params.get("organization", 0)
        ctx = {"curr_month": month, "curr_year": year,
               "today": today, "organization_id": organization_id}
        return ctx

    def get_queryset(self):
        today = timezone.datetime.today()
        year = self.request.query_params.get("year", today.year)
        month = self.request.query_params.get("month", today.month)
        organization_id = self.request.query_params.get("organization", None)

        flowcell_qs = Flowcell.objects.select_related(
            "pool_size",
        ).order_by("flowcell_id")

        libraries_qs = (
            Library.objects.filter(~Q(pool=None))
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
                flowcell__create_time__year=year,
                flowcell__create_time__month=month,
                sequenced=True,
                cost_unit__organization__id=organization_id
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

        today = timezone.datetime.today()
        year = self.request.query_params.get("year", today.year)
        month = self.request.query_params.get("month", today.month)
        ctx = {"curr_month": month, "curr_year": year, "today": today}
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(methods=["get"], detail=False)
    def billing_periods(self, request):
        flowcells = Flowcell.objects.all()
        data = []

        if flowcells.count() == 0:
            return Response(data)

        start_date = flowcells.first().create_time
        end_date = flowcells.last().create_time
        end_date = end_date + relativedelta(months=1)

        dates = pd.date_range(start_date, end_date, inclusive="left", freq="M")
        for dt in dates:
            try:
                report_urls = []
                reports = InvoicingReport.objects.filter(month=dt.strftime("%Y-%m"))
                for r in reports:
                    report_urls.append({'organization_id': r.organization.id, 'url': settings.MEDIA_URL + r.report.name})
            except InvoicingReport.DoesNotExist:
                report_urls = []
            data.append(
                {
                    "name": dt.strftime("%B %Y"),
                    "value": [dt.year, dt.month],
                    "report_urls": report_urls,
                }
            )

        return Response(data)

    @action(
        methods=["post"],
        detail=False,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def upload(self, request):
        """Upload Invoicing Report."""
        month = request.data.get("month", None)
        report = request.data.get("report", None)
        organization_id = request.data.get("organization", None)

        if not month or not report or not organization_id:
            return Response(
                {
                    "success": False,
                    "error": "Month, report or organization is not set.",
                },
                400,
            )

        try:
            report = InvoicingReport.objects.get(month=month, organization__id=organization_id)
            report.report = request.data.get("report")
        except InvoicingReport.DoesNotExist:
            report = InvoicingReport(
                month=Month.from_string(month),
                report=request.data.get("report"),
                organization_id=organization_id
            )
        finally:
            report.save()

        return JsonResponse({"success": True})

    @action(methods=["get"], detail=False)
    def download(self, request):
        """Download Invoicing Report."""
        today = timezone.datetime.today()
        year = self.request.query_params.get("year", today.year)
        month = int(self.request.query_params.get("month", today.month))
        organization = Organization.objects.get(id=self.request.query_params.get("organization", 0))

        filename = f"Invoicing_Report_{'_'.join(str(organization).split())}_{calendar.month_name[month]}_{year}.xls"
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        queryset = self.filter_queryset(self.get_queryset())
        data = self.get_serializer(queryset, many=True).data

        wb = Workbook(encoding="utf-8")

        font_style = XFStyle()
        font_style.alignment.wrap = 1
        font_style_bold = XFStyle()
        font_style_bold.font.bold = True

        def write_header(ws, row_num, header):
            for i, column in enumerate(header):
                ws.write(row_num, i, column, font_style_bold)
                ws.col(i).width = 8000

        def write_row(ws, row_num, row):
            for i in range(len(row)):
                ws.write(row_num, i, row[i], font_style)

        # First sheet
        ws = wb.add_sheet("Invoicing")
        row_num = 0
        header = [
            "Request ID",
            "Cost Unit",
            "Sequencing kit",
            "Date + Flowcell ID",
            "Pool ID",
            "% of Lanes",
            "Read Length",
            "# of Libraries/Samples",
            "Library Preparation Protocol",
            "Fixed Costs",
            "Sequencing Costs",
            "Preparation Costs",
            "Variable Costs",
            "Total Costs",
        ]
        write_header(ws, row_num, header)

        for item in data:
            row_num += 1

            # cost_units = '; '.join(sorted(item['cost_unit']))
            pool_sizes = "; ".join(
                sorted(list({x["pool_size_name"] for x in item["pool_size"]}))
            )
            flowcells = "; ".join(item["flowcell"])
            pools = "; ".join(item["pool"])

            percentage = "; ".join(
                list(
                    map(
                        lambda x: ", ".join([y["percentage"] for y in x["pools"]]),
                        item["percentage"],
                    )
                )
            )

            read_lengths = "; ".join(
                ReadLength.objects.filter(pk__in=item["read_length"])
                .order_by("name")
                .values_list("name", flat=True)
            )

            protocol = LibraryProtocol.objects.get(pk=item["library_protocol"])

            row = [
                item["request"],
                item["cost_unit"],
                pool_sizes,
                flowcells,
                pools,
                percentage,
                read_lengths,
                item["num_libraries_samples"],
                protocol.name,
                item["fixed_costs"],
                item["sequencing_costs"],
                item["preparation_costs"],
                item["variable_costs"],
                item["total_costs"],
            ]
            write_row(ws, row_num, row)

        # Second sheet
        ws = wb.add_sheet("Fixed Costs")
        row_num = 0
        header = ["Sequencer", "Price"]
        write_header(ws, row_num, header)
        for item in FixedCosts.objects.filter(fixedprice__organization=organization):
            row_num += 1
            row = [item.sequencer.name, item.fixedprice_set.get(organization=organization).price]
            write_row(ws, row_num, row)

        # Third sheet
        ws = wb.add_sheet("Preparation Costs")
        row_num = 0
        header = ["Library Protocol", "Price"]
        write_header(ws, row_num, header)
        for item in LibraryPreparationCosts.objects.filter(librarypreparationprice__organization=organization):
            row_num += 1
            row = [item.library_protocol.name, item.librarypreparationprice_set.get(organization=organization).price]
            write_row(ws, row_num, row)

        # Fourth sheet
        ws = wb.add_sheet("Sequencing Costs")
        row_num = 0
        header = ["Sequencing Kit", "Price"]
        write_header(ws, row_num, header)
        for item in SequencingCosts.objects.filter(sequencingprice__organization=organization):
            row_num += 1
            row = [
                str(item.pool_size),
                item.sequencingprice_set.get(organization=organization).price,
            ]
            write_row(ws, row_num, row)

        wb.save(response)
        return response


class FixedCostsViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of Fixed Costs."""

    permission_classes = [IsAdminUser]
    queryset = FixedCosts.objects.filter(sequencer__obsolete=settings.NON_OBSOLETE)
    serializer_class = FixedCostsSerializer

    def get_serializer_context(self):
        organization_id = self.request.query_params.get("organization", 0)
        ctx = {'organization_id': organization_id}
        return ctx


class LibraryPreparationCostsViewSet(
    mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet
):
    """Get the list of Library Preparation Costs."""

    permission_classes = [IsAdminUser]
    queryset = LibraryPreparationCosts.objects.filter(
        library_protocol__obsolete=settings.NON_OBSOLETE
    )
    serializer_class = LibraryPreparationCostsSerializer

    def get_serializer_context(self):
        organization_id = self.request.query_params.get("organization", 0)
        ctx = {'organization_id': organization_id}
        return ctx

    def update(self, request, *args, **kwargs):

        return super().update(request, *args, **kwargs)


class SequencingCostsViewSet(mixins.UpdateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Get the list of Sequencing Costs."""

    permission_classes = [IsAdminUser]
    queryset = SequencingCosts.objects.filter(pool_size__sequencer__obsolete=settings.NON_OBSOLETE)
    serializer_class = SequencingCostsSerializer

    def get_serializer_context(self):
        organization_id = self.request.query_params.get("organization", 0)
        ctx = {'organization_id': organization_id}
        return ctx
