import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination

from .models import CostUnit, PrincipalInvestigator
from .serializers import CostUnitSerializer, PrincipalInvestigatorSerializer

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


class CostUnitsViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of cost units."""

    serializer_class = CostUnitSerializer

    def get_queryset(self):
        pi_id = self.request.query_params.get("principal_investigator_id", None)
        try:
            pi = get_object_or_404(PrincipalInvestigator, id=pi_id)
            queryset = pi.costunit_set.all().order_by("name")
            return queryset.order_by("name")
        except Exception:
            return CostUnit.objects.all()


class PrincipalInvestigatorViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of Principal Investigators."""

    serializer_class = PrincipalInvestigatorSerializer

    def get_queryset(self):
        queryset = PrincipalInvestigator.objects.order_by("name")
        user_id = self.request.query_params.get("user_id", None)
        try:
            user = get_object_or_404(User, id=user_id)
            pi_ids = user.pi.all().values_list('id', flat=True)
            queryset = queryset.filter(pk__in=pi_ids)
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
