from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Installs the fixture(s) in the database."

    def handle(self, *args, **options):
        for m in ("organization", "principalinvestigator", "costunit", "user"):
            self.loaddata_wrapper(model=m, app_label="common")
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
            self.loaddata_wrapper(model=m, app_label="library_sample_shared")
        for m in ("nucleicacidtype", "sample"):
            self.loaddata_wrapper(model=m, app_label="sample")
        self.loaddata_wrapper(model="library", app_label="library")
        # self.loaddata_wrapper(
        #     model="librarypreparation", app_label="library_preparation"
        # )
        self.loaddata_wrapper(model="pooling", app_label="pooling")
        for m in ("poolsize", "pool"):
            self.loaddata_wrapper(model=m, app_label="index_generator")
        for m in ("filerequest", "request"):
            self.loaddata_wrapper(model=m, app_label="request")
        for m in ("sequencer", "lane", "flowcell"):
            self.loaddata_wrapper(model=m, app_label="flowcell")
        for m in ("fixedcosts", "librarypreparationcosts", "sequencingcosts"):
            self.loaddata_wrapper(model=m, app_label="invoicing")
        self.stdout.write(self.style.SUCCESS("Successfully loaded initial data."))

    def loaddata_wrapper(self, model, app_label):
        print("\t Processing: " + app_label + "/fixtures/" + model + ".json")
        call_command("loaddata", model, app_label=app_label)
