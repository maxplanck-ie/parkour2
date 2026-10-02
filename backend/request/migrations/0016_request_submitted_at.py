# Generated migration for adding submitted_at field to Request model

from django.db import migrations, models


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
    ]
