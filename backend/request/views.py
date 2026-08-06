import csv
import itertools
import json
import logging
import os
from io import StringIO
from unicodedata import normalize
from urllib.parse import urlencode

from common.mviews import refresh_batched
from common.serializers import UserSerializer
from common.utils import retrieve_group_items
from common.views import CsrfExemptSessionAuthentication, StandardResultsSetPagination
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import dateformat, timezone
from django.utils.crypto import get_random_string
from fpdf import FPDF, HTMLMixin
from fpdf.errors import FPDFUnicodeEncodingException
from library_sample_shared.models import LibraryProtocol
from library_sample_shared.serializers import LibraryProtocolSerializer
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from tablib import Dataset

from .models import FileRequest, Request, is_valid_file_type
from .resources import LibrariesResource, SamplesResource
from .serializers import RequestFileSerializer, RequestSerializer

User = get_user_model()
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")

logger = logging.getLogger("db")


def _recipient_list_with_sender_copy(*recipients):
    emails = []
    for recipient in recipients:
        if not recipient:
            continue
        if isinstance(recipient, (list, tuple, set)):
            emails.extend([r for r in recipient if r])
        else:
            emails.append(recipient)

    sender_email = getattr(settings, "SERVER_EMAIL", None)
    if sender_email:
        emails.append(sender_email)

    # Preserve order while removing duplicates
    return list(dict.fromkeys(emails))


class PDF(FPDF):  # pragma: no cover
    def __init__(self, title="Title", font="Arial"):
        super().__init__()
        self.core_fonts_encoding = "UTF-8"
        self.title = title
        self.font = font

    def header(self):
        self.set_font(self.font, style="B", size=14)  # Arial bold 15
        self.cell(0, 10, self.title, align="C")  # Title
        self.ln(10)  # Line break

    def footer(self):
        self.set_y(-15)  # Position at 1.5 cm from bottom
        self.set_font(self.font, size=8)  # Arial 8
        # Page number
        self.cell(0, 10, "Page " + str(self.page_no()) + " of {nb}", 0, 0, "C")

    def info_row(self, title, value):
        self.set_font(self.font, style="B", size=11)
        self.cell(35, 10, title + ":")
        self.set_font(self.font, size=11)
        self.cell(0, 10, value)
        self.ln(6)

    def multi_info_row(self, title, value):
        self.set_font(self.font, style="B", size=11)
        self.ln(3)
        self.cell(35, 4, title + ":")
        self.set_font(self.font, size=11)
        self.multi_cell(0, 5, value)
        self.ln(6)

    def multi_checkbox_row(self, title, values):
        self.set_font(self.font, style="B", size=11)
        self.ln(3)
        self.cell(35, 4, title + ":")
        for i in range(len(values)):
            if i > 0:
                self.cell(35, 4, "")
            self.set_font("glyphicons", size=11)
            self.cell(1, 4, "")
            self.set_font(self.font, size=11)
            self.multi_cell(0, 5, values[i])
            self.ln(1)
        self.ln(1)

    def table_row(self, index, name, barcode, type, depth, bold=False):
        if bold:
            self.set_font(self.font, style="B", size=11)
        else:
            self.set_font(self.font, size=11)
        self.cell(10, 10, str(index))
        self.cell(60, 10, name)
        self.cell(40, 10, barcode)
        self.cell(35, 10, type)
        self.cell(0, 10, str(depth))
        self.ln(6)


