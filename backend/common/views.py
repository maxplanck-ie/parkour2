import json
from mimetypes import guess_type
import os
from os.path import basename
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse, FileResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from request.models import Request
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    AttachmentFileType,
    CostUnit,
    Duty,
    LoadFlowcellsTemplate,
    LibrariesAndSamplesTemplate,
    IncomingLibrariesSamplesTemplate,
    LibraryPreparationTemplate,
    PoolingTemplate,
    RunStatisticsTemplate,
    SequencesStatisticsTemplate,
    InvoicingTemplate,
)
from .serializers import (
    AttachmentFileTypeSerializer,
    CostUnitSerializer,
    DutySerializer,
    UserSerializer,
    LoadFlowcellsTemplateSerializer,
    LibrariesAndSamplesTemplateSerializer,
    IncomingLibrariesSamplesTemplateSerializer,
    LibraryPreparationTemplateSerializer,
    PoolingTemplateSerializer,
    RunStatisticsTemplateSerializer,
    SequencesStatisticsTemplateSerializer,
    InvoicingTemplateSerializer,
)

User = get_user_model()
XLSX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
XLSM_MIME_TYPE = "application/vnd.ms-excel.sheet.macroEnabled.12"


def get_excel_content_type(file_name):
    return (
        XLSM_MIME_TYPE if str(file_name).lower().endswith(".xlsm") else XLSX_MIME_TYPE
    )


@login_required
def index(request):
    user = request.user
    return render(
        request,
        "index.html",
        {
            "DEBUG": settings.DEBUG,
            "USER": json.dumps(
                {
                    "id": user.pk,
                    "name": user.full_name,
                    "is_staff": user.is_staff,
                    "paperless_approval": user.paperless_approval,
                }
            ),
        },
    )


@login_required
def get_navigation_tree(request):
    """Get main NavigationTree."""

    data = [
        {
            "text": "Libraries & Samples",
            "iconCls": "x-fa fa-flask",
            "viewType": "libraries-vue",
            "leaf": True,
        },
    ]

    if request.user.is_staff:
        data += [
            {
                "text": "Incoming Libraries/Samples",
                "iconCls": "x-fa fa-arrow-down",
                "viewType": "incoming-libraries-vue",
                "leaf": True,
            },
            {
                "text": "Index Generator",
                "iconCls": "x-fa fa-cogs",
                "viewType": "index-generator-vue",
                "leaf": True,
            },
            {
                "text": "Preparation",
                "iconCls": "x-fa fa-table",
                "viewType": "library-preparation-vue",
                "leaf": True,
            },
            {
                "text": "Pooling",
                "iconCls": "x-fa fa-sort-amount-desc",
                "viewType": "pooling-vue",
                "leaf": True,
            },
            {
                "text": "Load Flowcells",
                "iconCls": "x-fa fa-level-down",
                "viewType": "flowcells-vue",
                "leaf": True,
            },
            {
                "text": "Invoicing",
                "iconCls": "x-fa fa-eur",
                "viewType": "invoicing-vue",
                "leaf": True,
            },
            {
                "text": "Usage",
                "iconCls": "x-fa fa-bar-chart",
                "viewType": "usage-vue",
                "leaf": True,
            },
            {
                "text": "Statistics",
                "iconCls": "x-fa fa-line-chart",
                "expanded": False,
                "children": [
                    {
                        "text": "Runs Statistics",
                        "viewType": "run-statistics-vue",
                        "leaf": True,
                    },
                    {
                        "text": "Sequenced Samples Statistics",
                        "viewType": "sequences-statistics-vue",
                        "leaf": True,
                    },
                ],
            },
        ]

    return JsonResponse({"text": ".", "children": data})


