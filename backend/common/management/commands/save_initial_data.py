import subprocess

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Saves relevant database content into fixture(s) correspondingly."

    def handle(self, *args, **options):
        for m in ("librarypreparationcosts",
                  "sequencingcosts",
                  "librarypreparationprice",
                  "sequencingprice"):
            self.dumpdata_wrapper(model=m, app_label="invoicing")
        self.dumpdata_wrapper(model="poolsize", app_label="index_generator")
        self.dumpdata_wrapper(model="sequencer", app_label="flowcell")
        for m in (
            "organism",
            "concentrationmethod",
            "indexi7",
            "indexi5",
            "indextype",
            "indexpair",
            "libraryprotocol",
            "librarytype",
            "readlength",
        ):
            self.dumpdata_wrapper(model=m, app_label="library_sample_shared")
        self.dumpdata_wrapper(model="nucleicacidtype", app_label="sample")
        self.dumpdata_wrapper(model="group", app_label="auth")
        for m in ("organization", "user"):
            self.dumpdata_wrapper(model=m, app_label="common")
        self.stdout.write(self.style.SUCCESS("Successfully saved initial data."))

    def dumpdata_wrapper(self, model, app_label):
        app_label_path = app_label
        if app_label == "auth":
            app_label_path = 'common'
        with open(
            app_label_path + "/fixtures/" + model + ".json", "w", encoding="utf-8"
        ) as f:
            # django.core.management.call_command("dumpdata", app_label + "." + model, stdout=f)
            print("Saving: " + app_label + "/fixtures/" + model + ".json")
            subprocess.run(
                """
            python manage.py dumpdata {} --natural-foreign | tail -1 |
            jq .""".format(
                    app_label + "." + model
                ),
                stdout=f,
                shell=True,
                check=True,
            )
