from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Truncates all tables and reloads fixtures. For the hourly demo-mode reset only."

    def handle(self, *args, **options):
        if not getattr(settings, "DEMO_MODE", False):
            raise CommandError(
                "reset_demo refuses to run unless DEMO_MODE is enabled "
                "(DJANGO_SETTINGS_MODULE=config.settings.demo) -- this is destructive."
            )
        call_command("flush", interactive=False)
        call_command("load_initial_data")
        self.stdout.write(self.style.SUCCESS("Demo database reset."))
