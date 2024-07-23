import csv
import io
import json
import os
from zipfile import ZipFile

# from bioblend.galaxy import GalaxyInstance
from common.views import CsrfExemptSessionAuthentication
from django.apps import apps
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import MetadataSerializer

Request = apps.get_model("request", "Request")
Library = apps.get_model("library", "Library")
Sample = apps.get_model("sample", "Sample")


class MetadataExporterViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Request.objects.all().filter(archived=False).order_by("-create_time")
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)
        data = queryset.values("pk", "name")
        return Response(data)

    def retrieve(self, request, pk=None):
        libraries_qs = (
            Library.objects.select_related(
                "organism",
                "read_length",
                "library_protocol",
                "library_type",
            )
            .only(
                "name",
                "status",
                "barcode",
                "comments",
                "organism__taxon_id",
                "organism__scientific_name",
                "read_length__name",
                "mean_fragment_size",
                "library_protocol__name",
                "library_type__name",
            )
            .filter(status__gte=5)
        )

        samples_qs = (
            Sample.objects.select_related(
                "organism",
                "read_length",
                "library_protocol",
                "library_type",
                "librarypreparation",
            )
            .only(
                "name",
                "status",
                "barcode",
                "comments",
                "organism__taxon_id",
                "organism__scientific_name",
                "read_length__name",
                "library_protocol__name",
                "library_type__name",
                "librarypreparation__mean_fragment_size",
            )
            .filter(status__gte=5)
        )

        queryset = (
            Request.objects.filter(archived=False)
            .prefetch_related(
                Prefetch("libraries", queryset=libraries_qs),
                Prefetch("samples", queryset=samples_qs),
            )
            .only(
                "description",
                "libraries",
                "samples",
            )
        )

        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)

        req = get_object_or_404(queryset, pk=pk)
        serializer = MetadataSerializer(req)
        data = serializer.data.get("result")

        data = sorted(data, key=lambda x: x["barcode"][3:])
        return Response(data)

    @action(methods=["post"], detail=False)
    def get_galaxy_status(self, request):
        url = request.data.get("galaxy_url", "")
        api_key = request.data.get("galaxy_api_key", "")

        try:
            gi = GalaxyInstance(url=url, key=api_key)
            gi.histories.get_most_recently_used_history()
            return Response({"success": True})
        except Exception as e:
            return Response({"success": False, "message": f"ERROR: {e}"})

    @action(
        methods=["post"],
        detail=True,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def download(self, request, pk=None):
        samples = json.loads(request.data.get("samples", "[]"))
        study_type = request.data.get("study_type", "")
        study_title = request.data.get("study_title", "")
        study_abstract = request.data.get("study_abstract", "")

        response = HttpResponse(content_type="application/zip")
        response["Content-Disposition"] = "attachment; filename=ENA.zip"

        experiments_file, samples_file, studies_file, runs_file = self._generate_files(
            samples,
            study_data={
                "title": study_title,
                "study_type": study_type,
                "study_abstract": study_abstract,
                "alias": f'study_{study_title.replace(" ", "_")}',
            },
        )

        # Archive the files
        in_memory = io.BytesIO()
        with ZipFile(in_memory, "a") as z:
            z.writestr("experiments.tsv", experiments_file.getvalue())
            z.writestr("samples.tsv", samples_file.getvalue())
            z.writestr("studies.tsv", studies_file.getvalue())
            z.writestr("runs.tsv", runs_file.getvalue())

        in_memory.seek(0)
        response.write(in_memory.read())

        return response

    @action(
        methods=["post"],
        detail=True,
        authentication_classes=[CsrfExemptSessionAuthentication],
    )
    def upload(self, request, pk=None):
        url = request.data.get("galaxy_url", "")
        api_key = request.data.get("galaxy_api_key", "")
        samples = json.loads(request.data.get("samples", "[]"))
        study_type = request.data.get("study_type", "")
        study_title = request.data.get("study_title", "")
        study_abstract = request.data.get("study_abstract", "")

        experiments_file_path = "experiments.tsv"
        samples_file_path = "samples.tsv"
        studies_file_path = "studies.tsv"
        runs_file_path = "runs.tsv"
        new_history_name = "ENA"

        try:
            gi = GalaxyInstance(url=url, key=api_key)
            gi.histories.get_most_recently_used_history()
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Couldn't connect to Galaxy: {e}",
                }
            )

        experiments_file, samples_file, studies_file, runs_file = self._generate_files(
            samples,
            study_data={
                "title": study_title,
                "study_type": study_type,
                "study_abstract": study_abstract,
                "alias": f'study_{study_title.replace(" ", "_")}',
            },
        )

        files = {
            experiments_file_path: experiments_file,
            samples_file_path: samples_file,
            studies_file_path: studies_file,
            runs_file_path: runs_file,
        }

        # Save files locally
        for file_path, file in files.items():
            with open(file_path, "w") as f:
                f.write(file.getvalue())

        new_history = gi.histories.create_history(new_history_name)
        try:
            for file_path in files.keys():
                gi.tools.upload_file(os.path.abspath(file_path), new_history["id"])
        except Exception as e:
            return Response({"success": False, "message": str(e)})
        finally:
            for file_path in files.keys():
                if os.path.isfile(file_path):
                    os.remove(file_path)
        return Response({"success": True})

    @staticmethod
    def _generate_files(data, **kwargs):
        def getrow(header, item, type, index):
            row = []
            name = item.get("library_name")
            for h in header:
                if h == "alias" and type != "study":
                    value = f"{type}_{name}"
                elif h == "experiment_alias":
                    value = f"experiment_{name}"
                elif h == "sample_alias":
                    value = f"sample_{name}"
                elif h == "run_alias":
                    value = f"run_{name}"
                else:
                    value = item.get(h, "None")
                row.append(value)
            return row

        def getfile(type, header, data, **kwargs):
            study_data = kwargs.get("study_data", {})
            file = io.StringIO()
            writer = csv.writer(file, dialect="excel-tab")
            writer.writerow(header)

            if type == "study":
                item = {**dict(data[0]), **study_data}
                writer.writerow(getrow(header, item, type, 1))
            else:
                for i, item in enumerate(data):
                    item_ = {
                        **dict(item),
                        **{"study_alias": study_data.get("alias", "")},
                    }
                    writer.writerow(getrow(header, item_, type, i))

            return file

        # Create experiments.tsv
        header = [
            "alias",
            "status",
            "accession",
            "title",
            "study_alias",
            "sample_alias",
            "design_description",
            "library_name",
            "library_strategy",
            "library_source",
            "library_selection",
            "library_layout",
            "insert_size",
            "library_construction_protocol",
            "platform",
            "instrument_model",
            "submission_date",
        ]
        experiments_file = getfile(
            "experiment", header, data, study_data=kwargs.get("study_data")
        )

        # Create samples.tsv
        header = [
            "alias",
            "status",
            "accession",
            "title",
            "scientific_name",
            "taxon_id",
            "sample_description",
            "submission_date",
        ]
        samples_file = getfile("sample", header, data)

        # Create studies.tsv
        header = [
            "alias",
            "status",
            "accession",
            "title",
            "study_type",
            "study_abstract",
            "pubmed_id",
            "submission_date",
        ]
        studies_file = getfile(
            "study", header, data, study_data=kwargs.get("study_data")
        )

        # Create runs.tsv
        header = [
            "alias",
            "status",
            "accession",
            "experiment_alias",
            "file_name",
            "file_format",
            "file_checksum",
            "submission_date",
        ]
        runs_file = getfile("run", header, data)

        return experiments_file, samples_file, studies_file, runs_file
