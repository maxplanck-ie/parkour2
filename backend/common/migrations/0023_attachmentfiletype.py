import django.core.validators
import simple_history.models
from django.db import migrations, models


DEFAULT_FILE_TYPES = (
    "RNA_FragmentSize_QC",
    "DNA_FragmentSize_QC",
    "Library_FragmentSize_QC",
    "Sample_Barcodes",
    "Experimental_Design",
)


def add_default_file_types(apps, schema_editor):
    AttachmentFileType = apps.get_model("common", "AttachmentFileType")
    AttachmentFileType.objects.bulk_create(
        [AttachmentFileType(name=name) for name in DEFAULT_FILE_TYPES],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0022_historicalprincipalinvestigator_deliver_to_and_more")
    ]

    operations = [
        migrations.CreateModel(
            name="AttachmentFileType",
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
                (
                    "name",
                    models.CharField(
                        help_text="Use letters and numbers separated by single underscores.",
                        max_length=100,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$",
                                "Use letters and numbers separated by single underscores; spaces are not allowed.",
                            )
                        ],
                        verbose_name="Name",
                    ),
                ),
                (
                    "archived",
                    models.BooleanField(default=False, verbose_name="Archived"),
                ),
            ],
            options={
                "verbose_name": "Attachment File Type",
                "verbose_name_plural": "Attachment File Types",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="HistoricalAttachmentFileType",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True,
                        blank=True,
                        db_index=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True,
                        help_text="Use letters and numbers separated by single underscores.",
                        max_length=100,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*$",
                                "Use letters and numbers separated by single underscores; spaces are not allowed.",
                            )
                        ],
                        verbose_name="Name",
                    ),
                ),
                (
                    "archived",
                    models.BooleanField(default=False, verbose_name="Archived"),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[
                            ("+", "Created"),
                            ("~", "Changed"),
                            ("-", "Deleted"),
                        ],
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
                "verbose_name": "historical Attachment File Type",
                "verbose_name_plural": "historical Attachment File Types",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.RunPython(add_default_file_types, migrations.RunPython.noop),
    ]
