from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("request", "0009_historicalrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="request",
            name="flowcell_loaded_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Timestamp of the first record reaching Sequencing (status 5)",
                null=True,
                verbose_name="Loaded Onto Flowcell At",
            ),
        ),
        migrations.AddField(
            model_name="request",
            name="qc_completed_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Timestamp of the first record reaching Quality Check Approved (status 2)",
                null=True,
                verbose_name="QC Completed At",
            ),
        ),
        migrations.AddField(
            model_name="historicalrequest",
            name="flowcell_loaded_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Timestamp of the first record reaching Sequencing (status 5)",
                null=True,
                verbose_name="Loaded Onto Flowcell At",
            ),
        ),
        migrations.AddField(
            model_name="historicalrequest",
            name="qc_completed_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Timestamp of the first record reaching Quality Check Approved (status 2)",
                null=True,
                verbose_name="QC Completed At",
            ),
        ),
    ]
