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

    def load_common_fixtures(self):
        call_command("loaddata", "organization", app_label="common")
        call_command("loaddata", "principalinvestigator", app_label="common")
        call_command("loaddata", "costunit", app_label="common")

    def load_library_sample_shared_fixtures(self):
        call_command("loaddata", "organism", app_label="library_sample_shared")

        call_command(
            "loaddata", "concentrationmethod", app_label="library_sample_shared"
        )

        call_command("loaddata", "readlength", app_label="library_sample_shared")

        call_command("loaddata", "indexi7", app_label="library_sample_shared")

        call_command("loaddata", "indexi5", app_label="library_sample_shared")

        call_command("loaddata", "indextype", app_label="library_sample_shared")

        call_command("loaddata", "indexpair", app_label="library_sample_shared")

        call_command("loaddata", "libraryprotocol", app_label="library_sample_shared")

        call_command("loaddata", "librarytype", app_label="library_sample_shared")

    def load_sample_fixtures(self):
        call_command("loaddata", "nucleicacidtype", app_label="sample")

    def load_index_generator_fixtures(self):
        call_command("loaddata", "poolsize", app_label="index_generator")

    def load_flowcell_fixtures(self):
        call_command("loaddata", "sequencer", app_label="flowcell")

    def load_invoicing_fixtures(self):
        call_command("loaddata", "fixedcosts", app_label="invoicing")
        call_command("loaddata", "librarypreparationcosts", app_label="invoicing")
        call_command("loaddata", "sequencingcosts", app_label="invoicing")
