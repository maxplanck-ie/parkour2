import shutil
from datetime import date, datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from request import submission_forms as sf


class Command(BaseCommand):
    help = (
        "Publish a file in the 'Submission forms' checklist. "
        "--replace <id> swaps the file of an existing form (new version, "
        "old file deleted, id and label kept); --new <id> --label '...' adds "
        "a form. The file is renamed to YYYYMMDD_Name_with_underscores.ext."
    )

    def add_arguments(self, parser):
        parser.add_argument("path", help="File to publish")
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument(
            "--replace",
            metavar="ID",
            help="Id of the existing form this file is a new version of",
        )
        mode.add_argument(
            "--new",
            metavar="ID",
            help="Id for a brand new form (lowercase letters, digits, underscores)",
        )
        parser.add_argument(
            "--label",
            help="Label shown to users (required with --new; optional with --replace)",
        )
        parser.add_argument(
            "--for-libraries",
            action="store_true",
            help="With --new: also offer it in Libraries mode",
        )
        parser.add_argument("--date", help="Version date, YYYYMMDD (default: today)")

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

        forms = sf.load_submission_forms()
        new_name = sf.normalize_submission_form_name(source.name, version)
        target = sf.docs_path() / new_name
        if target.exists():
            raise CommandError(f"{target} already exists")

        if options["replace"]:
            form_id = options["replace"]
            if form_id not in forms:
                known = ", ".join(f"{i} ({f['label']})" for i, f in forms.items())
                raise CommandError(f"Unknown id {form_id!r}. Known: {known}")
            form = forms[form_id]
            old_file = sf.docs_path() / form["file"]
            if options["label"]:
                form["label"] = options["label"]
            form["file"] = new_name
        else:
            form_id = options["new"]
            if not form_id.replace("_", "").isalnum() or form_id != form_id.lower():
                raise CommandError(
                    "--new id must be lowercase letters, digits and underscores"
                )
            if not options["label"]:
                raise CommandError("--new needs --label")
            if form_id in forms:
                raise CommandError(
                    f"Id {form_id!r} exists; use --replace {form_id} for a new version"
                )
            twin = next(
                (
                    i
                    for i, f in forms.items()
                    if sf.name_without_date(f["file"]) == sf.name_without_date(new_name)
                ),
                None,
            )
            if twin:
                raise CommandError(
                    f"{new_name} looks like another version of {twin!r}; "
                    f"use --replace {twin} instead"
                )
            old_file = None
            forms[form_id] = {
                "label": options["label"],
                "file": new_name,
                "for_libraries": options["for_libraries"],
            }

        shutil.copyfile(source, target)
        sf.save_submission_forms(forms)
        if old_file is not None and old_file.exists():
            old_file.unlink()
        self.stdout.write(
            self.style.SUCCESS(
                f"{form_id}: {forms[form_id]['label']} -> {new_name}"
                + (f" (removed {old_file.name})" if old_file else "")
            )
        )
