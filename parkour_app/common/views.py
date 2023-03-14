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
from request.models import Request
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination

from .models import CostUnit
from .serializers import CostUnitSerializer

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
                "viewType": "incoming-libraries",
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
                "viewType": "preparation",
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
                "expanded": True,
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
    else:
        allow_download = Request.objects.filter(
            Q(deep_seq_request=url_path) | Q(files__file=url_path), user=request.user
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
        response[
            "Content-Disposition"
        ] = f"attachment; filename*=utf-8''{quote(file_name)}"

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
