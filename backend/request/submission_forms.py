"""Documents offered in the "Submission forms" checklist of the Add Request dialog.

File naming rule (enforced by tests and by the `add_submission_form`
management command): `YYYYMMDD_Name_with_underscores.ext`, in
backend/static/docs/. The date is the version date; it is shown in the
checklist so users can tell old templates from current ones.

To add or update a form, run (from backend/):

    python manage.py add_submission_form "path/to/My form.xlsx" --date 20261125

It cleans the name, copies the file into backend/static/docs/ and prints the
SUBMISSION_FORMS line to add below. When publishing a new version of an
existing form, point the entry at the new file and delete the old file.
"""

import re
from datetime import datetime
from os.path import basename

DOCS_DIR = "docs"

SUBMISSION_FORMS = {
    "guidelines": (
        "Submission guidelines 2026",
        "docs/20261125_Submission_guidelines_2026.pdf",
    ),
    "s1": ("Formblatt S1 (GMO)", "docs/20261112_Formblatt_S1_GMO.docx"),
    "relacs": (
        "RELACS submission form",
        "docs/20260727_RELACS_submission_form.xlsx",
    ),
    "cut_and_tag": (
        "Cut&Tag submission form",
        "docs/20261125_Cut&Tag_submission_form.xlsx",
    ),
    "gem_x": (
        "GEM-X Universal 3' v4 4-plex OCM submission form",
        "docs/20261125_GEM-X_Universal_3_v4_4-plex_OCM_submission_form.xlsx",
    ),
}

# Forms also offered when the dialog is in "Libraries" mode (not tied to samples).
LIBRARY_FORM_IDS = {"guidelines"}

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


def submission_form_entry(form_id, label, path, today):
    form_date = submission_form_date(path)
    return {
        "id": form_id,
        "label": label,
        "filename": basename(path),
        "date": form_date.isoformat() if form_date else None,
        "is_new": submission_form_is_new(form_date, today),
        "for_libraries": form_id in LIBRARY_FORM_IDS,
    }


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
