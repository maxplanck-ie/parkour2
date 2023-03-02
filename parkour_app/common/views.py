import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.http import HttpResponse, Http404
from request.models import Request
from mimetypes import guess_type
from os.path import basename
from urllib.parse import quote

from .models import CostUnit, Organization
from .serializers import (CostUnitSerializer,
                          PrincipalInvestigatorSerializer,
                          OrganizationSerializer,
                          BioinformaticianSerializer)

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
                    "member_of_bcf": user.member_of_bcf,
                    "is_bioinformatician": user.is_bioinformatician,
                    "is_pi": user.is_pi,
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

    if request.user.is_staff or request.user.member_of_bcf:
        allow_download = True
    else:
        allow_download = Request.objects.filter(Q(user=request.user) | Q(pi=request.user) | Q(bioinformatician=request.user),
                                                Q(deep_seq_request=url_path) | Q(files__file=url_path)) \
                                        .exists()

    if allow_download:

        response = HttpResponse()
        
        # Set file type and encoding
        mimetype, encoding = guess_type(url_path)
        response["Content-Type"] = mimetype if mimetype else 'application/octet-stream'
        if encoding: response["Content-Encoding"] = encoding
        
        # Set internal redirect to protected media
        response['X-Accel-Redirect'] = f"/protected_media/{url_path}"
        
        # Set file name
        file_name = basename(url_path)
        response["Content-Disposition"] = f"attachment; filename*=utf-8''{quote(file_name)}" # Needed for file names that include special, non ascii, characters 

        return response
    
    raise Http404


class CostUnitsViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of cost units."""

    serializer_class = CostUnitSerializer

    def get_queryset(self):
        pi_id = self.request.query_params.get("principal_investigator_id", None)
        if self.request.user.is_pi:
            pi_id = self.request.user.id
        try:
            pi = get_object_or_404(User, id=pi_id)
            queryset = pi.costunit_set.all().order_by("name")
            if self.request.user.is_staff or self.request.user.member_of_bcf:
                return queryset
            else:
                return queryset.filter(obsolete=settings.NON_OBSOLETE)
        except Exception:
            return CostUnit.objects.all() if self.request.user.is_staff or self.request.user.member_of_bcf else CostUnit.objects.none()


class PrincipalInvestigatorViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of Principal Investigators."""

    serializer_class = PrincipalInvestigatorSerializer

    def get_queryset(self):
        # If a seq request already exists, add the PI attached to it 
        # to the list of PIs shown in the PI drop-down box for said request
        # This is to account for those cases where a PI is not attached to
        # a User anymore and therefore would not otherwise be shown
        seq_request_pi_id = self.request.query_params.get("request_pi", None)
        seq_request_pi_id = seq_request_pi_id if seq_request_pi_id else None
        try:
            user = self.request.user
            if user.is_staff or user.member_of_bcf:
                qs =  User.objects.filter(Q(is_pi=True) | Q(id=seq_request_pi_id))
            elif user.is_pi:
                qs = User.objects.filter(id__in=[user.id, seq_request_pi_id])
            else:
                qs = User.objects.filter(id__in=list(user.pi.all().values_list('id', flat=True)) + [seq_request_pi_id])
            return qs.distinct().order_by("last_name")
        except Exception:
            return User.objects.none()


class BioinformaticianViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of Bioinformaticians"""

    serializer_class = BioinformaticianSerializer

    def get_queryset(self):

        try:

            seq_request_user_id = int(self.request.query_params.get("request_user", 0))
            seq_request_bioinformatician_id = int(self.request.query_params.get("request_bioinformatician", 0))

            #  Create or get external bioinformatician user
            external_bioinformatician, created = User.objects.get_or_create(email='external.bioinformatician@example.com',
                                                                            first_name='External',
                                                                            last_name='Bioinformatician',
                                                                            is_bioinformatician=True)
            # If external_bioinformatician is newly created, set it so
            # that it can't be used to log in
            if created:
                external_bioinformatician.is_active = False
                external_bioinformatician.set_unusable_password()
                external_bioinformatician.save()

            choices = list(User.objects.filter(Q(is_bioinformatician=True) |
                                               Q(id__in=[seq_request_user_id, seq_request_bioinformatician_id, self.request.user.id]))
                                       .distinct())

            # Prettify the full name of external_bioinformatician for the front end
            external_bioinformatician = [u for u in choices if u.id == external_bioinformatician.id][0]
            external_bioinformatician.last_name = "(add details to 'Description')"

            if seq_request_user_id:
                # Highlight the sequencing request user
                seq_request_user = [u for u in choices if u.id == int(seq_request_user_id)][0]
                seq_request_user.last_name += ' (request user)'

            # Highlight the http request user, i.e. themselves
            http_request_user = [u for u in choices if u.id == self.request.user.id][0]
            http_request_user.last_name = http_request_user.last_name.replace(' (request user)', '') + ' (you)'

            return sorted(choices, key=lambda u: u.last_name)

        except:

            return User.objects.filter(is_bioinformatician=True)


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of Principal Investigators."""

    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100
