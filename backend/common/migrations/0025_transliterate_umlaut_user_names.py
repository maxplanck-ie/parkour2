from django.db import migrations

# Standard German ASCII transliteration (the "digraph" convention: ä -> ae,
# not the single-letter form Illumina/dissectBCL use for folder names). Once a
# name has no diacritics left, dissectBCL's `umlautDestroyer` and Parkour's
# `transliterate_name` (common.utils) both become no-ops on it, so it can no
# longer mismatch a filesystem-derived token regardless of which convention
# was used to get there.
UMLAUT_MAP = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",  # codespell:ignore ue
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",  # codespell:ignore ue
    "ß": "ss",
}


def transliterate(value):
    for src, dst in UMLAUT_MAP.items():
        value = value.replace(src, dst)
    return value


def rename_umlaut_names(apps, schema_editor):
    User = apps.get_model("common", "User")
    for user in User.objects.all():
        new_first = transliterate(user.first_name)
        new_last = transliterate(user.last_name)
        if new_first != user.first_name or new_last != user.last_name:
            user.first_name = new_first
            user.last_name = new_last
            user.save(update_fields=["first_name", "last_name"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0024_merge_20260806_0000"),
    ]

    operations = [
        migrations.RunPython(rename_umlaut_names, noop_reverse),
    ]
