import request.models
from django.db import migrations, models


def convert_filepaths_to_list(apps, schema_editor):
    Request = apps.get_model("request", "request")
    for req in Request.objects.exclude(filepaths=[]):
        value = req.filepaths
        if isinstance(value, dict):
            if not any(value.values()):
                req.filepaths = []
            else:
                req.filepaths = [value]
            req.save(update_fields=["filepaths"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("request", "0013_historicalrequest_related_requests"),
    ]

    operations = [
        migrations.AlterField(
            model_name="request",
            name="filepaths",
            field=models.JSONField(default=request.models.filepaths_default),
        ),
        migrations.AlterField(
            model_name="historicalrequest",
            name="filepaths",
            field=models.JSONField(default=request.models.filepaths_default),
        ),
        migrations.RunPython(convert_filepaths_to_list, noop_reverse),
    ]
