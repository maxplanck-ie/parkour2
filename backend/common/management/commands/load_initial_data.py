from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Installs the fixture(s) in the database."

    def handle(self, *args, **options):
        for m in ("group", "organization", "user"):
            self.loaddata_wrapper(model=m, app_label="common")
        self.loaddata_wrapper(model="nucleicacidtype", app_label="sample")
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
            self.loaddata_wrapper(model=m, app_label="library_sample_shared")
        self.loaddata_wrapper(model="sequencer", app_label="flowcell")
        self.loaddata_wrapper(model="poolsize", app_label="index_generator")
        for m in ("librarypreparationcosts",
                  "sequencingcosts",
                  "librarypreparationprice",
                  "sequencingprice"):
            self.loaddata_wrapper(model=m, app_label="invoicing")
        self.stdout.write(self.style.SUCCESS(
            "Successfully loaded initial data."))

    def loaddata_wrapper(self, model, app_label):
        print("\t Processing: " + app_label + "/fixtures/" + model + ".json")
        call_command("loaddata", model, app_label=app_label)
