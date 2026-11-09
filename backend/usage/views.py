import statistics
from collections import Counter

from common.utils import transliterate_name
from django.apps import apps
from django.db.models import Exists, OuterRef, Prefetch, Subquery
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

Request = apps.get_model("request", "Request")
AnalysisType = apps.get_model("library_sample_shared", "AnalysisType")
Library = apps.get_model("library", "Library")
Flowcell = apps.get_model("flowcell", "Flowcell")
Sample = apps.get_model("sample", "Sample")
PrincipalInvestigator = apps.get_model("common", "PrincipalInvestigator")
CompleteLibraryData = apps.get_model("library", "CompleteLibraryData")


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


def get_record_type(request):
    record_type = request.query_params.get("record_type", "all")
    return record_type if record_type in ("libraries", "samples") else "all"


def filter_requests_by_record_type(requests, record_type):
    """Keep only requests linked to at least one record of the selected kind."""
    if record_type == "libraries":
        return requests.filter(Exists(Library.objects.filter(request=OuterRef("pk"))))
    if record_type == "samples":
        return requests.filter(Exists(Sample.objects.filter(request=OuterRef("pk"))))
    return requests


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


def get_min_count(request):
    """Minimum data points a group needs to be shown (default 3)."""
    try:
        return max(int(request.query_params.get("min_count", 3)), 0)
    except ValueError:
        return 3


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

        min_count = get_min_count(request)
        data = [
            {"name": organization, "data": sum(count.values())}
            for organization, count in counts.items()
            if sum(count.values()) >= min_count
        ]

        return Response(data)


