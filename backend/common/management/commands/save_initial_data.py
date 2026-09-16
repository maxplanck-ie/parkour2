import os
import re

from django.core.management import call_command
from django.core.management.base import BaseCommand

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")


class Command(BaseCommand):
    help = "Saves relevant database content into fixture(s) correspondingly."

    def handle(self, *args, **options):
        self.dumpdata_wrapper(
            model="librarypreparation", app_label="library_preparation"
        )
        for m in ("filerequest", "request"):
            self.dumpdata_wrapper(model=m, app_label="request")
        for m in ("nucleicacidtype", "sample"):
            self.dumpdata_wrapper(model=m, app_label="sample")
        self.dumpdata_wrapper(model="library", app_label="library")
        for m in (
            "organism",
            "concentrationmethod",
            "readlength",
            "indexi7",
            "indexi5",
            "indextype",
            "indexpair",
            "libraryprotocol",
            "analysistype",
            "barcodecounter",
        ):
            self.dumpdata_wrapper(model=m, app_label="library_sample_shared")
        for m in ("poolsize", "pool"):
            self.dumpdata_wrapper(model=m, app_label="index_generator")
        for m in ("sequencer", "lane", "flowcell"):
            self.dumpdata_wrapper(model=m, app_label="flowcell")
        for m in ("organization", "principalinvestigator", "costunit", "user", "duty"):
            self.dumpdata_wrapper(model=m, app_label="common")
        self.dumpdata_wrapper(model="pooling", app_label="pooling")
        self.stdout.write(self.style.SUCCESS("Successfully saved initial data."))

    def dumpdata_wrapper(self, model, app_label):
        for name in (model, app_label):
            if not SAFE_IDENTIFIER_RE.match(name):
                raise ValueError(f"Invalid model/app_label identifier: {name}")
        fixture_path = os.path.join(
            os.path.basename(app_label), "fixtures", os.path.basename(model) + ".json"
        )
        with open(fixture_path, "w", encoding="utf-8") as f:
            call_command("dumpdata", app_label + "." + model, indent=4, stdout=f)
