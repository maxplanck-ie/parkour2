import subprocess

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Saves relevant database content into fixture(s) correspondingly."

    def handle(self, *args, **options):
        # Save demo data for all apps
        self.save_library_sample_shared_fixtures()
        self.save_sample_fixtures()
        self.save_index_generator_fixtures()
        self.save_flowcell_fixtures()

        self.stdout.write(self.style.SUCCESS("Successfully saved demo data."))

    def dumpdata_wrapper(self, model, app_label):
        with open(
            app_label + "/fixtures/" + model + ".json", "w", encoding="utf-8"
        ) as f:
            # django.core.management.call_command("dumpdata", app_label + "." + model, stdout=f)
            subprocess.run(
                """
            python manage.py dumpdata {} | tail -1 |
            jq .""".format(
                    app_label + "." + model
                ),
                stdout=f,
                shell=True,
                check=True,
            )

    def save_library_sample_shared_fixtures(self):
        self.dumpdata_wrapper(model="organism", app_label="library_sample_shared")
        self.dumpdata_wrapper(
            model="concentrationmethod", app_label="library_sample_shared"
        )
        self.dumpdata_wrapper(model="readlength", app_label="library_sample_shared")
        self.dumpdata_wrapper(model="indexi7", app_label="library_sample_shared")
        self.dumpdata_wrapper(model="indexi5", app_label="library_sample_shared")
        self.dumpdata_wrapper(model="indextype", app_label="library_sample_shared")
        self.dumpdata_wrapper(model="indexpair", app_label="library_sample_shared")
        self.dumpdata_wrapper(
            model="libraryprotocol", app_label="library_sample_shared"
        )
        self.dumpdata_wrapper(model="librarytype", app_label="library_sample_shared")

    def save_sample_fixtures(self):
        self.dumpdata_wrapper(model="nucleicacidtype", app_label="sample")

    def save_index_generator_fixtures(self):
        self.dumpdata_wrapper(model="poolsize", app_label="index_generator")

    def save_flowcell_fixtures(self):
        self.dumpdata_wrapper(model="sequencer", app_label="flowcell")