class PrincipalInvestigatorsUsage(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")
        record_type = get_record_type(request)

        libraries_qs = Library.objects.only("id")
        samples_qs = Sample.objects.only("id")

        requests = (
            filter_requests_by_record_type(
                Request.objects.filter(archived=False), record_type
            )
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
            if record_type != "samples":
                counts[pi_name]["libraries"] += len(req.fetched_libraries)
            if record_type != "libraries":
                counts[pi_name]["samples"] += len(req.fetched_samples)

        min_count = get_min_count(request)
        data = [
            {
                "name": pi,
                "data": sum(count.values()),
                "libraries": count["libraries"],
                "samples": count["samples"],
            }
            for pi, count in counts.items()
            if sum(count.values()) >= min_count
        ]

        data = sorted(data, key=lambda x: x["name"])
        return Response(data)


class AnalysisTypesUsage(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")
        record_type = get_record_type(request)

        libraries_qs = Library.objects.select_related("analysis_type").only(
            "id", "analysis_type__name"
        )
        samples_qs = Sample.objects.select_related("analysis_type").only(
            "id", "analysis_type__name"
        )

        requests = (
            filter_requests_by_record_type(
                Request.objects.filter(archived=False), record_type
            )
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
            analysis_types = (
                [x.analysis_type.name for x in req.fetched_libraries if x.analysis_type]
                if record_type != "samples"
                else []
            )
            sample_types = (
                [x.analysis_type.name for x in req.fetched_samples if x.analysis_type]
                if record_type != "libraries"
                else []
            )

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

        min_count = get_min_count(request)
        data = [
            {
                "name": analysis_type,
                "data": sum(count.values()),
                "libraries": count["libraries"],
                "samples": count["samples"],
            }
            for analysis_type, count in counts.items()
            if sum(count.values()) >= min_count
        ]

        data = sorted(data, key=lambda x: x["name"])
        return Response(data)


class TurnaroundTimeUsage(APIView):
    permission_classes = (IsAdminUser,)

    def get(self, request):
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")
        group_by = request.query_params.get("group_by", "sequencer")
        record_type = get_record_type(request)
        include_libraries = record_type in ("all", "libraries")
        include_samples = record_type in ("all", "samples")

        # The first flowcell is the earliest non-archived one; both the
        # turnaround end time and the sequencer come from that same flowcell.
        first_flowcell = Flowcell.objects.filter(
            requests=OuterRef("pk"), archived=False
        ).order_by("create_time", "pk")

        requests = filter_requests_by_record_type(
            Request.objects.annotate(
                first_flowcell_at=Subquery(first_flowcell.values("create_time")[:1]),
                first_flowcell_id=Subquery(first_flowcell.values("flowcell_id")[:1]),
                first_sequencer_name=Subquery(
                    first_flowcell.values("sequencer__name")[:1]
                ),
            ),
            record_type,
        ).filter(
            archived=False,
            submitted_at__isnull=False,
            first_flowcell_at__isnull=False,
            first_flowcell_at__gte=start,
            first_flowcell_at__lte=end,
        )

        if group_by == "analysis_type":
            prefetches = []
            if include_libraries:
                prefetches.append(
                    Prefetch(
                        "libraries",
                        queryset=Library.objects.select_related("analysis_type").only(
                            "id", "analysis_type__name"
                        ),
                        to_attr="fetched_libraries",
                    )
                )
            if include_samples:
                prefetches.append(
                    Prefetch(
                        "samples",
                        queryset=Sample.objects.select_related("analysis_type").only(
                            "id", "analysis_type__name"
                        ),
                        to_attr="fetched_samples",
                    )
                )
            requests = requests.prefetch_related(*prefetches)

        groups = {}
        for req in requests:
            turnaround_days = (
                req.first_flowcell_at - req.submitted_at
            ).total_seconds() / 86400
            if turnaround_days < 0:
                continue

            if group_by == "analysis_type":
                names = set()
                if include_libraries:
                    names |= {
                        x.analysis_type.name
                        for x in req.fetched_libraries
                        if x.analysis_type
                    }
                if include_samples:
                    names |= {
                        x.analysis_type.name
                        for x in req.fetched_samples
                        if x.analysis_type
                    }
            else:
                names = {req.first_sequencer_name or "None"}

            for name in names:
                groups.setdefault(name, []).append(
                    {
                        "value": round(turnaround_days),
                        "request_id": req.pk,
                        "flowcell_id": req.first_flowcell_id,
                    }
                )

        min_count = get_min_count(request)
        data = []
        for name, items in groups.items():
            if len(items) < min_count:
                continue
            items.sort(key=lambda x: x["value"])
            values = [x["value"] for x in items]
            if len(values) >= 2:
                q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
            else:
                q1 = q3 = values[0]

            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr
            inliers = [v for v in values if lower_fence <= v <= upper_fence]
            outliers = [
                item
                for item in items
                if item["value"] < lower_fence or item["value"] > upper_fence
            ]

            data.append(
                {
                    "name": name,
                    "count": len(values),
                    "data": [
                        round(min(inliers) if inliers else values[0]),
                        round(q1),
                        round(statistics.median(values)),
                        round(q3),
                        round(max(inliers) if inliers else values[-1]),
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


class ProtocolComparisonUsage(APIView):
    """Per-protocol concentration and optical-duplicate-rate distributions.

    Query params:
      protocols: comma-separated protocol names (max 2 compared)
      start/end: ISO datetime, as on the Usage page

    Returns one entry per requested protocol with flat lists of observed
    values: concentration_library (ng/µl) per library created in the window,
    and optical duplicate rate (%) averaged over the flowcells each library
    ran on within the window.
    """

    permission_classes = (IsAdminUser,)

    def get(self, request):
        protocol_names = [
            p.strip()
            for p in request.query_params.get("protocols", "").split(",")
            if p.strip()
        ][:2]
        if not protocol_names:
            return Response(
                {"error": "Provide 1-2 protocol names via 'protocols'."},
                status=400,
            )
        start, end = get_date_range(request, "%Y-%m-%dT%H:%M:%S")
        record_type = get_record_type(request)
        min_count = get_min_count(request)

        dup_by_barcode = {}
        for flowcell in (
            Flowcell.objects.filter(
                create_time__gte=start, create_time__lte=end, archived=False
            )
            .exclude(sequences=None)
            .only("flowcell_id", "sequences")
        ):
            for entry in flowcell.sequences or []:
                barcode = entry.get("barcode")
                dup = entry.get("optical_duplicates")
                if barcode and dup is not None:
                    dup_by_barcode.setdefault(barcode, []).append(dup)

        result = []
        if record_type == "samples":
            # CompleteLibraryData has no samples; return empty for requested protocols
            for name in protocol_names:
                result.append(
                    {
                        "protocol": name,
                        "concentration": [],
                        "optical_duplicates": [],
                    }
                )
            return Response(result)
        for name in protocol_names:
            rows = (
                CompleteLibraryData.objects.filter(
                    library_protocol_name=name,
                    create_time__gte=start,
                    create_time__lte=end,
                )
                .exclude(concentration_library=None)
                .values("barcode", "concentration_library")
            )
            concentration = []
            optical = []
            for row in rows:
                concentration.append(row["concentration_library"])
                dups = dup_by_barcode.get(row["barcode"])
                if dups:
                    optical.append(sum(dups) / len(dups))
            if len(concentration) < min_count:
                concentration = []
            if len(optical) < min_count:
                optical = []
            result.append(
                {
                    "protocol": name,
                    "concentration": concentration,
                    "optical_duplicates": optical,
                }
            )
        return Response(result)
