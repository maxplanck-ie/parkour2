from django.db import migrations, models
import simple_history.models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0018_alter_historicalloadflowcellstemplate_file_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RunStatisticsTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="File Name")),
                ("file", models.FileField(upload_to="templates/run_statistics/")),
                (
                    "uploaded_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Uploaded At"
                    ),
                ),
            ],
            options={
                "verbose_name": "Run Statistics Template",
                "verbose_name_plural": "Templates -> Run Statistics",
            },
        ),
        migrations.CreateModel(
            name="SequencesStatisticsTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="File Name")),
                ("file", models.FileField(upload_to="templates/sequences_statistics/")),
                (
                    "uploaded_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Uploaded At"
                    ),
                ),
            ],
            options={
                "verbose_name": "Sequence Statistics Template",
                "verbose_name_plural": "Templates -> Sequence Statistics",
            },
        ),
        migrations.CreateModel(
            name="HistoricalRunStatisticsTemplate",
            fields=[
                (
                    "id",
                    models.BigIntegerField(auto_created=True, blank=True, db_index=True),
                ),
                ("name", models.CharField(max_length=200, verbose_name="File Name")),
                ("file", models.FileField(upload_to="templates/run_statistics/")),
                (
                    "uploaded_at",
                    models.DateTimeField(
                        blank=True, editable=False, verbose_name="Uploaded At"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="+",
                        to="common.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Run Statistics Template",
                "verbose_name_plural": "historical Templates -> Run Statistics",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalSequencesStatisticsTemplate",
            fields=[
                (
                    "id",
                    models.BigIntegerField(auto_created=True, blank=True, db_index=True),
                ),
                ("name", models.CharField(max_length=200, verbose_name="File Name")),
                ("file", models.FileField(upload_to="templates/sequences_statistics/")),
                (
                    "uploaded_at",
                    models.DateTimeField(
                        blank=True, editable=False, verbose_name="Uploaded At"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="+",
                        to="common.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Sequence Statistics Template",
                "verbose_name_plural": "historical Templates -> Sequence Statistics",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
