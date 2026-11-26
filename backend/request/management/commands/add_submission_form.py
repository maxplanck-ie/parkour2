import shutil
from datetime import date, datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from request.submission_forms import (
    DOCS_DIR,
    SUBMISSION_FORMS,
    normalize_submission_form_name,
)


class Command(BaseCommand):
    help = (
        "Copy a submission form into backend/static/docs/ under the required "
        "name (YYYYMMDD_Name_with_underscores.ext) and print the "
        "SUBMISSION_FORMS line to add."
    )

    def add_arguments(self, parser):
        parser.add_argument("path", help="File to add")
        parser.add_argument(
            "--date",
            help="Version date, YYYYMMDD (default: today)",
        )
        parser.add_argument(
            "--id",
            dest="form_id",
            help="Existing form id when publishing a new version of it",
        )

    def handle(self, *args, **options):
        source = Path(options["path"])
        if not source.is_file():
            raise CommandError(f"Not a file: {source}")

        if options["date"]:
            try:
                version = datetime.strptime(options["date"], "%Y%m%d").date()
            except ValueError:
                raise CommandError("--date must be YYYYMMDD, e.g. 20261125")
        else:
            version = date.today()

        new_name = normalize_submission_form_name(source.name, version)
        target_dir = Path(settings.BASE_DIR) / "static" / DOCS_DIR
        target = target_dir / new_name
        if target.exists():
            raise CommandError(f"{target} already exists")

        form_id = options["form_id"]
        old_path = None
        if form_id:
            if form_id not in SUBMISSION_FORMS:
                raise CommandError(
                    f"Unknown id {form_id!r}. Known: {', '.join(SUBMISSION_FORMS)}"
                )
            old_path = SUBMISSION_FORMS[form_id][1]

        shutil.copyfile(source, target)
        self.stdout.write(self.style.SUCCESS(f"Copied to {target}"))
        entry = f'"{DOCS_DIR}/{new_name}"'
        if form_id:
            self.stdout.write(
                f"In request/submission_forms.py set the path of {form_id!r} to "
                f"{entry} and delete the old file: git rm backend/static/{old_path}"
            )
        else:
            self.stdout.write(
                "Add to SUBMISSION_FORMS in request/submission_forms.py:\n"
                f'    "<id>": ("<label shown to users>", {entry}),'
            )
