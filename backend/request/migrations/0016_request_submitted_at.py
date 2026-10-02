# Adds submitted_at field to Request model, plus a backfill of that field
# for pre-existing requests from the legacy approval['TIMESTAMP'] value (the
# closest proxy available in historical data, since library/sample
# status-transition history was never retained).

from django.db import migrations, models
from django.utils.dateparse import parse_datetime


def backfill_submitted_at(apps, schema_editor):
    Request = apps.get_model("request", "Request")
    for req in Request.objects.filter(
        submitted_at__isnull=True, approval__TIMESTAMP__isnull=False
    ).iterator():
        timestamp = parse_datetime(req.approval["TIMESTAMP"])
        if timestamp is None:
            continue
        req.submitted_at = timestamp
        req.save(update_fields=["submitted_at"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("request", "0015_filerequest_file_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="submitted_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Timestamp of the first record reaching Submitted (status 1)",
                null=True,
                verbose_name="Submitted At",
            ),
        ),
        migrations.AddField(
            model_name="historicalrequest",
            name="submitted_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Timestamp of the first record reaching Submitted (status 1)",
                null=True,
                verbose_name="Submitted At",
            ),
        ),
        migrations.RunPython(backfill_submitted_at, noop_reverse),
    ]
