import statistics
from collections import Counter
from datetime import datetime

from common.utils import transliterate_name
from django.apps import apps
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

Request = apps.get_model("request", "Request")
AnalysisType = apps.get_model("library_sample_shared", "AnalysisType")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")
PrincipalInvestigator = apps.get_model("common", "PrincipalInvestigator")


def get_date_range(request, format):
    now = timezone.now()
    start = request.query_params.get("start", now)
    end = request.query_params.get("end", now)

    try:
        start = (
            timezone.datetime.strptime(start, format) if type(start) is str else start
        )
    except ValueError:
        start = now
    finally:
        start = start.replace(hour=0, minute=0)

    try:
        end = timezone.datetime.strptime(end, format) if type(end) is str else end
    except ValueError:
        end = now
    finally:
        end = end.replace(hour=23, minute=59)

    if start > end:
        start = end.replace(hour=0, minute=0)

    return (start, end)


class RecordsUsage(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")

        libraries = Library.objects.filter(
            request__isnull=False,
            create_time__gte=start,
            create_time__lte=end,
        ).only("id")

        samples = Sample.objects.filter(
            request__isnull=False,
            create_time__gte=start,
            create_time__lte=end,
        ).only("id")

        return Response(
            [
                {
                    "name": "Libraries",
                    "data": len(libraries),
                },
                {
                    "name": "Samples",
                    "data": len(samples),
                },
            ]
        )


class OrganizationsUsage(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")

        libraries_qs = Library.objects.only("id")
        samples_qs = Sample.objects.only("id")

        requests = (
            Request.objects.filter(archived=False)
            .select_related(
                "user",
                "user__organization",
            )
            .prefetch_related(
                Prefetch(
                    "libraries", queryset=libraries_qs, to_attr="fetched_libraries"
                ),
                Prefetch("samples", queryset=samples_qs, to_attr="fetched_samples"),
            )
            .filter(create_time__gte=start, create_time__lte=end)
            .only("id", "user", "libraries", "samples")
        )

        counts = {}
        for req in requests:
            organization = req.user.organization
            org_name = organization.name if organization else "None"
            if org_name not in counts.keys():
                counts[org_name] = {"libraries": 0, "samples": 0}
            counts[org_name]["libraries"] += len(req.fetched_libraries)
            counts[org_name]["samples"] += len(req.fetched_samples)

        data = [
            {"name": organization, "data": sum(count.values())}
            for organization, count in counts.items()
        ]

        return Response(data)


class PrincipalInvestigatorsUsage(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")

        libraries_qs = Library.objects.only("id")
        samples_qs = Sample.objects.only("id")

        requests = (
            Request.objects.filter(archived=False)
            .select_related(
                "user",
                "user__pi",
            )
            .prefetch_related(
                Prefetch(
                    "libraries", queryset=libraries_qs, to_attr="fetched_libraries"
                ),
                Prefetch("samples", queryset=samples_qs, to_attr="fetched_samples"),
            )
            .filter(create_time__gte=start, create_time__lte=end)
            .only("id", "user__pi__name", "libraries", "samples")
        )

        counts = {}
        for req in requests:
            pi = req.user.pi
            pi_name = pi.name if pi else "None"
            if pi_name not in counts.keys():
                counts[pi_name] = {"libraries": 0, "samples": 0}
            counts[pi_name]["libraries"] += len(req.fetched_libraries)
            counts[pi_name]["samples"] += len(req.fetched_samples)

        data = [
            {
                "name": pi,
                "data": sum(count.values()),
                "libraries": count["libraries"],
                "samples": count["samples"],
            }
            for pi, count in counts.items()
        ]

        data = sorted(data, key=lambda x: x["name"])
        return Response(data)


class AnalysisTypesUsage(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")

        libraries_qs = Library.objects.select_related("analysis_type").only(
            "id", "analysis_type__name"
        )
        samples_qs = Sample.objects.select_related("analysis_type").only(
            "id", "analysis_type__name"
        )

        requests = (
            Request.objects.filter(archived=False)
            .prefetch_related(
                Prefetch(
                    "libraries", queryset=libraries_qs, to_attr="fetched_libraries"
                ),
                Prefetch("samples", queryset=samples_qs, to_attr="fetched_samples"),
            )
            .filter(create_time__gte=start, create_time__lte=end)
            .only("id", "libraries", "samples")
        )

        counts = {}
        for req in requests:
            # Extract Library Types
            analysis_types = [x.analysis_type.name for x in req.fetched_libraries]
            sample_types = [x.analysis_type.name for x in req.fetched_samples]

            # Merge the counts
            library_cnt = {
                x[0]: {"libraries": x[1]} for x in Counter(analysis_types).items()
            }
            sample_cnt = {
                x[0]: {"samples": x[1]} for x in Counter(sample_types).items()
            }
            count = {
                k: {
                    **library_cnt.get(k, {"libraries": 0}),
                    **sample_cnt.get(k, {"samples": 0}),
                }
                for k in library_cnt.keys() | sample_cnt.keys()
            }

            for k, v in count.items():
                temp_dict = counts.get(k, {"libraries": 0, "samples": 0})
                temp_dict["libraries"] += v["libraries"]
                temp_dict["samples"] += v["samples"]
                counts[k] = temp_dict

        data = [
            {
                "name": analysis_type,
                "data": sum(count.values()),
                "libraries": count["libraries"],
                "samples": count["samples"],
            }
            for analysis_type, count in counts.items()
        ]

        data = sorted(data, key=lambda x: x["name"])
        return Response(data)


class TurnaroundTimeUsage(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")
        group_by = request.query_params.get("group_by", "pi")

        libraries_qs = Library.objects.select_related("analysis_type").only(
            "id", "analysis_type__name"
        )
        samples_qs = Sample.objects.select_related("analysis_type").only(
            "id", "analysis_type__name"
        )

        requests = (
            Request.objects.filter(
                archived=False,
                flowcell_loaded_at__isnull=False,
                flowcell_loaded_at__gte=start,
                flowcell_loaded_at__lte=end,
            )
            .select_related("user", "user__pi")
            .prefetch_related(
                Prefetch(
                    "libraries", queryset=libraries_qs, to_attr="fetched_libraries"
                ),
                Prefetch("samples", queryset=samples_qs, to_attr="fetched_samples"),
            )
            .only("id", "approval", "flowcell_loaded_at", "user__pi__name")
        )

        groups = {}
        for req in requests:
            timestamp = (req.approval or {}).get("TIMESTAMP")
            if not timestamp:
                continue
            try:
                approved_at = datetime.fromisoformat(timestamp)
            except (TypeError, ValueError):
                continue

            turnaround_days = (
                req.flowcell_loaded_at - approved_at
            ).total_seconds() / 86400
            if turnaround_days < 0:
                continue

            if group_by == "analysis_type":
                names = {x.analysis_type.name for x in req.fetched_libraries} | {
                    x.analysis_type.name for x in req.fetched_samples
                }
            else:
                pi = req.user.pi
                names = {pi.name if pi else "None"}

            for name in names:
                groups.setdefault(name, []).append(turnaround_days)

        data = []
        for name, values in groups.items():
            values.sort()
            if len(values) >= 2:
                q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
            else:
                q1 = q3 = values[0]

            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr
            inliers = [v for v in values if lower_fence <= v <= upper_fence]
            outliers = [v for v in values if v < lower_fence or v > upper_fence]

            data.append(
                {
                    "name": name,
                    "data": [
                        min(inliers) if inliers else values[0],
                        q1,
                        statistics.median(values),
                        q3,
                        max(inliers) if inliers else values[-1],
                    ],
                    "outliers": outliers,
                }
            )

        data = sorted(data, key=lambda x: x["name"])
        return Response(data)


class InternalPIsView(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        raw_organizations = request.query_params.get("organizations", "")
        organization_names = [
            name.strip() for name in raw_organizations.split(",") if name.strip()
        ]
        if not organization_names:
            return Response(
                {
                    "error": (
                        "Provide at least one comma separated organization name "
                        "via the 'organizations' query parameter."
                    )
                },
                status=400,
            )

        pis = (
            PrincipalInvestigator.objects.filter(
                archived=False, organization__name__in=organization_names
            )
            .values_list("name", "deliver_to")
            .distinct()
        )
        # Map the PI name, transliterated + lowercased the same way dissectBCL's
        # umlautDestroyer turns it into an on-disk folder token (accents/umlauts
        # stripped, spaces removed) -> IT delivery-directory override (or None
        # when the PI name already matches its /data directory). Using the raw
        # name here would never match an accented/spaced PI (e.g. "Cissé",
        # "AlHaj Abed") against the already-transliterated folder name dissectBCL
        # derives, silently routing them as external.
        return Response(
            {
                "pis": {
                    transliterate_name(name).lower(): (deliver_to or None)
                    for name, deliver_to in pis
                }
            }
        )
