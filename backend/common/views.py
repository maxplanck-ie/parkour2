import json
from mimetypes import guess_type
from os.path import basename
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from request.models import Request
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import CostUnit, Duty
from .serializers import CostUnitSerializer, DutySerializer, UserSerializer

User = get_user_model()


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
            "text": "Requests",
            "iconCls": "x-fa fa-file-text",
            "viewType": "requests",
            "leaf": True,
        },
        {
            "text": "Libraries & Samples",
            "iconCls": "x-fa fa-flask",
            "viewType": "libraries",
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
                "viewType": "index-generator",
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
                "viewType": "pooling",
                "leaf": True,
            },
            {
                "text": "Load Flowcells",
                "iconCls": "x-fa fa-level-down",
                "viewType": "flowcells",
                "leaf": True,
            },
            {
                "text": "Invoicing",
                "iconCls": "x-fa fa-eur",
                "viewType": "invoicing",
                "leaf": True,
            },
            {
                "text": "Usage",
                "iconCls": "x-fa fa-pie-chart",
                "viewType": "usage",
                "leaf": True,
            },
            {
                "text": "Statistics",
                "iconCls": "x-fa fa-line-chart",
                "expanded": False,
                "children": [
                    {
                        "text": "Runs",
                        "viewType": "run-statistics",
                        "leaf": True,
                    },
                    {
                        "text": "Sequences",
                        "viewType": "sequences-statistics",
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
