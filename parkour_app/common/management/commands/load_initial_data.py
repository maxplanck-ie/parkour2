from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Installs the fixture(s) in the database."

    def handle(self, *args, **options):
        # Load initial data for all apps
        self.load_common_fixtures()
        self.load_library_sample_shared_fixtures()
        self.load_sample_fixtures()
        self.load_index_generator_fixtures()
        self.load_flowcell_fixtures()
        self.load_invoicing_fixtures()

        self.stdout.write(self.style.SUCCESS("Successfully loaded initial data."))

    def loaddata_wrapper(self, model, app_label):
        print("\t Processing: " + app_label + "/fixtures/" + model + ".json")
        call_command("loaddata", model, app_label=app_label)

    def load_common_fixtures(self):
        self.loaddata_wrapper(model="organization", app_label="common")
        self.loaddata_wrapper(model="principalinvestigator", app_label="common")
        self.loaddata_wrapper(model="costunit", app_label="common")

    def load_library_sample_shared_fixtures(self):
        self.loaddata_wrapper(model="organism", app_label="library_sample_shared")

        call_command(
            "loaddata", "concentrationmethod", app_label="library_sample_shared"
        )

        self.loaddata_wrapper(model="readlength", app_label="library_sample_shared")

        self.loaddata_wrapper(model="indexi7", app_label="library_sample_shared")

        self.loaddata_wrapper(model="indexi5", app_label="library_sample_shared")

        self.loaddata_wrapper(model="indextype", app_label="library_sample_shared")

        self.loaddata_wrapper(model="indexpair", app_label="library_sample_shared")

        self.loaddata_wrapper(
            model="libraryprotocol", app_label="library_sample_shared"
        )

        self.loaddata_wrapper(model="librarytype", app_label="library_sample_shared")

    def load_sample_fixtures(self):
        self.loaddata_wrapper(model="nucleicacidtype", app_label="sample")

    def load_index_generator_fixtures(self):
        self.loaddata_wrapper(model="poolsize", app_label="index_generator")

    def load_flowcell_fixtures(self):
        self.loaddata_wrapper(model="sequencer", app_label="flowcell")

    def load_invoicing_fixtures(self):
        self.loaddata_wrapper(model="fixedcosts", app_label="invoicing")
        self.loaddata_wrapper(model="librarypreparationcosts", app_label="invoicing")
        self.loaddata_wrapper(model="sequencingcosts", app_label="invoicing")
