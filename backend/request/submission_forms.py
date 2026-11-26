"""Documents offered in the "Submission forms" checklist of the Add Request dialog.

The registry is backend/static/docs/forms.json: {id: {label, file,
for_libraries}}. Do not edit it or the files next to it by hand; use

    python manage.py publish_submission_form "<path>" --replace <id> [--date YYYYMMDD]
    python manage.py publish_submission_form "<path>" --new <id> --label "..." [--date YYYYMMDD]

File naming rule (enforced by the command and by tests):
`YYYYMMDD_Name_with_underscores.ext`. The date is the version date, shown in the
checklist so users can tell old templates from current ones.
"""

import json
import re
from datetime import datetime
from os.path import basename
from pathlib import Path

from django.conf import settings

DOCS_DIR = "docs"
REGISTRY_NAME = "forms.json"


def docs_path():
    return Path(settings.BASE_DIR) / "static" / DOCS_DIR


def load_submission_forms():
    """Registry as {id: {"label", "file", "for_libraries"}} (ordered as in the file)."""
    with open(docs_path() / REGISTRY_NAME, encoding="utf-8") as fh:
        return json.load(fh)


def save_submission_forms(forms):
    with open(docs_path() / REGISTRY_NAME, "w", encoding="utf-8") as fh:
        json.dump(forms, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def submission_form_static_path(form):
    """Path relative to the static root, as `find_static` expects."""
    return f"{DOCS_DIR}/{form['file']}"


# A form whose version date is at most this many days old gets a "New!" badge.
SUBMISSION_FORM_NEW_DAYS = 15

_DATE_PREFIX = re.compile(r"(\d{8})_")


def submission_form_date(path):
    """Version date from the YYYYMMDD_ prefix of the file name, or None."""
    match = _DATE_PREFIX.match(basename(path))
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d").date()
    except ValueError:
        return None


def submission_form_is_new(form_date, today):
    return (
        form_date is not None
        and 0 <= (today - form_date).days <= SUBMISSION_FORM_NEW_DAYS
    )


def submission_form_entry(form_id, form, today):
    form_date = submission_form_date(form["file"])
    return {
        "id": form_id,
        "label": form["label"],
        "filename": form["file"],
        "date": form_date.isoformat() if form_date else None,
        "is_new": submission_form_is_new(form_date, today),
        "for_libraries": form["for_libraries"],
    }


def name_without_date(filename):
    """`20261125_Foo_bar.pdf` -> `foo_bar.pdf`, for duplicate detection."""
    return _DATE_PREFIX.sub("", basename(filename), count=1).lower()


def normalize_submission_form_name(filename, date):
    """`My form (v2).xlsx` + date -> `20261125_My_form_v2.xlsx`.

    Any existing YYYYMMDD_ prefix is dropped and replaced by `date`
    (a `datetime.date`). Spaces become underscores; characters other than
    letters, digits, `.`, `_`, `-` and `&` are removed.
    """
    stem, dot, ext = basename(filename).rpartition(".")
    if not dot:
        stem, ext = ext, ""
    stem = _DATE_PREFIX.sub("", stem, count=1)
    stem = re.sub(r"\s+", "_", stem.strip())
    stem = re.sub(r"[^\w.&-]", "", stem, flags=re.ASCII)
    stem = re.sub(r"_+", "_", stem).strip("_")
    if not stem:
        raise ValueError(f"Nothing usable left of file name {filename!r}")
    name = f"{date:%Y%m%d}_{stem}"
    return f"{name}.{ext.lower()}" if ext else name
