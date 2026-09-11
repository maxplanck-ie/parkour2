from django.db import migrations

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
        ("common", "0022_attachmentfiletype_invoicingtemplate_and_more"),
    ]

    operations = [
        migrations.RunPython(add_default_file_types, migrations.RunPython.noop),
    ]
