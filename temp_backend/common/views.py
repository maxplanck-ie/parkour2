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
from constance import config
from request.models import Request
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import CostUnit, Organization, Duty
from .serializers import (CostUnitSerializer,
                          PrincipalInvestigatorSerializer,
                          OrganizationSerializer,
                          BioinformaticianSerializer,
                          DutySerializer,
                          UserSerializer)

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
                    "can_solicite_paperless_approval": user.can_solicite_paperless_approval,
                }
            ),
            "DOCUMENTATION_URL": config.DOCUMENTATION_URL,
            "GRID_INTRO_VIDEO_URL": config.GRID_INTRO_VIDEO_URL,
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
    elif request.user.member_of_bcf:
        data += [
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
        allow_download = Request.objects.filter(
            Q(user=request.user) | Q(pi=request.user) | Q(bioinformatician=request.user),
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
                return queryset.filter(archived=False)
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

            choices = list(User.objects.filter(Q(is_bioinformatician=True, is_active=True) |
                                               Q(is_bioinformatician=True, email__endswith='@example.com') |
                                               Q(id__in=[seq_request_user_id, seq_request_bioinformatician_id, self.request.user.id]))
                                       .order_by('last_name').distinct())

            if seq_request_user_id:
                # Highlight the sequencing request user
                for u in [u for u in choices if u.id == int(seq_request_user_id)]:
                    u.last_name += ' (request user)'

            # Highlight the http request user, i.e. themselves
            for u in [u for u in choices if u.id == self.request.user.id]:
                u.last_name = u.last_name.replace(' (request user)', '') + ' (you)'

            # Put system bioinformatician at the end of choices
            system_bioinformaticians = [u for u in choices if u.email.lower().endswith('@example.com')]
            choices = [u for u in choices if not u.email.lower().endswith('@example.com')] + system_bioinformaticians

            return choices

        except:

            return User.objects.filter(is_bioinformatician=True)


class StaffMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """Get the list of members of GCF/Staff"""

    serializer_class = BioinformaticianSerializer

    def get_queryset(self):

        try:

            request_handler = int(self.request.query_params.get("request_handler", 0))
            return User.objects.filter(Q(groups__name=settings.DEEPSEQ, is_active=True, is_staff=True) |
                                       Q(id=request_handler)).order_by('last_name').distinct()

        except:

            return User.objects.filter(groups__name=settings.DEEPSEQ)


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

    def get(self, request, *args, **kwargs):
        serializer = DutySerializer(self.queryset, many=True)
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