class Report(FPDF, HTMLMixin):
    def __init__(self, title="Report", font="Arial"):
        self.core_fonts_encoding = "UTF-8"
        self.title = title
        self.font = font
        super().__init__()

    def header(self):
        self.set_font(family=self.font, size=8)
        self.set_text_color(r=189, g=189, b=189)
        self.cell(0, 10, "COMPLETE REPORT", align="L")
        self.cell(0, 10, "Deep Sequencing Facility @ MPI-IE, Freiburg", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)  # Position at 1.5 cm from bottom
        self.set_font(self.font, size=8)  # Arial 8
        # Page number
        self.cell(0, 10, "Page " + str(self.page_no()) + " of {nb}", 0, 0, "C")

    def page_header(self, text):
        self.set_font(family=self.font, style="B", size=12)
        self.cell(0, 10, text)
        self.ln(14)

    def text_block(self, text, style="", size=11, multi=False):
        self.set_font(family=self.font, style=style, size=size)
        if multi:
            self.multi_cell(0, 6, text)
        else:
            self.cell(0, 10, text)
        self.ln(6)

    def generate_html_table(self, data):
        if len(data) == 0:
            return ""

        columns = list(data[0].keys())
        length = len(columns)

        thead = "".join(
            map(
                lambda c: f'<th width="{100 // length}%" align="left">{c}</th>',
                columns,
            )
        )

        tbody = []
        for item in data:
            row = "".join(map(lambda x: f"<td>{x}</td>", item.values()))
            tbody.append(f"<tr>{row}</tr>")
        tbody = "".join(tbody)

        html = """
        <font face="Arial" size="10">
             <table border="0" width="100%">
                <thead>
                    <tr>{}</tr>
                </thead>
                <tbody>{}</tbody>
            </table>
        </font>
        """.format(thead, tbody)
        html = html.replace("\n", "")

        return html


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    pagination_class = StandardResultsSetPagination

    filter_backends = (filters.SearchFilter,)
    search_fields = (
        "name",
        "description",
        "user__first_name",
        "user__last_name",
        "user__pi__name",
        "user__organization__name",
        "cost_unit__name",
    )

    def get_queryset(self, showAll=True):
        libraries_qs = Library.objects.all().only("status", "sequencing_depth")
        samples_qs = Sample.objects.all().only("status", "sequencing_depth")
        #   print(libraries_qs.values())

        queryset = (
            Request.objects.filter(archived=False)
            .select_related("user")
            .prefetch_related(
                Prefetch("libraries", queryset=libraries_qs),
                Prefetch("samples", queryset=samples_qs),
                "files",
            )
            .order_by("-create_time")
        )

        if not showAll:
            queryset = queryset.filter(sequenced=False)
        if self.request.user.is_staff:
            pass
        else:
            if not self.request.user.is_pi:
                queryset = queryset.filter(user=self.request.user)
            else:
                queryset = retrieve_group_items(self.request, queryset)

        return queryset

    def _relatable_requests(self, user):
        """Requests that `user` is allowed to link as related projects.

        Mirrors the visibility scoping of get_queryset: staff see every
        request, PI users see requests belonging to their PI group, and
        everyone else sees only their own. This is the single source of
        truth for both the search dropdown and the write-path validation.
        """
        queryset = Request.objects.filter(archived=False)
        if user.is_staff:
            return queryset
        if getattr(user, "is_pi", False) and user.pi:
            return queryset.filter(user__pi=user.pi)
        return queryset.filter(user=user)

    def _forbidden_related_requests(self, user, post_data, instance=None):
        """PKs in post_data['related_requests'] the user may not link.

        Returns a sorted list of the offending ids (empty when the payload
        is fully permitted). The search dropdown is only a UI convenience;
        this check is what actually prevents a crafted POST from linking to
        projects the user cannot see.
        """
        raw = post_data.get("related_requests") or []
        try:
            requested_ids = {int(pk) for pk in raw}
        except (TypeError, ValueError):
            return ["invalid"]
        if instance is not None:
            requested_ids.discard(instance.pk)
        if not requested_ids:
            return []
        allowed_ids = set(
            self._relatable_requests(user)
            .filter(pk__in=requested_ids)
            .values_list("pk", flat=True)
        )
        return sorted(requested_ids - allowed_ids)

    def list(self, request):
        """Get the list of requests."""

        showAll = False
        if request.GET.get("showAll") == "True":
            showAll = True

        queryset = self.filter_queryset(self.get_queryset(showAll))

        try:
            page = self.paginate_queryset(queryset)
        except NotFound:
            page = None

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    def create(self, request):
        """Create a request."""
        post_data = self._get_post_data(request)
        post_data.update({"user": request.user.pk})

        forbidden = self._forbidden_related_requests(request.user, post_data)
        if forbidden:
            return Response(
                {
                    "success": False,
                    "message": "Invalid payload.",
                    "errors": {
                        "related_requests": [
                            "You are not allowed to link to these projects: "
                            + ", ".join(str(pk) for pk in forbidden)
                        ]
                    },
                },
                400,
            )

        serializer = self.serializer_class(data=post_data)

        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "pk": serializer.data["pk"]}, 201)

        else:
            return Response(
                {
                    "success": False,
                    "message": "Invalid payload.",
                    "errors": serializer.errors,
                },
                400,
            )

    @action(methods=["post"], detail=True)
    def edit(self, request, pk=None):
        """Update request with a given id."""
        instance = self.get_object()
        post_data = self._get_post_data(request)

        if request.user.is_staff and post_data.get("user"):
            # Allow staff to reassign a request to another user.
            get_object_or_404(User, pk=post_data["user"])
        else:
            post_data["user"] = instance.user.pk

        forbidden = self._forbidden_related_requests(request.user, post_data, instance)
        if forbidden:
            return Response(
                {
                    "success": False,
                    "message": "Invalid payload.",
                    "errors": {
                        "related_requests": [
                            "You are not allowed to link to these projects: "
                            + ", ".join(str(pk) for pk in forbidden)
                        ]
                    },
                },
                400,
            )

        serializer = self.get_serializer(data=post_data, instance=instance)

        if serializer.is_valid():
            instance = serializer.save()
            if request.user.is_staff and post_data.get("user"):
                new_user = User.objects.get(pk=post_data["user"])
                if instance.user_id != new_user.pk:
                    instance.user = new_user
                new_name = f"{instance.id}_{new_user.last_name}"
                if new_user.pi:
                    new_name += f"_{new_user.pi.name}"
                instance.name = new_name
                instance.save(update_fields=["name"])
            return Response(
                {
                    "success": True,
                    "name": instance.name,
                    "user": instance.user.pk,
                }
            )

        else:
            return Response(
                {
                    "success": False,
                    "message": "Invalid payload.",
                    "errors": serializer.errors,
                },
                400,
            )

    @action(methods=["post"], detail=True)
    def samples_submitted(self, request, pk=None):
        instance = self.get_object()
        post_data = self._get_post_data(request)
        instance.samples_submitted = post_data["result"]
        instance.save(update_fields=["samples_submitted"])
        return Response({"success": True})

    @action(methods=["get"], detail=True)
    def get_records(self, request, pk=None):
        """Get the list of record's submitted libraries and samples."""
        libraries_qs = Library.objects.all().only(
            "name",
            "barcode",
        )
        samples_qs = Sample.objects.all().only(
            "name",
            "barcode",
            "is_converted",
        )

        try:
            instance = (
                Request.objects.filter(archived=False, pk=pk)
                .prefetch_related(
                    Prefetch("libraries", queryset=libraries_qs),
                    Prefetch("samples", queryset=samples_qs),
                )
                .only("libraries", "samples")
                .first()
            )

            data = [
                {
                    "pk": obj.pk,
                    "name": obj.name,
                    "barcode": obj.barcode,
                    "record_type": obj.__class__.__name__,
                    "is_converted": (
                        True
                        if hasattr(obj, "is_converted") and obj.is_converted
                        else False
                    ),
                }
                for obj in instance.records
            ]

            data = sorted(data, key=lambda x: x["barcode"][3:])
            Res = Response(data)

        except AttributeError as e:
            Res = Response({"success": False, "message": f"{pk} not found!"}, 400)
        return Res

    @action(methods=["get"], detail=True)
    def get_protocol(self, request, pk=None):
        """For example, to poll IDs of Nanopore's Sequencing Kits"""
        instance = LibraryProtocol(id=pk)
        serializer = LibraryProtocolSerializer(instance)
        return Response(serializer.data)

    @action(methods=["get"], detail=True)
    def get_contact_details(self, request, pk=None):
        """Get the user contact details."""
        users_qs = User.objects.all()
        data = (
            Request.objects.filter(pk=pk)
            .prefetch_related(Prefetch("user", queryset=users_qs))
            .only("user")
            .first()
        )
        serializer = UserSerializer(data.user)
        return Response(serializer.data)

    @action(methods=["get"], detail=False, permission_classes=[IsAdminUser])
    def search_users(self, request):
        """Search for active users for staff request reassignment."""
        query = request.query_params.get("query", "").strip()
        users = User.objects.filter(is_active=True)
        if query:
            exact_filter = (
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(pi__name__icontains=query)
                | Q(organization__name__icontains=query)
            )
            token_filter = Q()
            for term in query.split():
                token_filter &= (
                    Q(first_name__icontains=term)
                    | Q(last_name__icontains=term)
                    | Q(email__icontains=term)
                    | Q(pi__name__icontains=term)
                    | Q(organization__name__icontains=term)
                )
            users = users.filter(exact_filter | token_filter)
        users = users.order_by("last_name", "first_name").select_related("pi")
        data = [
            {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "pi_name": user.pi.name if user.pi else "",
            }
            for user in users
        ]
        return Response(data)

    @action(methods=["get"], detail=False)
    def search_related_requests(self, request):
        """Search requests by ID/name for related project selection."""
        query = request.query_params.get("query", "").strip()
        exclude_request_id = request.query_params.get("exclude_request_id", "").strip()
        ids_raw = request.query_params.get("ids", "").strip()

        requests_qs = self._relatable_requests(request.user).select_related("user")

        if ids_raw:
            ids = [
                int(value)
                for value in ids_raw.split(",")
                if str(value).strip().isdigit()
            ]
            if not ids:
                return Response([])
            requests_qs = requests_qs.filter(id__in=ids)
        elif query:
            request_filter = Q(name__icontains=query)
            if query.isdigit():
                request_filter |= Q(id=int(query))
            requests_qs = requests_qs.filter(request_filter)
        else:
            return Response([])

        if exclude_request_id.isdigit():
            requests_qs = requests_qs.exclude(id=int(exclude_request_id))

        results = requests_qs.order_by("-id")[:30]
        data = [
            {
                "id": req.pk,
                "name": req.name,
                "owner": req.user.full_name if req.user else "",
            }
            for req in results
        ]
        return Response(data)

    @action(methods=["get"], detail=True)
    def get_files(self, request, pk=None):
        """Get the list of attached files for a request with a given id."""
        instance = self.get_object()
        files = instance.files.all().order_by("name")
        serializer = RequestFileSerializer(files, many=True)
        return Response(serializer.data)

    @action(
        methods=["post"],
        detail=False,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def upload_files(self, request):
        file_ids = []
        files = request.FILES.getlist("files")

        if not files:
            return JsonResponse(
                {"success": False, "message": "No files provided."}, status=400
            )

        raw_file_types = request.POST.get("file_types")
        if raw_file_types is not None:
            try:
                file_types = json.loads(raw_file_types)
            except (TypeError, json.JSONDecodeError):
                file_types = None
        else:
            file_types = None

        if (
            not isinstance(file_types, list)
            or len(file_types) != len(files)
            or not all(is_valid_file_type(value) for value in file_types)
        ):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Select a valid file type for every file.",
                },
                status=400,
            )

        for file, file_type in zip(files, file_types, strict=True):
            f = FileRequest(name=file.name, file=file, file_type=file_type)
            f.save()
            file_ids.append(f.id)

        return JsonResponse({"success": True, "fileIds": file_ids})

    @action(methods=["get"], detail=False)
    def get_files_after_upload(self, request):
        file_ids = json.loads(request.query_params.get("file_ids", "[]"))
        error = ""
        data = []

        try:
            files = [f for f in FileRequest.objects.all() if f.id in file_ids]

            data = [
                {
                    "id": file.id,
                    "name": file.name,
                    "size": file.file.size,
                    "path": settings.MEDIA_URL + file.file.name,
                    "file_type": file.file_type,
                }
                for file in files
            ]

        except Exception as e:
            error = "Could not get the attached files."
            logger.exception(e)

        return JsonResponse(
            {
                "success": not error,
                "error": error,
                "data": data,
            }
        )

    @action(methods=["get"], detail=False)
    def download_RELACS_Pellets_Abs_form(self, request):
        file_path = os.path.join(
            settings.STATIC_ROOT,
            "docs/RELACS_submission_form.xlsx",
        )

        with open(file_path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response["Content-Disposition"] = "inline; filename=" + os.path.basename(
                file_path
            )
            return response

    @action(methods=["get"], detail=True)
    def download_deep_sequencing_request(self, request, pk=None):  # pragma: no cover
        """Generate a deep sequencing request form in PDF."""
        instance = self.get_object()
        user = instance.user
        organization = user.organization.name if user.organization else ""
        cost_unit = instance.cost_unit.name if instance.cost_unit else ""
        objects = list(
            itertools.chain(
                instance.samples.all(),
                instance.libraries.all(),
            )
        )
        records = [
            {
                "name": obj.name,
                "type": obj.__class__.__name__,
                "barcode": obj.barcode,
                "depth": obj.sequencing_depth,
            }
            for obj in objects
        ]
        records = sorted(records, key=lambda x: x["barcode"][3:])

        declaration_general = "None of the samples listed below are potentially infectious. The listed samples can be handled in an S1 laboratory (BioSafety Level 1) without any safety concerns."

        declaration_gmo = [
            (
                "  Non-GMO samples. Samples listed below do not fall under GenTG regulation (naked DNA, Sequencing libraries, RNA, proteins or metabolites, fixed or lysed cells, etc.). No additional documentation is required."
            ),
            (
                '  GMO samples of BioSafety Level 1 (BSL 1). Samples listed below fall under GenTG regulation. Additional documentation is required: an electronic copy of "Formblatt S1" (in "white" folder) in editable format is provided to the Deep Sequencing Facility BEFORE bringing S1 GMO to the facility (e.g. upload "Formblatt S1" via Parkour to your Request).'
            ),
            (
                "  GMO samples of BioSafety Level 2 (BSL 2). Not possible to be processed in the Deep Sequencing Facility."
            ),
        ]

        pdf = PDF("Deep Sequencing Request")
        pdf.add_font(
            "glyphicons",
            "",
            "/usr/src/app/static/fonts/glyphicons-halflings-regular.ttf",
            uni=True,
        )
        pdf.set_draw_color(217, 217, 217)
        pdf.alias_nb_pages()
        pdf.add_page()

        # Deep Sequencing Request info
        pdf.info_row("Request Name", instance.name)
        pdf.info_row("Date", instance.create_time.strftime("%d.%m.%Y"))
        pdf.info_row("User", user.full_name)
        pdf.info_row("Phone", user.phone if user.phone else "")
        pdf.info_row("Email", user.email)
        pdf.info_row("Organization", organization)
        pdf.info_row("Cost Unit", cost_unit)
        pdf.multi_info_row("Declaration", declaration_general)
        pdf.multi_checkbox_row("GMO Samples", declaration_gmo)
        try:
            pdf.multi_info_row("Description", instance.description)
        except FPDFUnicodeEncodingException:
            pdf.multi_info_row("Description", "ERROR: Character-set outside UTF-8.")
        # except:
        # pdf.multi_info_row(f"Description", "ERROR: {Exception}")

        y = pdf.get_y()
        pdf.line(pdf.l_margin + 1, y, pdf.w - pdf.r_margin - 1, y)

        # List of libraries/samples
        heading = "List of libraries/samples to be submitted for sequencing"
        pdf.ln(5)
        pdf.cell(0, 10, heading, align="C")
        pdf.ln(10)

        pdf.table_row("#", "Name", "Barcode", "Type", "Sequencing Depth (M)", True)

        for i, record in enumerate(records):
            pdf.table_row(
                i + 1,
                record["name"],
                record["barcode"],
                record["type"],
                record["depth"],
            )

        pdf.ln(10)
        y = pdf.get_y()
        pdf.line(pdf.l_margin + 1, y, pdf.w - pdf.r_margin - 1, y)
        pdf.ln(30)

        # Ensure there is enough space for the signature
        if pdf.get_y() > 265:
            pdf.add_page()
            pdf.ln(20)

        # Signature
        pdf.set_draw_color(0, 0, 0)
        y = pdf.get_y()
        x1_date = pdf.w / 2
        x2_date = x1_date + 45
        x1_signature = x2_date + 5
        x2_signature = pdf.w - pdf.r_margin - 1
        pdf.line(x1_date, y, x2_date, y)
        pdf.line(x1_signature, y, x2_signature, y)

        pdf.set_x(x1_date + (x2_date - x1_date) / 2 - 6)
        pdf.cell(12, 10, "(Date)")
        pdf.set_x(x1_signature + 2)
        pdf.cell(0, 10, "(Principal Investigator)")

        # Generate response
        request_name = (
            normalize("NFKD", instance.name).encode("ASCII", "ignore").decode("utf-8")
        )
        f_name = request_name + "_Deep_Sequencing_Request.pdf"
        response = HttpResponse(bytes(pdf.output()), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="%s"' % f_name

        return response

    @action(
        methods=["post"],
        detail=True,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def upload_deep_sequencing_request(self, request, pk=None):
        """
        Upload a deep sequencing request with the PI's signature and
        change request's libraries' and samples' statuses to 1.
        """
        instance = self.get_object()

        if not any(request.FILES):
            return JsonResponse(
                {"success": False, "message": "File is missing."}, status=400
            )

        instance.deep_seq_request = request.FILES.get("file")
        instance.save()

        file_name = instance.deep_seq_request.name.split("/")[-1]
        file_path = settings.MEDIA_URL + instance.deep_seq_request.name

        instance.libraries.all().update(status=1)
        instance.samples.all().update(status=1)

        return JsonResponse({"success": True, "name": file_name, "path": file_path})

    @action(methods=["post"], detail=True)
    def solicit_approval(self, request, pk=None):  # pragma: no cover
        """Send an email to the PI."""
        error = ""
        instance = self.get_object()
        subject = f"[ {settings.INSTANCE_NAME} | pending approval ] "
        subject += request.data.get("subject", "")
        message = request.data.get("message", "")
        include_records = json.loads(request.POST.get("include_records", "true"))
        records = []
        try:
            if instance.user.pi.archived:
                raise ValueError(
                    "PI: "
                    + instance.user.pi.name
                    + ", is no longer enrolled. Please contact an admin."
                )
            elif instance.user.pi.email == "Unset":
                raise ValueError(
                    "PI: "
                    + instance.user.pi.name
                    + ", has no e-mail address assigned. Please contact an admin."
                )
            records = list(instance.libraries.all()) + list(instance.samples.all())
            for r in records:
                if r.status != 0:
                    raise ValueError("Not all records have status of zero.")
            records = sorted(records, key=lambda x: x.barcode[3:])
            if not include_records:
                records = []
            instance.token = get_random_string(30)
            instance.save(update_fields=["token"])
            url_scheme = request.is_secure() and "https" or "http"
            url_domain = get_current_site(request).domain
            logo_url = (
                f"{url_scheme}://{url_domain}{settings.STATIC_URL}"
                "main-hub/resources/images/logo.png"
            )
            url_query = urlencode({"token": instance.token})
            send_mail(
                subject=subject,
                message="",
                html_message=render_to_string(
                    "approval.html",
                    {
                        "full_name": instance.user.full_name,
                        "pi_name": instance.user.pi.name,
                        "message": message,
                        "token_url": f"{url_scheme}://{url_domain}/api/approve/this/?pk={instance.id}&{url_query}",
                        "logo_url": logo_url,
                        "records": records,
                        "instance_title": settings.INSTANCE_TITLE,
                    },
                ),
                from_email=settings.SERVER_EMAIL,
                recipient_list=_recipient_list_with_sender_copy(instance.user.pi.email),
            )
        except Exception as e:
            error = str(e)
            logger.exception(e)
        return JsonResponse({"success": not error, "error": error})

    @action(methods=["post"], detail=True, permission_classes=[IsAdminUser])
    def send_email(self, request, pk=None):  # pragma: no cover
        """Send an email to the user."""
        error = ""

        instance = self.get_object()
        subject = request.data.get("subject", "")
        message = request.data.get("message", "")
        include_failed_records = json.loads(
            request.POST.get("include_failed_records", "false")
        )
        records = []

        try:
            if subject == "" or message == "":
                raise ValueError("Email subject and/or message is missing.")

            if include_failed_records:
                records = list(instance.libraries.filter(status=-1)) + list(
                    instance.samples.filter(status=-1)
                )
                records = sorted(records, key=lambda x: x.barcode[3:])

            send_mail(
                subject=f"[ {settings.INSTANCE_NAME} | new message ] " + subject,
                message="",
                html_message=render_to_string(
                    "email.html",
                    {
                        "full_name": instance.user.full_name,
                        "message": message,
                        "records": records,
                        "instance_title": settings.INSTANCE_TITLE,
                        "logo_url": request.build_absolute_uri(
                            f"{settings.STATIC_URL}main-hub/resources/images/logo.png"
                        ),
                    },
                ),
                from_email=settings.SERVER_EMAIL,
                recipient_list=_recipient_list_with_sender_copy(instance.user.email),
            )

        except Exception as e:
            error = str(e)
            logger.exception(e)

        return JsonResponse({"success": not error, "error": error})

    @action(methods=["get"], detail=True)
    def get_filepaths(self, request, *args, **kwargs):
        filepaths = self.get_object().filepaths
        return JsonResponse({"success": True, "filepaths": filepaths})

    @action(methods=["post"], detail=True, permission_classes=[IsAdminUser])
    def put_filepaths(self, request, pk=None):
        instance = self.get_object()
        entry = dict(request.data)
        existing = instance.filepaths
        if isinstance(existing, dict):
            # legacy single-entry shape from before filepaths became a list
            existing = [existing] if any(existing.values()) else []
        # Match on "data" (the release path) so a later call - e.g. an async
        # checksum worker posting just {"data": ..., "md5": ...} - updates
        # the existing entry in place instead of accumulating duplicates.
        match = next(
            (
                e
                for e in existing
                if e.get("data") and e.get("data") == entry.get("data")
            ),
            None,
        )
        if match is not None:
            match.update(entry)
        elif entry not in existing:
            existing = existing + [entry]
        instance.filepaths = existing
        records = list(instance.libraries.all()) + list(instance.samples.all())
        for r in records:
            # 'Sequencing' -> 'Delivered'
            if r.status == 5:
                r.status += 1
                r.save()
        instance.save(update_fields=["filepaths"])
        return Response({"success": True})

    @action(methods=["post"], detail=True)
    def put_metapaths(self, request, pk=None):
        instance = self.get_object()
        instance.metapaths = request.data
        instance.save(update_fields=["metapaths"])
        return Response({"success": True})

    @action(methods=["get"], detail=True, permission_classes=[IsAdminUser])
    def get_flowcell(self, request, *args, **kwargs):
        instance = self.get_object()

        def get_flowcell_from_record(record, instance=instance):
            finalized = len(instance.statuses) == sum(
                [x >= 5 or x < 0 for x in instance.statuses]
            )
            if not finalized:
                value = ["Sequencing incomplete"]
            else:
                fcids = []
                for pool in record.pool.all():
                    for lane in pool.lane_set.all():
                        for flowcell in lane.flowcell.all():
                            fcids.append(flowcell)
                value = [f.flowcell_id for f in fcids]
            return json.dumps(value)

        records = list(instance.libraries.all()) + list(instance.samples.all())
        flowpaths = dict.fromkeys([r.barcode for r in records])
        for r in records:
            flowpaths[r.barcode] = get_flowcell_from_record(r)
        return JsonResponse({"flowpaths": flowpaths})

    @action(methods=["get"], detail=True, permission_classes=[IsAdminUser])
    def get_poolpaths(self, request, *args, **kwargs):
        instance = self.get_object()
        records = list(instance.libraries.all()) + list(instance.samples.all())
        poolpaths = dict.fromkeys([r.barcode for r in records])
        for r in records:
            poolpaths[r.barcode] = [p.name for p in list(r.pool.all())]
        return JsonResponse({"success": True, "poolpaths": poolpaths})

    def _get_post_data(self, request):
        post_data = {}
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            post_data = request.data.get("data", {})
            if isinstance(post_data, str):
                post_data = json.loads(post_data)
        else:
            post_data = json.loads(request.data.get("data", "{}"))
        return post_data


@login_required
def export_request(request):
    if request.method == "POST":
        primary_key = request.POST["project-id"]
        file_format = request.POST["file-format"]
        req = get_object_or_404(Request, id=primary_key)
        if not request.user.is_staff and req.user != request.user:
            raise PermissionDenied()
        dataset = Dataset()
        dataset.headers = (
            "id",
            "name",
            "barcode",
            "nucleic_acid_type",  # samples
            "library_protocol",
            "library_type",
            "concentration",
            "mean_fragment_size",  # libraries
            "index_type",  # libraries
            "index_reads",  # libraries
            "index_i7",  # libraries
            "index_i5",  # libraries
            "read_length",
            "sequencing_depth",
            "organism",
            "comments",
        )

        def get_concentration_value(record):
            for attr in (
                "measured_value",
                "measured_value_facility",
                "concentration_library",
            ):
                if hasattr(record, attr):
                    value = getattr(record, attr)
                    if value is not None and value != "":
                        return value
            return ""

        records = req.records
        for r in records:
            r_type = r.__class__.__name__
            if r_type == "Sample":
                dataset.append(
                    (
                        "_",  # id
                        r.name,
                        "_",  # barcode
                        r.nucleic_acid_type,
                        r.library_protocol,
                        r.library_type,
                        get_concentration_value(r),
                        "_",  # mean_fragment_size
                        "_",  # index_type
                        "_",  # index_reads
                        "_",  # index_i7
                        "_",  # index_i5
                        r.read_length,
                        r.sequencing_depth,
                        r.organism,
                        r.comments,
                    )
                )
            elif r_type == "Library":
                dataset.append(
                    (
                        "_",  # id
                        r.name,
                        "_",  # barcode
                        "_",  # nucleic_acid_type
                        r.library_protocol,
                        r.library_type,
                        get_concentration_value(r),
                        r.mean_fragment_size,
                        r.index_type,
                        r.index_reads,
                        r.index_i7,
                        r.index_i5,
                        r.read_length,
                        r.sequencing_depth,
                        r.organism,
                        r.comments,
                    )
                )
            else:
                raise RuntimeError(f"What's {r.barcode} with {r_type}?!")

        if file_format == "CSV":
            response = HttpResponse(dataset.csv, content_type="text/csv")
            response["Content-Disposition"] = (
                'attachment; filename="exported_project_' + str(primary_key) + '.csv"'
            )
            return response

        elif file_format == "JSON":
            return render(
                request, "export.html", {"errors": "JSON import not implemented yet"}
            )

        else:
            raise ValueError(f"Invalid file_format: {file_format}")

    return render(request, "export.html")


# TODO: what about other fields from Libraries or Samples? like status, BarcodeCounter, ...
@login_required
def import_request(request):
    if request.method == "POST":
        file_format = request.POST["file-format"]
        new_file = request.FILES["importData"]

        if new_file.size > 5 * 1024 * 1024:  # 5 MB limit
            return render(
                request, "import.html", {"errors": "File size exceeds 5 MB limit"}
            )

        if file_format == "CSV":
            try:
                with transaction.atomic():
                    new_request = Request.objects.create(user=request.user)
                    csv_file = StringIO(new_file.read().decode("utf-8"))
                    csv_reader = csv.DictReader(csv_file)

                    samples = []
                    libraries = []

                    for row in csv_reader:
                        record_type = row.get("record_type", "").upper()

                        if record_type == "S":
                            sample = Sample.objects.create(
                                name=row.get("name"),
                                # Add other Sample-specific fields here
                            )
                            samples.append(sample)
                        elif record_type == "L":
                            library = Library.objects.create(
                                name=row.get("name"),
                                # Add other Library-specific fields here
                            )
                            libraries.append(library)
                        else:
                            raise ValueError(f"Invalid record_type: {record_type}")

                    # Add the samples and libraries to the request
                    new_request.samples.add(*samples)
                    new_request.libraries.add(*libraries)

                return render(request, "import.html", {"success": True})

            except Exception as e:
                return render(
                    request,
                    "import.html",
                    {"errors": f"Error processing CSV: {str(e)}"},
                )

        elif file_format == "JSON":
            return render(
                request, "import.html", {"errors": "JSON import not implemented yet"}
            )

    return render(request, "import.html")


class ApproveViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = RequestSerializer
    queryset = Request.objects.all().filter(id=0)

    @action(methods=["get"], detail=False)
    def this(self, request, *args, **kwargs):  # pragma: no cover
        """Process token sent to PI."""
        error = ""
        try:
            token = request.query_params.get("token")
            pk = request.query_params.get("pk")
            instance = list(Request.objects.filter(id=pk))[0]
            if not all(s == 0 for s in instance.statuses):
                raise ValueError(f"Not all statuses are zero: {instance.statuses}")
            if token == instance.token:
                library_ids = list(instance.libraries.values_list("id", flat=True))
                sample_ids = list(instance.samples.values_list("id", flat=True))
                with transaction.atomic():
                    instance.libraries.all().update(status=1)
                    instance.samples.all().update(status=1)
                    instance.token = None
                    instance.approval = {
                        "TIMESTAMP": dateformat.format(timezone.now(), "c"),
                        "TOKEN": token,
                        "REMOTE_ADDR": request.META.get("REMOTE_ADDR"),
                        "REMOTE_PORT": request.META.get("REMOTE_PORT"),
                        "HTTP_USER_AGENT": request.headers.get("user-agent"),
                        "HTTP_ACCEPT": request.headers.get("accept"),
                        "HTTP_ACCEPT_ENCODING": request.headers.get("accept-encoding"),
                        "HTTP_ACCEPT_LANGUAGE": request.headers.get("accept-language"),
                        "HTTP_X_FORWARDED_FOR": request.headers.get("x-forwarded-for"),
                        "HTTP_X_REAL_IP": request.headers.get("x-real-ip"),
                    }
                    instance.save(update_fields=["token", "approval"])
                refresh_batched(library_ids=library_ids, sample_ids=sample_ids)
            else:
                raise ValueError(f"Token mismatch.")
        except Exception as e:
            error = str(e)
            logger.exception(e)
            return JsonResponse({"success": not error, "error": error})
        send_mail(
            subject=f"[ {settings.INSTANCE_NAME} | request approved ] {instance.name}",
            message="",
            html_message=render_to_string(
                "approved.html",
                {
                    "full_name": instance.user.full_name,
                    "pi_name": instance.user.pi.name,
                    "instance_title": settings.INSTANCE_TITLE,
                    "logo_url": request.build_absolute_uri(
                        f"{settings.STATIC_URL}main-hub/resources/images/logo.png"
                    ),
                },
            ),
            from_email=settings.SERVER_EMAIL,
            recipient_list=_recipient_list_with_sender_copy(
                instance.user.email, instance.user.pi.email
            ),
        )
        return HttpResponseRedirect("/danke")
