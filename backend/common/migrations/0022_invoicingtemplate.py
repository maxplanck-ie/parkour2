from django.db import migrations, models
import simple_history.models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0021_merge_common_0020_migrations"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvoicingTemplate",
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
                ("file", models.FileField(upload_to="templates/invoicing/")),
                (
                    "uploaded_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Uploaded At"),
                ),
            ],
            options={
                "verbose_name": "Invoicing Template",
                "verbose_name_plural": "Templates -> Invoicing",
            },
        ),
        migrations.CreateModel(
            name="HistoricalInvoicingTemplate",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True
                    ),
                ),
                ("name", models.CharField(max_length=200, verbose_name="File Name")),
                ("file", models.FileField(upload_to="templates/invoicing/")),
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
                "verbose_name": "historical Invoicing Template",
                "verbose_name_plural": "historical Templates -> Invoicing",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
