import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Creates ReadOnly role and user in DB for django-sql-explorer."

    def handle(self, *args, **options):
        assert settings.DEBUG
        READONLY_USER = os.environ.get("READONLY_USER")
        READONLY_PASSWORD = os.environ.get("READONLY_PASSWORD")
        READONLY_ROLE = "readonly"
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE ROLE {READONLY_ROLE};")
                cursor.execute(
                    f"GRANT CONNECT ON DATABASE postgres TO {READONLY_ROLE};"
                )
                cursor.execute(f"GRANT USAGE ON SCHEMA public TO {READONLY_ROLE};")
                cursor.execute(
                    f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {READONLY_ROLE};"
                )
                cursor.execute(
                    f"CREATE USER {READONLY_USER} WITH PASSWORD '{READONLY_PASSWORD}';"
                )
                cursor.execute(f"GRANT {READONLY_ROLE} TO {READONLY_USER};")

            self.stdout.write(
                self.style.SUCCESS("Successfully created ReadOnly role and user")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
