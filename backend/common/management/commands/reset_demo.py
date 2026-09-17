import subprocess

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from common.mviews import refresh_now_blocking

# Baked into the pk2_demo image by the release CI workflow -- see
# .github/workflows/demo-deploy.yml and backend.Dockerfile's pk2_demo
# stage. Must match the COPY destination there exactly.
DUMP_PATH = "/app/fixtures_snapshot.dump"


class Command(BaseCommand):
    help = (
        "Flushes all data and restores it from the release's baked-in "
        "fixture snapshot. For the hourly demo-mode reset only."
    )

    def handle(self, *args, **options):
        if not getattr(settings, "DEMO_MODE", False):
            raise CommandError(
                "reset_demo refuses to run unless DEMO_MODE is enabled "
                "(DJANGO_SETTINGS_MODULE=config.settings.demo) -- this is destructive."
            )
        call_command("flush", interactive=False)
        subprocess.run(
            [
                "pg_restore",
                "--data-only",
                "--single-transaction",
                "--dbname",
                settings.DATABASE_URL,
                DUMP_PATH,
            ],
            check=True,
        )
        # flush()'s post_migrate signal recreates django_content_type/
        # auth_permission, but it skips complete_library_data_mv and
        # complete_sample_data_mv -- both managed=False, so Django's
        # sql_flush never touches them. Rebuild them explicitly; this also
        # TRUNCATEs both tables itself (see common/mviews.py's
        # _execute_full_refresh), so the restored dump's rows for anything
        # those views derive from become visible here, not before.
        refresh_now_blocking(full_refresh=True)
        self.stdout.write(self.style.SUCCESS("Demo database reset."))
