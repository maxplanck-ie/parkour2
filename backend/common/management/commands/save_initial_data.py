import subprocess

from django.core.management.base import BaseCommand


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
            "librarytype",
            "barcodecounter",
        ):
            self.dumpdata_wrapper(model=m, app_label="library_sample_shared")
        for m in ("poolsize", "pool"):
            self.dumpdata_wrapper(model=m, app_label="index_generator")
        for m in ("sequencer", "lane", "flowcell"):
            self.dumpdata_wrapper(model=m, app_label="flowcell")
        for m in ("organization", "principalinvestigator", "costunit", "user"):
            self.dumpdata_wrapper(model=m, app_label="common")
        self.dumpdata_wrapper(model="pooling", app_label="pooling")
        self.stdout.write(self.style.SUCCESS("Successfully saved initial data."))

    def dumpdata_wrapper(self, model, app_label):
        with open(
            app_label + "/fixtures/" + model + ".json", "w", encoding="utf-8"
        ) as f:
            # django.core.management.call_command("dumpdata", app_label + "." + model, stdout=f)
            subprocess.run(
                """
            python manage.py dumpdata {} | tail -1 |
            python -m json.tool""".format(app_label + "." + model),
                stdout=f,
                shell=True,
                check=True,
            )
