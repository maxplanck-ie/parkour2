import os
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
        # Check the snapshot exists BEFORE flushing: flush() runs in its own
        # transaction and commits, so a missing dump discovered afterwards
        # would leave the demo database permanently empty.
        if not os.path.exists(DUMP_PATH):
            raise CommandError(
                f"Fixture snapshot missing at {DUMP_PATH}; refusing to flush."
            )
        call_command("flush", interactive=False)
        # The connection is reassembled from DATABASES["default"] instead of
        # passing settings.DATABASE_URL to --dbname: that URL embeds the
        # password, which would be visible in /proc/<pid>/cmdline and, worse,
        # echoed back inside subprocess.CalledProcessError's message on
        # failure -- straight into the Fly Machine logs. The password goes via
        # PGPASSWORD in the subprocess environment instead.
        db = settings.DATABASES["default"]
        subprocess.run(
            [
                "pg_restore",
                "--data-only",
                "--single-transaction",
                "--host",
                db["HOST"],
                "--port",
                str(db["PORT"]),
                "--username",
                db["USER"],
                "--dbname",
                db["NAME"],
                DUMP_PATH,
            ],
            check=True,
            env={**os.environ, "PGPASSWORD": db["PASSWORD"]},
        )
        # The dump the restore above reads is `pg_dump --data-only` with six
        # tables excluded (see .github/workflows/demo-deploy.yml):
        #   django_content_type, auth_permission -- flush()'s post_migrate
        #     signal recreates these itself, so restoring them would double
        #     them and collide on their unique keys;
        #   django_migrations -- flush() never truncates it, and the live
        #     demo DB's migration history is authoritative;
        #   django_session -- stale sessions have no business being replayed;
        #   complete_library_data_mv, complete_sample_data_mv -- derived,
        #     denormalized data, and both are managed=False so Django's
        #     sql_flush skips them; their rows survive flush(), so restoring
        #     a second copy would collide on idx_cld_mv_pk/idx_csd_mv_pk
        #     (backend/common/sql.py) and roll back the whole
        #     --single-transaction restore. They are rebuilt from scratch by
        #     the refresh below instead.
        # refresh_now_blocking TRUNCATEs and rebuilds both mv tables itself
        # (see common/mviews.py's _execute_full_refresh), so the restored
        # rows they derive from become visible here, not before.
        refresh_now_blocking(full_refresh=True)
        self.stdout.write(self.style.SUCCESS("Demo database reset."))