@login_required
def protected_media(request, *args, **kwargs):
    """Protected view for media files"""

    allow_download = False
    url_path = kwargs["url_path"]

    if request.user.is_staff:
        allow_download = True
    elif request.user.is_pi:
        # Master/ PI accounts should be able to access attachments
        allow_download = (
            request.user.pi
            == Request.objects.filter(
                Q(deep_seq_request=url_path) | Q(files__file=url_path), archived=False
            )[0].user.pi
        )
    else:
        allow_download = Request.objects.filter(
            Q(deep_seq_request=url_path) | Q(files__file=url_path),
            user=request.user,
            archived=False,
        ).exists()

    if allow_download:
        response = HttpResponse()

        # Set file type and encoding
        mimetype, encoding = guess_type(url_path)
        response["Content-Type"] = mimetype if mimetype else "application/octet-stream"
        if encoding:
            response["Content-Encoding"] = encoding

        # Set internal redirect to protected media
        response["X-Accel-Redirect"] = f"/protected_media/{url_path}"

        # Set file name
        file_name = basename(url_path)
        # Needed for file names that include special, non ascii, characters
        response["Content-Disposition"] = (
            f"attachment; filename*=utf-8''{quote(file_name)}"
        )

        return response

    raise Http404


class CostUnitsViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of cost units."""

    serializer_class = CostUnitSerializer

    def get_queryset(self):
        queryset = CostUnit.objects.order_by("name")
        user_id = self.request.query_params.get("user_id", None)
        try:
            user = get_object_or_404(User, id=user_id)
            cost_units = user.cost_unit.values_list("pk", flat=True)
            queryset = queryset.filter(pk__in=cost_units)
        except Exception:
            pass
        return queryset


class AttachmentFileTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Return file types that are available for attachment uploads."""

    serializer_class = AttachmentFileTypeSerializer
    queryset = AttachmentFileType.objects.filter(archived=False).order_by("name")


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100


class DutyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = DutySerializer
    queryset = Duty.objects.all().filter(archived=False).order_by("-start_date")

    @action(methods=["get"], detail=False)
    def responsibles(self, request, *args, **kwargs):
        qs = User.objects.filter(is_active=True)
        serializer = UserSerializer(
            [u for u in list(qs) if u.facility is not None], many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        today_var = timezone.now()
        start_date_var = request.query_params.get("start_date")
        end_date_var = request.query_params.get("end_date")
        ongoing_var = request.query_params.get("ongoing")
        upcoming_var = request.query_params.get("upcoming")
        queryset_var = self.queryset.filter()

        if str(ongoing_var).lower() in ["true", "t", "yes", "y", "1"]:
            queryset_var = self.queryset.filter(
                Q(start_date__lte=today_var, end_date__gte=today_var)
                | Q(start_date__lte=today_var, end_date__isnull=True)
            )
        elif str(upcoming_var).lower() in ["true", "t", "yes", "y", "1"]:
            queryset_var = self.queryset.filter(start_date__gte=today_var)
        elif start_date_var and end_date_var:
            queryset_var = self.queryset.filter(
                Q(start_date__gte=start_date_var, start_date__lte=end_date_var)
                | Q(start_date__gte=start_date_var, end_date__isnull=True)
            )

        serializer = DutySerializer(queryset_var, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = {
            "main_name": request.data.get("main_name"),
            "backup_name": request.data.get("backup_name"),
            "start_date": request.data.get("start_date"),
            "end_date": request.data.get("end_date"),
            "platform": request.data.get("platform"),
            "comment": request.data.get("comment"),
            "archived": request.data.get("archived"),
        }
        serializer = DutySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, duty_id, *args, **kwargs):
        duty_instance = self.get_object(duty_id)
        if not duty_instance:
            return Response(
                {"res": "Object with duty id does not exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = {
            "main_name": request.data.get("main_name"),
            "backup_name": request.data.get("backup_name"),
            "start_date": request.data.get("start_date"),
            "end_date": request.data.get("end_date"),
            "platform": request.data.get("platform"),
            "comment": request.data.get("comment"),
            "archived": request.data.get("archived"),
        }
        serializer = DutySerializer(instance=duty_instance, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, duty_id, *args, **kwargs):
    #     duty_instance = self.get_object(duty_id)
    #     if not duty_instance:
    #         return Response(
    #             {"res": "Object with duty id does not exists"},
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )
    #     duty_instance.delete()
    #     return Response({"res": "Object deleted!"}, status=status.HTTP_200_OK)


@login_required
def user_details(request):
    user = request.user
    data = {
        "DEBUG": settings.DEBUG,
        "INSTANCE_VERSION": settings.INSTANCE_VERSION,
        "USER": json.dumps(
            {
                "id": user.pk,
                "name": user.full_name,
                "is_staff": user.is_staff,
                "paperless_approval": user.paperless_approval,
            }
        ),
    }
    return JsonResponse(data)


def danke(request):
    return render(request, "danke.html")


class PasswordSetConfirmView(auth_views.PasswordResetConfirmView):
    """Same as the stock view, plus a "password changed" confirmation email."""

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        if user.email:
            send_mail(
                subject="[Parkour LIMS] Password Changed",
                message="",
                html_message=render_to_string(
                    "email/password_changed_email.html",
                    {
                        "user": user,
                        "domain": get_current_site(self.request).domain,
                        "logo_url": self.request.build_absolute_uri(
                            f"{settings.STATIC_URL}images/logo.png"
                        ),
                    },
                ),
                from_email=settings.SERVER_EMAIL,
                recipient_list=[user.email],
            )
        return response


class BaseTemplateViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAdminUser]

    model = None
    serializer_class = None

    def get_queryset(self):
        return self.model.objects.order_by("-uploaded_at")

    @action(detail=False, methods=["post"])
    def upload(self, request):
        """Upload a new XLSX or XLSM file (replaces old if exists)."""
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"success": False, "message": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not str(file.name).lower().endswith((".xlsx", ".xlsm")):
            return Response(
                {"success": False, "message": "Only XLSX and XLSM files are allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        old_template = self.model.objects.first()
        if old_template:
            old_template.file.delete()
            old_template.delete()
        template = self.model(name=file.name, file=file)
        template.save()
        serializer = self.get_serializer(template)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["delete"])
    def remove(self, request, pk=None):
        """Remove an XLSX or XLSM file."""
        template = self.get_object()
        template.file.delete()
        template.delete()
        return Response(
            {"success": True, "message": "File removed successfully."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Download an XLSX or XLSM file."""
        try:
            template = self.get_object()
            file_path = template.file.path
            if not os.path.exists(file_path):
                return Response({"error": "File not found"}, status=404)
            response = FileResponse(
                open(file_path, "rb"),
                content_type=get_excel_content_type(template.name),
            )
            response["Content-Disposition"] = f'attachment; filename="{template.name}"'
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class LibrariesAndSamplesTemplateViewSet(BaseTemplateViewSet):
    model = LibrariesAndSamplesTemplate
    serializer_class = LibrariesAndSamplesTemplateSerializer


class IncomingLibrariesSamplesTemplateViewSet(BaseTemplateViewSet):
    model = IncomingLibrariesSamplesTemplate
    serializer_class = IncomingLibrariesSamplesTemplateSerializer


class LibraryPreparationTemplateViewSet(BaseTemplateViewSet):
    model = LibraryPreparationTemplate
    serializer_class = LibraryPreparationTemplateSerializer


class PoolingTemplateViewSet(BaseTemplateViewSet):
    model = PoolingTemplate
    serializer_class = PoolingTemplateSerializer


class LoadFlowcellsTemplateViewSet(BaseTemplateViewSet):
    model = LoadFlowcellsTemplate
    serializer_class = LoadFlowcellsTemplateSerializer


class RunStatisticsTemplateViewSet(BaseTemplateViewSet):
    model = RunStatisticsTemplate
    serializer_class = RunStatisticsTemplateSerializer


class SequencesStatisticsTemplateViewSet(BaseTemplateViewSet):
    model = SequencesStatisticsTemplate
    serializer_class = SequencesStatisticsTemplateSerializer


class InvoicingTemplateViewSet(BaseTemplateViewSet):
    model = InvoicingTemplate
    serializer_class = InvoicingTemplateSerializer
